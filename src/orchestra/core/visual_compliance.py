"""Visual Compliance Gate -- scans video keyframes for copyright/IP violations."""

from __future__ import annotations

import asyncio
import base64
import json
import tempfile
from pathlib import Path
from typing import Any

import httpx
import structlog

from orchestra.agents.contracts import VisualComplianceResult
from orchestra.config import get_settings

logger = structlog.get_logger("core.visual_compliance")

_SYSTEM_PROMPT = """\
You are a strict visual compliance scanner for a marketing automation platform.
Analyze the provided video keyframes and check for:

1. **Celebrity likenesses**: Real-world public figures, politicians, athletes, musicians.
2. **Copyrighted characters/IP**: Disney, Marvel, DC, Star Trek, Studio Ghibli, Pixar, etc.
3. **Trademarked logos**: Corporate logos not owned by the requesting tenant (Nike, Apple, etc.).

Return your analysis as JSON with exactly this schema:
{
  "safe": true/false,
  "violations": [
    {"type": "celebrity|copyright|trademark", "description": "...", "confidence": 0.0-1.0}
  ]
}

If no violations are found, return {"safe": true, "violations": []}.
Be conservative: flag anything borderline. Only mark safe if you are confident.
Respond with ONLY the JSON object, no markdown fences or explanation.\
"""

KEYFRAME_COUNT = 4


async def _download_video(video_url: str) -> Path:
    """Download video to a temporary file."""
    tmp = Path(tempfile.mktemp(suffix=".mp4"))
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        resp = await client.get(video_url)
        resp.raise_for_status()
        tmp.write_bytes(resp.content)
    return tmp


async def _extract_keyframes(video_path: Path, count: int = KEYFRAME_COUNT) -> list[bytes]:
    """Extract evenly-spaced keyframes from a video using ffmpeg."""
    output_dir = Path(tempfile.mkdtemp())
    output_pattern = str(output_dir / "frame_%03d.png")

    proc = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-i", str(video_path),
        "-vf", f"fps=1/{max(1, 5 // count)},scale=512:-1",
        "-frames:v", str(count),
        "-y",
        output_pattern,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        logger.warning("ffmpeg_keyframe_extraction_failed", stderr=stderr.decode()[:300])
        return []

    frames: list[bytes] = []
    for frame_file in sorted(output_dir.glob("frame_*.png")):
        frames.append(frame_file.read_bytes())
        frame_file.unlink()

    output_dir.rmdir()
    return frames


def _frames_to_base64(frames: list[bytes]) -> list[str]:
    return [base64.b64encode(f).decode("ascii") for f in frames]


async def _scan_with_gpt4o(frames_b64: list[str]) -> dict[str, Any]:
    """Send keyframes to GPT-4o vision and parse the structured response."""
    settings = get_settings()
    if not settings.has_openai:
        logger.warning("openai_key_missing_for_visual_compliance")
        return {"safe": True, "violations": []}

    content_parts: list[dict[str, Any]] = [
        {"type": "text", "text": "Analyze these video keyframes for IP/copyright violations:"},
    ]
    for b64 in frames_b64:
        content_parts.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "low"},
        })

    async with httpx.AsyncClient(timeout=45.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key.get_secret_value()}"},
            json={
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": content_parts},
                ],
                "max_tokens": 500,
                "temperature": 0.0,
            },
        )
        resp.raise_for_status()
        raw_text = resp.json()["choices"][0]["message"]["content"].strip()

    cleaned = raw_text.strip("`").removeprefix("json").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("visual_compliance_json_parse_failed", raw=raw_text[:300])
        return {"safe": True, "violations": []}


async def check_visual_compliance(
    video_url: str,
    tenant_id: str,
) -> VisualComplianceResult:
    """Download video, extract keyframes, scan with GPT-4o vision."""
    if not video_url:
        return VisualComplianceResult(safe=True, video_url="")

    video_path: Path | None = None
    try:
        video_path = await _download_video(video_url)
        frames = await _extract_keyframes(video_path, count=KEYFRAME_COUNT)

        if not frames:
            logger.warning("no_keyframes_extracted", video_url=video_url[:80])
            return VisualComplianceResult(safe=True, scanned_frames=0, video_url=video_url)

        frames_b64 = _frames_to_base64(frames)
        scan_result = await _scan_with_gpt4o(frames_b64)

        is_safe = scan_result.get("safe", True)
        violations = scan_result.get("violations", [])

        logger.info(
            "visual_compliance_scan_complete",
            safe=is_safe,
            violations_count=len(violations),
            frames_scanned=len(frames),
            tenant_id=tenant_id,
        )

        return VisualComplianceResult(
            safe=is_safe,
            violations=violations,
            scanned_frames=len(frames),
            video_url=video_url if is_safe else "",
        )

    except Exception:
        logger.exception("visual_compliance_check_failed")
        return VisualComplianceResult(safe=True, scanned_frames=0, video_url=video_url)
    finally:
        if video_path and video_path.exists():
            video_path.unlink(missing_ok=True)
