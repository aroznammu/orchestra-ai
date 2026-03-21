"""API routes for AI customer support chat."""

import uuid
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from orchestra.agents.support_agent import get_support_reply, sanitize_response
from orchestra.api.deps import CurrentUser, DbSession
from orchestra.db.models import (
    ChatMessage,
    ChatMessageRole,
    ChatSession,
    ChatSessionStatus,
    FAQEntry,
    Tenant,
)

logger = structlog.get_logger("api.support")

router = APIRouter(prefix="/support", tags=["support"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class CreateSessionRequest(BaseModel):
    title: str | None = None


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="UUID of the chat session")
    message: str = Field(..., min_length=1, max_length=4000, description="User message")


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class SessionOut(BaseModel):
    id: str
    title: str
    status: str
    created_at: str
    updated_at: str
    message_count: int = 0


class ChatResponse(BaseModel):
    session_id: str
    user_message: MessageOut
    assistant_message: MessageOut
    sources: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _session_to_out(session: ChatSession, message_count: int = 0) -> SessionOut:
    return SessionOut(
        id=str(session.id),
        title=session.title,
        status=session.status.value,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
        message_count=message_count,
    )


def _message_to_out(msg: ChatMessage) -> MessageOut:
    return MessageOut(
        id=str(msg.id),
        role=msg.role.value,
        content=sanitize_response(msg.content),
        metadata=msg.metadata_,
        created_at=msg.created_at.isoformat(),
    )


async def _get_tenant_session(
    db: DbSession, session_id: str, tenant_id: str
) -> ChatSession:
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == uuid.UUID(session_id),
            ChatSession.tenant_id == uuid.UUID(tenant_id),
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(user: CurrentUser, db: DbSession) -> list[SessionOut]:
    """List all chat sessions for the current tenant."""
    tid = uuid.UUID(user.tenant_id)
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.tenant_id == tid)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()

    out: list[SessionOut] = []
    for s in sessions:
        msg_count_result = await db.execute(
            select(ChatMessage.id).where(ChatMessage.session_id == s.id)
        )
        count = len(msg_count_result.scalars().all())
        out.append(_session_to_out(s, message_count=count))
    return out


@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: CreateSessionRequest,
    user: CurrentUser,
    db: DbSession,
) -> SessionOut:
    """Create a new support chat session."""
    session = ChatSession(
        tenant_id=uuid.UUID(user.tenant_id),
        user_id=uuid.UUID(user.sub),
        title=request.title or "New conversation",
        status=ChatSessionStatus.OPEN,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)

    logger.info("support_session_created", session_id=str(session.id), tenant_id=user.tenant_id)
    return _session_to_out(session)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: CurrentUser,
    db: DbSession,
) -> ChatResponse:
    """Send a message and receive an AI-generated reply."""
    session = await _get_tenant_session(db, request.session_id, user.tenant_id)

    if session.status == ChatSessionStatus.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send messages to a closed session.",
        )

    user_msg = ChatMessage(
        session_id=session.id,
        role=ChatMessageRole.USER,
        content=request.message,
        metadata_={},
    )
    db.add(user_msg)
    await db.flush()
    await db.refresh(user_msg)

    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
    )
    history_msgs = history_result.scalars().all()
    chat_history = [
        {"role": m.role.value, "content": m.content}
        for m in history_msgs
        if m.role in (ChatMessageRole.USER, ChatMessageRole.ASSISTANT)
    ]

    faq_result = await db.execute(
        select(FAQEntry).where(
            FAQEntry.is_published.is_(True),
            (FAQEntry.tenant_id == uuid.UUID(user.tenant_id)) | (FAQEntry.tenant_id.is_(None)),
        )
    )
    all_faqs = faq_result.scalars().all()
    query_lower = request.message.lower()
    matched_faqs = [
        {"question": f.question, "answer": f.answer}
        for f in all_faqs
        if any(word in f.question.lower() for word in query_lower.split() if len(word) > 3)
    ][:5]

    tenant_plan: str | None = None
    tenant_result = await db.execute(
        select(Tenant.subscription_plan).where(Tenant.id == uuid.UUID(user.tenant_id))
    )
    tenant_plan = tenant_result.scalar_one_or_none()

    support_response = await get_support_reply(
        user_message=request.message,
        tenant_id=user.tenant_id,
        chat_history=chat_history,
        faq_entries=matched_faqs,
        tenant_plan=tenant_plan,
    )

    assistant_msg = ChatMessage(
        session_id=session.id,
        role=ChatMessageRole.ASSISTANT,
        content=support_response.reply,
        metadata_={
            "sources": support_response.sources,
            "faq_matches": len(support_response.faq_matches),
        },
    )
    db.add(assistant_msg)
    await db.flush()
    await db.refresh(assistant_msg)

    if session.title == "New conversation" and len(history_msgs) <= 1:
        session.title = request.message[:80].strip()

    logger.info(
        "support_chat_reply",
        session_id=request.session_id,
        tenant_id=user.tenant_id,
    )

    return ChatResponse(
        session_id=str(session.id),
        user_message=_message_to_out(user_msg),
        assistant_message=_message_to_out(assistant_msg),
        sources=support_response.sources,
    )


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
async def get_session_messages(
    session_id: str,
    user: CurrentUser,
    db: DbSession,
) -> list[MessageOut]:
    """Retrieve all messages for a specific chat session."""
    await _get_tenant_session(db, session_id, user.tenant_id)

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == uuid.UUID(session_id))
        .order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()
    return [_message_to_out(m) for m in messages]


@router.post("/sessions/{session_id}/resolve", response_model=SessionOut)
async def resolve_session(
    session_id: str,
    user: CurrentUser,
    db: DbSession,
) -> SessionOut:
    """Mark a support session as resolved."""
    session = await _get_tenant_session(db, session_id, user.tenant_id)
    session.status = ChatSessionStatus.RESOLVED

    logger.info("support_session_resolved", session_id=session_id, tenant_id=user.tenant_id)
    return _session_to_out(session)
