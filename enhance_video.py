"""
OrchestraAI Marketing Video Post-Production Pipeline
=====================================================
Adds captions, background music, thumbnail, and multi-platform exports.
Base: docs/video/orchestraai_marketing_60s_075x.mp4 (80.68s, 832x1120, 25fps)
"""

import sys
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(line_buffering=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "docs", "video")
BASE_VIDEO = os.path.join(VIDEO_DIR, "orchestraai_marketing_60s_075x.mp4")
FFMPEG = r"C:\Users\naghm\AppData\Local\Programs\Python\Python311\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"

FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"
FONT_REGULAR = r"C:\Windows\Fonts\arial.ttf"

# Full transcript subtitles — timestamps from Whisper word-level transcription
CAPTIONS = [
    # Act 1 — The Problem
    ( 0.00,  1.50, "Marketing teams are drowning."),
    ( 1.66,  2.74, "Nine platforms. Nine dashboards.\nNine separate budgets —"),
    ( 4.76,  1.20, "and none of them\ntalk to each other."),
    ( 6.64,  3.26, "One misconfigured bid on Google Ads\ncan drain $5,000 before anyone notices."),
    (10.24,  2.74, "Your Instagram campaign doesn't know\nyour LinkedIn one is underperforming."),
    (13.28,  1.16, "Budget gets wasted in silos."),

    # Act 2 — The Solution
    (15.10,  1.66, "We built OrchestraAI to fix this."),
    (17.50,  3.74, "One AI layer that connects Twitter,\nYouTube, TikTok, Pinterest, Facebook,"),
    (21.58,  3.46, "Instagram, LinkedIn, Snapchat, and\nGoogle Ads — all nine —"),
    (23.62,  1.42, "under a single\nintelligent orchestrator."),
    (25.78,  3.24, "You type a natural language command like\n\"generate a video ad for our summer sale,\""),
    (29.18,  2.12, "and our ten-node LangGraph agent\nhandles everything:"),
    (31.82,  1.52, "Intent classification,\ncompliance checking,"),
    (33.66,  2.18, "content generation, AI video creation\nwith Seedance 2.0,"),
    (37.20,  1.86, "automated copyright scanning\nwith GPT-4o Vision,"),
    (39.60,  1.88, "policy validation, and\ncross-platform publishing."),
    (42.14,  0.86, "All in one request."),

    # Act 3 — The Differentiator
    (43.50,  2.52, "But here's what no other tool does:\nfinancial guardrails."),
    (46.76,  3.16, "Three-phase bidding that starts fully\nhuman-approved and earns autonomy over time."),
    (50.56,  3.30, "Three-tier spend caps — daily, weekly,\nmonthly — that cannot be overridden."),
    (54.54,  2.94, "Statistical anomaly detection\nusing Z-scores and IQR."),
    (57.48,  2.74, "And a kill switch that halts all spend\nacross every platform in one click."),
    (60.96,  2.42, "Every campaign you run makes\nthe AI smarter for your business."),
    (63.56,  1.92, "Our data moat compounds\nyour advantage over time."),
    (65.96,  2.14, "Your competitors cannot replicate\nyour performance data."),

    # Act 4 — The CTA
    (68.78,  0.96, "OrchestraAI is live today."),
    (70.06,  1.56, "Self-host it with Docker\nin sixty seconds,"),
    (71.88,  2.28, "or use Enterprise Cloud\nstarting at $99 a month."),
    (74.68,  1.80, "Open-core.\nApache 2.0 licensed."),
    (77.06,  1.16, "Stop managing nine dashboards."),
    (78.60,  0.66, "Start orchestrating."),
]

FADE_DUR = 0.3  # seconds


# ---------------------------------------------------------------------------
# Step 1: Render captions onto video (no audio change)
# ---------------------------------------------------------------------------
def render_caption_frame(text, width, height, opacity=1.0):
    """Return an RGBA numpy array with the caption pill overlay."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_size = max(20, int(height * 0.028))
    font = ImageFont.truetype(FONT_BOLD, font_size)

    lines = text.split("\n")
    line_bboxes = [draw.textbbox((0, 0), line, font=font) for line in lines]
    line_heights = [bb[3] - bb[1] for bb in line_bboxes]
    line_widths = [bb[2] - bb[0] for bb in line_bboxes]
    total_text_h = sum(line_heights) + (len(lines) - 1) * int(font_size * 0.4)
    max_text_w = max(line_widths)

    pad_x, pad_y = int(font_size * 1.2), int(font_size * 0.6)
    pill_w = max_text_w + 2 * pad_x
    pill_h = total_text_h + 2 * pad_y
    pill_x = (width - pill_w) // 2
    pill_y = height - int(height * 0.12) - pill_h

    alpha = int(180 * opacity)
    draw.rounded_rectangle(
        [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
        radius=int(font_size * 0.5),
        fill=(15, 15, 20, alpha),
    )

    y_cursor = pill_y + pad_y
    text_alpha = int(255 * opacity)
    for i, line in enumerate(lines):
        lw = line_widths[i]
        lx = (width - lw) // 2
        draw.text((lx, y_cursor), line, font=font, fill=(255, 255, 255, text_alpha))
        y_cursor += line_heights[i] + int(font_size * 0.4)

    return np.array(img)


def build_captioned_video():
    """Overlay captions on every frame, output a video without audio."""
    from moviepy import VideoFileClip, VideoClip

    print("[1/5] Loading base video...", flush=True)
    base = VideoFileClip(BASE_VIDEO)
    w, h = base.size
    fps = base.fps
    dur = base.duration
    print(f"  Base: {w}x{h}, {fps}fps, {dur:.2f}s", flush=True)

    def get_caption_opacity(t):
        """Return (text, opacity) for a given time, or None."""
        for start, length, text in CAPTIONS:
            if start <= t < start + length:
                elapsed = t - start
                if elapsed < FADE_DUR:
                    return text, elapsed / FADE_DUR
                elif elapsed > length - FADE_DUR:
                    return text, (length - elapsed) / FADE_DUR
                else:
                    return text, 1.0
        return None, 0.0

    def make_frame(t):
        frame = base.get_frame(t)
        text, opacity = get_caption_opacity(t)
        if text and opacity > 0:
            overlay = render_caption_frame(text, w, h, opacity)
            alpha = overlay[:, :, 3:4].astype(np.float32) / 255.0
            rgb = overlay[:, :, :3].astype(np.float32)
            frame = frame.astype(np.float32)
            frame = frame * (1 - alpha) + rgb * alpha
            frame = np.clip(frame, 0, 255).astype(np.uint8)
        return frame

    print("[1/5] Rendering captions...", flush=True)
    captioned = VideoClip(make_frame, duration=dur).with_fps(fps)

    out_path = os.path.join(VIDEO_DIR, "_captioned_noaudio.mp4")
    captioned.write_videofile(out_path, codec="libx264", fps=int(fps), audio=False, logger="bar")
    base.close()
    print("[1/5] Captioned video saved.", flush=True)
    return out_path


# ---------------------------------------------------------------------------
# Step 2: Master export (captions + original audio, no background music)
# ---------------------------------------------------------------------------
def build_master(captioned_video_path):
    """Combine captioned video frames with original narration audio."""
    import subprocess

    print("[2/5] Building master (captions + narration, no music)...", flush=True)
    master_path = os.path.join(VIDEO_DIR, "orchestraai_final.mp4")
    subprocess.run(
        [
            FFMPEG, "-y",
            "-i", captioned_video_path,
            "-i", BASE_VIDEO,
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
            "-shortest", master_path,
        ],
        capture_output=True,
    )
    print("[2/5] Master exported.", flush=True)
    return master_path


# ---------------------------------------------------------------------------
# Step 3: Thumbnail
# ---------------------------------------------------------------------------
def generate_thumbnails(master_path):
    """Extract frame and create branded thumbnails."""
    from moviepy import VideoFileClip

    print("[3/5] Generating thumbnails...", flush=True)
    vid = VideoFileClip(master_path)
    frame = vid.get_frame(27)  # ~27s, solution section
    vid.close()

    frame_img = Image.fromarray(frame)
    src_w, src_h = frame_img.size

    for label, out_w, out_h, filename in [
        ("landscape", 1280, 720, "thumbnail.png"),
        ("portrait", 832, 1120, "thumbnail_portrait.png"),
    ]:
        thumb = Image.new("RGB", (out_w, out_h), (15, 15, 20))

        scale = max(out_w / src_w, out_h / src_h)
        resized_w = int(src_w * scale)
        resized_h = int(src_h * scale)
        resized = frame_img.resize((resized_w, resized_h), Image.LANCZOS)
        paste_x = (out_w - resized_w) // 2
        paste_y = (out_h - resized_h) // 2
        thumb.paste(resized, (paste_x, paste_y))

        draw = ImageDraw.Draw(thumb, "RGBA")

        # Dark gradient overlay on bottom third
        grad_top = int(out_h * 0.55)
        for y in range(grad_top, out_h):
            alpha = int(200 * ((y - grad_top) / (out_h - grad_top)))
            draw.line([(0, y), (out_w, y)], fill=(10, 10, 15, alpha))

        # Title text
        title_size = max(24, int(out_h * 0.07))
        sub_size = max(16, int(out_h * 0.04))
        title_font = ImageFont.truetype(FONT_BOLD, title_size)
        sub_font = ImageFont.truetype(FONT_REGULAR, sub_size)

        title = "OrchestraAI"
        subtitle = "One AI. Nine Platforms."

        title_bb = draw.textbbox((0, 0), title, font=title_font)
        sub_bb = draw.textbbox((0, 0), subtitle, font=sub_font)

        title_x = (out_w - (title_bb[2] - title_bb[0])) // 2
        title_y = int(out_h * 0.75)
        sub_x = (out_w - (sub_bb[2] - sub_bb[0])) // 2
        sub_y = title_y + title_size + int(title_size * 0.3)

        # Text shadow
        for dx, dy in [(2, 2), (-1, -1), (1, -1), (-1, 1)]:
            draw.text((title_x + dx, title_y + dy), title, font=title_font, fill=(0, 0, 0, 180))
        draw.text((title_x, title_y), title, font=title_font, fill=(255, 255, 255, 255))

        for dx, dy in [(1, 1)]:
            draw.text((sub_x + dx, sub_y + dy), subtitle, font=sub_font, fill=(0, 0, 0, 150))
        draw.text((sub_x, sub_y), subtitle, font=sub_font, fill=(200, 200, 220, 255))

        # Play button (circle + triangle)
        cx, cy = out_w // 2, int(out_h * 0.42)
        r = int(min(out_w, out_h) * 0.07)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 60), outline=(255, 255, 255, 140), width=2)
        tri_size = int(r * 0.6)
        tri_offset = int(tri_size * 0.15)
        tri = [
            (cx - tri_size // 2 + tri_offset, cy - tri_size),
            (cx - tri_size // 2 + tri_offset, cy + tri_size),
            (cx + tri_size + tri_offset, cy),
        ]
        draw.polygon(tri, fill=(255, 255, 255, 180))

        out_path = os.path.join(VIDEO_DIR, filename)
        thumb.convert("RGB").save(out_path, quality=95)
        print(f"  Saved {label} thumbnail: {filename}", flush=True)

    print("[3/5] Thumbnails done.", flush=True)


# ---------------------------------------------------------------------------
# Step 5: Multi-platform aspect ratio exports
# ---------------------------------------------------------------------------
def export_aspect_ratios(master_path):
    """Export 16:9, 9:16, and 1:1 versions using ffmpeg."""
    import subprocess

    print("[4/5] Exporting aspect ratio variants...", flush=True)

    # 16:9 landscape (1920x1080) -- pillarbox with blurred background
    out_16x9 = os.path.join(VIDEO_DIR, "orchestraai_16x9.mp4")
    subprocess.run(
        [
            FFMPEG, "-y", "-i", master_path,
            "-filter_complex",
            "[0:v]split[bg][fg];"
            "[bg]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,gblur=sigma=40,setsar=1[blurred];"
            "[fg]scale=-2:1080[scaled];"
            "[blurred][scaled]overlay=(W-w)/2:(H-h)/2[out]",
            "-map", "[out]", "-map", "0:a",
            "-c:v", "libx264", "-crf", "20", "-c:a", "aac", "-b:a", "128k",
            "-r", "25", out_16x9,
        ],
        capture_output=True,
    )
    print(f"  16:9 landscape: {os.path.basename(out_16x9)}", flush=True)

    # 9:16 portrait (1080x1920) -- upscale from 832x1120
    out_9x16 = os.path.join(VIDEO_DIR, "orchestraai_9x16.mp4")
    subprocess.run(
        [
            FFMPEG, "-y", "-i", master_path,
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0f0f14",
            "-c:v", "libx264", "-crf", "20", "-c:a", "aac", "-b:a", "128k",
            "-r", "25", out_9x16,
        ],
        capture_output=True,
    )
    print(f"  9:16 portrait:  {os.path.basename(out_9x16)}", flush=True)

    # 1:1 square (1080x1080) -- center crop focusing on head/shoulders
    out_1x1 = os.path.join(VIDEO_DIR, "orchestraai_1x1.mp4")
    subprocess.run(
        [
            FFMPEG, "-y", "-i", master_path,
            "-vf", "crop=ih*832/1120:ih:0:0,scale=1080:1080",
            "-c:v", "libx264", "-crf", "20", "-c:a", "aac", "-b:a", "128k",
            "-r", "25", out_1x1,
        ],
        capture_output=True,
    )
    print(f"  1:1 square:     {os.path.basename(out_1x1)}", flush=True)

    print("[4/5] All aspect ratios exported.", flush=True)


# ---------------------------------------------------------------------------
# Step 6: Cleanup
# ---------------------------------------------------------------------------
def cleanup():
    temp = os.path.join(VIDEO_DIR, "_captioned_noaudio.mp4")
    if os.path.exists(temp):
        os.remove(temp)
        print("[5/5] Cleaned up temp files.", flush=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60, flush=True)
    print("OrchestraAI Video Post-Production Pipeline", flush=True)
    print("=" * 60, flush=True)

    captioned_path = build_captioned_video()
    master_path = build_master(captioned_path)
    generate_thumbnails(master_path)
    export_aspect_ratios(master_path)
    cleanup()

    print("\n" + "=" * 60, flush=True)
    print("DONE! Output files:", flush=True)
    for f in os.listdir(VIDEO_DIR):
        fp = os.path.join(VIDEO_DIR, f)
        if os.path.isfile(fp):
            size = os.path.getsize(fp) / (1024 * 1024)
            print(f"  {f:45s} {size:7.1f} MB", flush=True)
    print("=" * 60, flush=True)
