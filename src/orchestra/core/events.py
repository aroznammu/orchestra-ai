"""Hybrid EventBus abstraction: Redis Streams (real-time) + Kafka (durable/audit).

Events are routed by type:
- Ephemeral/real-time events -> Redis Streams
- Durable/audit/moat events -> Kafka
"""

import json
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger("events")


class EventChannel(str, Enum):
    REALTIME = "realtime"
    DURABLE = "durable"


class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str
    channel: EventChannel = EventChannel.REALTIME
    tenant_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


DURABLE_EVENT_TYPES = {
    "campaign.created",
    "campaign.completed",
    "spend.recorded",
    "spend.anomaly_detected",
    "bid.changed",
    "budget.changed",
    "compliance.violation",
    "platform.connected",
    "platform.disconnected",
    "kill_switch.activated",
    "audit.action",
}


class EventBusBackend(ABC):
    @abstractmethod
    async def publish(self, stream: str, event: Event) -> None: ...

    @abstractmethod
    async def subscribe(self, stream: str, group: str, consumer: str) -> list[Event]: ...

    @abstractmethod
    async def close(self) -> None: ...


class RedisStreamBackend(EventBusBackend):
    """Redis Streams backend for real-time ephemeral events."""

    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url
        self._redis = None

    async def _get_redis(self):  # noqa: ANN202
        if self._redis is None:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def publish(self, stream: str, event: Event) -> None:
        r = await self._get_redis()
        await r.xadd(stream, {"data": event.model_dump_json()}, maxlen=10000)
        logger.debug("event_published", stream=stream, event_type=event.type, backend="redis")

    async def subscribe(self, stream: str, group: str, consumer: str) -> list[Event]:
        r = await self._get_redis()
        try:
            await r.xgroup_create(stream, group, id="0", mkstream=True)
        except Exception:
            pass
        messages = await r.xreadgroup(group, consumer, {stream: ">"}, count=10, block=1000)
        events = []
        for _stream_name, entries in messages:
            for _msg_id, data in entries:
                events.append(Event.model_validate_json(data["data"]))
        return events

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()


class KafkaBackend(EventBusBackend):
    """Kafka backend for durable audit/moat events."""

    def __init__(self, bootstrap_servers: str) -> None:
        self.bootstrap_servers = bootstrap_servers
        self._producer = None

    async def _get_producer(self):  # noqa: ANN202
        if self._producer is None:
            from aiokafka import AIOKafkaProducer
            self._producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)
            await self._producer.start()
        return self._producer

    async def publish(self, stream: str, event: Event) -> None:
        producer = await self._get_producer()
        value = event.model_dump_json().encode("utf-8")
        key = (event.tenant_id or event.id).encode("utf-8")
        await producer.send_and_wait(stream, value=value, key=key)
        logger.debug("event_published", stream=stream, event_type=event.type, backend="kafka")

    async def subscribe(self, stream: str, group: str, consumer: str) -> list[Event]:
        from aiokafka import AIOKafkaConsumer
        c = AIOKafkaConsumer(stream, bootstrap_servers=self.bootstrap_servers, group_id=group)
        await c.start()
        try:
            data = await c.getmany(timeout_ms=1000)
            events = []
            for _tp, messages in data.items():
                for msg in messages:
                    events.append(Event.model_validate_json(msg.value.decode("utf-8")))
            return events
        finally:
            await c.stop()

    async def close(self) -> None:
        if self._producer:
            await self._producer.stop()


class HybridEventBus:
    """Routes events to Redis Streams or Kafka based on event type."""

    def __init__(self, redis_url: str, kafka_servers: str) -> None:
        self.redis = RedisStreamBackend(redis_url)
        self.kafka = KafkaBackend(kafka_servers)

    async def publish(self, event: Event) -> None:
        if event.type in DURABLE_EVENT_TYPES:
            event.channel = EventChannel.DURABLE
            await self.kafka.publish(f"orchestra.{event.type}", event)
        else:
            event.channel = EventChannel.REALTIME
            await self.redis.publish(f"orchestra:{event.type}", event)

    async def close(self) -> None:
        await self.redis.close()
        await self.kafka.close()
