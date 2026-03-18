# OrchestraAI Marketing Video -- Production Guide

## Overview

This document contains everything needed to produce a 60-second marketing video for OrchestraAI. The video will be used across Product Hunt, the landing page, Twitter/LinkedIn, and paid social.

**Generated video:** `docs/orchestraai_marketing_60s.mp4` (60s, 832x1120, 25fps, 25MB)

---

## Section 0: Model Selection (Revised)

The original plan used `fal-ai/ai-avatar/single-text`, but that model caps at **241 frames (9.6s at 25fps)** regardless of transcript length. The actual workflow uses a two-step approach:

1. **OpenAI TTS** (`tts-1-hd`, voice: `onyx`, speed: 1.7) to generate the 60-second narration audio
2. **ByteDance Omnihuman 1.5** (`fal-ai/bytedance/omnihuman/v1.5`) to generate lip-synced video from image + audio

| Model | Cost/sec | Max Duration | Input | Notes |
|-------|----------|-------------|-------|-------|
| `fal-ai/ai-avatar/single-text` | $0.20 | **~9.6s (241 frames)** | text + image | Built-in TTS but hard frame cap |
| `fal-ai/bytedance/omnihuman/v1.5` | $0.16 | **60s at 720p** | audio + image | Requires separate TTS step |
| `fal-ai/stable-avatar` | $0.10 | **5 minutes** | audio + image | Cheapest but slow GPU availability |

### Actual Cost Breakdown

| Step | Service | Cost |
|------|---------|------|
| TTS audio generation | OpenAI `tts-1-hd` | ~$0.02 |
| Video generation | Omnihuman 1.5 (60s at 720p) | ~$9.60 |
| **Total** | | **~$9.62** |

---

## Section 1: Complete Two-Step Workflow

### Step 1: Generate Audio with OpenAI TTS

```python
from openai import OpenAI

client = OpenAI()  # uses OPENAI_API_KEY from env

response = client.audio.speech.create(
    model="tts-1-hd",
    voice="onyx",
    input=TRANSCRIPT,  # see Section 2 for full transcript
    response_format="mp3",
    speed=1.7,  # calibrated to fit ~195 words into ~60 seconds
)
response.stream_to_file("marketing_narration.mp3")
```

Trim the output to under 60 seconds if needed (Omnihuman 1.5 hard limit).

### Step 2: Generate Video with Omnihuman 1.5

```python
import fal_client

result = fal_client.subscribe(
    "fal-ai/bytedance/omnihuman/v1.5",
    arguments={
        "image_url": "<YOUR_UPLOADED_IMAGE_URL>",
        "audio_url": "<YOUR_UPLOADED_AUDIO_URL>",
        "resolution": "720p",
        "seed": 42,
    },
    with_logs=True,
    on_queue_update=lambda update: (
        [print(log["message"]) for log in update.logs]
        if isinstance(update, fal_client.InProgress)
        else None
    ),
)
print("Video URL:", result["video"]["url"])
```

Before running, set your API keys:
- `export FAL_KEY=<your-fal-api-key>`
- `export OPENAI_API_KEY=<your-openai-api-key>`

---

## Section 1b: Legacy API Payload (fal-ai/ai-avatar -- 9.6s clips only)

> **Warning:** This model produces a maximum of 9.6 seconds per generation (241 frames at 25fps). It is NOT suitable for a single 60-second video. Kept here for reference only.

### Model

- **Model ID:** `fal-ai/ai-avatar/single-text`
- **Endpoint:** `https://fal.run/fal-ai/ai-avatar/single-text`
- **Pricing:** $0.20 per second of output video
- **Actual cost per generation:** ~$7.71 (for 9.6s clip)

### Input Parameters

#### `image_url` -- Avatar Source Image

Upload a headshot to fal.ai storage first, then use the returned URL. The image must meet these specifications:

- **Subject:** A man in his early-to-mid 30s with a clean, trustworthy, approachable look. Short dark brown hair, neatly trimmed on the sides, slightly longer on top. Light stubble (one to two days of growth). Clear skin. No glasses.
- **Expression:** Slight closed-mouth smile. Relaxed brow. Eyes looking directly at the camera.
- **Wardrobe:** Dark navy crew-neck sweater over a white collared shirt. The white collar should be visible at the neckline. No tie, no blazer, no logos.
- **Framing:** Head and shoulders only. Centered in frame. Shot from chest level up.
- **Background of the photo:** Solid matte dark charcoal, hex #1c1c1e. No gradient, no texture, no objects behind the subject.
- **Lighting of the photo:** Soft diffused key light from camera-left at roughly 45 degrees. Subtle cool-toned rim light from behind-right to separate the subject from the background. No harsh shadows under the nose or chin. Catchlights visible in both eyes.
- **Image format:** PNG or JPG, minimum 512x512 pixels, aspect ratio close to 1:1 or 3:4.

**Where to get this image:** Use a royalty-free professional headshot from [unsplash.com](https://unsplash.com/s/photos/business-portrait-dark-background) or [pexels.com](https://www.pexels.com/search/business%20portrait%20dark%20background/). Search for "professional man portrait dark background studio lighting." Alternatively, generate one using an AI image generator with the description above.

#### `voice` -- Speech Voice

```
"Roger"
```

Roger is a confident, clear American male voice with moderate depth. Standard American English accent with no regional dialect. Authoritative but not aggressive. Suitable for SaaS product marketing.

**Alternative:** Use `"Daniel"` for a slightly more British-inflected professional tone, or `"Sarah"` for a clear, confident American female voice.

#### `resolution`

```
"720p"
```

720p balances quality and credit cost. Do not use 480p for marketing material.

#### `num_frames`

```
241
```

241 frames is the maximum allowed. At the default frame rate this produces the longest possible video. The transcript below is calibrated to fit within this duration at natural speaking pace (~145 words per minute).

#### `acceleration`

```
"regular"
```

Regular acceleration provides the best quality. Use `"high"` only if testing drafts to save credits.

#### `seed`

```
42
```

Fixed seed for reproducibility. Change this number to get a different generation with the same inputs.

#### `prompt` -- Visual Scene Description

This field tells the model what the avatar is doing and how the scene looks. It does NOT contain the spoken words (that goes in `text_input`).

```
A confident male tech founder in his early thirties presents a product to the camera. He wears a dark navy crew-neck sweater over a white collared shirt. He is seated in a modern, dimly lit studio with a solid matte charcoal background. Soft key light illuminates his face from the left. A subtle cool rim light separates him from the dark background. He speaks directly to the camera with natural hand gestures, occasional nods, and steady eye contact. His expression shifts from serious concern when describing a problem to confident enthusiasm when presenting the solution. The framing is a medium shot from the chest up. The mood is professional, modern, and authoritative -- like a YC demo day pitch.
```

#### `text_input` -- Spoken Transcript

This is the exact text the avatar will speak. See Section 2 below for the full transcript.

### Complete API Call

```json
{
  "image_url": "<YOUR_UPLOADED_IMAGE_URL>",
  "text_input": "Marketing teams are drowning. Nine platforms. Nine dashboards. Nine separate budgets -- and none of them talk to each other. One misconfigured bid on Google Ads can drain five thousand dollars before anyone notices. Your Instagram campaign doesn't know your LinkedIn one is underperforming. Budget gets wasted in silos.\n\nWe built OrchestraAI to fix this.\n\nOne AI layer that connects Twitter, YouTube, TikTok, Pinterest, Facebook, Instagram, LinkedIn, Snapchat, and Google Ads -- all nine -- under a single intelligent orchestrator. You type a natural language command like 'generate a video ad for our summer sale,' and our ten-node LangGraph agent handles everything: intent classification, compliance checking, content generation, AI video creation with Seedance two-point-oh, automated copyright scanning with GPT-4o Vision, policy validation, and cross-platform publishing. All in one request.\n\nBut here is what no other tool does: financial guardrails.\n\nThree-phase bidding that starts fully human-approved and earns autonomy over time. Three-tier spend caps -- daily, weekly, monthly -- that cannot be overridden. Statistical anomaly detection using Z-scores and IQR. And a kill switch that halts all spend across every platform in one click.\n\nEvery campaign you run makes the AI smarter for your business. Our data moat compounds your advantage over time -- your competitors cannot replicate your performance data.\n\nOrchestraAI is live today. Self-host it with Docker in sixty seconds, or use Enterprise Cloud starting at ninety-nine dollars a month. Open-core. Apache two-point-oh licensed.\n\nStop managing nine dashboards. Start orchestrating. Visit use orchestra dot dev.",
  "voice": "Roger",
  "prompt": "A confident male tech founder in his early thirties presents a product to the camera. He wears a dark navy crew-neck sweater over a white collared shirt. He is seated in a modern, dimly lit studio with a solid matte charcoal background. Soft key light illuminates his face from the left. A subtle cool rim light separates him from the dark background. He speaks directly to the camera with natural hand gestures, occasional nods, and steady eye contact. His expression shifts from serious concern when describing a problem to confident enthusiasm when presenting the solution. The framing is a medium shot from the chest up. The mood is professional, modern, and authoritative -- like a YC demo day pitch.",
  "num_frames": 241,
  "resolution": "720p",
  "seed": 42,
  "acceleration": "regular"
}
```

### Python Script to Generate

```python
import fal_client

result = fal_client.subscribe(
    "fal-ai/ai-avatar/single-text",
    arguments={
        "image_url": "<YOUR_UPLOADED_IMAGE_URL>",
        "text_input": (
            "Marketing teams are drowning. Nine platforms. Nine dashboards. "
            "Nine separate budgets -- and none of them talk to each other. "
            "One misconfigured bid on Google Ads can drain five thousand dollars "
            "before anyone notices. Your Instagram campaign doesn't know your "
            "LinkedIn one is underperforming. Budget gets wasted in silos.\n\n"
            "We built OrchestraAI to fix this.\n\n"
            "One AI layer that connects Twitter, YouTube, TikTok, Pinterest, "
            "Facebook, Instagram, LinkedIn, Snapchat, and Google Ads -- all nine "
            "-- under a single intelligent orchestrator. You type a natural "
            "language command like 'generate a video ad for our summer sale,' and "
            "our ten-node LangGraph agent handles everything: intent classification, "
            "compliance checking, content generation, AI video creation with Seedance "
            "two-point-oh, automated copyright scanning with GPT-4o Vision, policy "
            "validation, and cross-platform publishing. All in one request.\n\n"
            "But here is what no other tool does: financial guardrails.\n\n"
            "Three-phase bidding that starts fully human-approved and earns autonomy "
            "over time. Three-tier spend caps -- daily, weekly, monthly -- that "
            "cannot be overridden. Statistical anomaly detection using Z-scores and "
            "IQR. And a kill switch that halts all spend across every platform in "
            "one click.\n\n"
            "Every campaign you run makes the AI smarter for your business. Our data "
            "moat compounds your advantage over time -- your competitors cannot "
            "replicate your performance data.\n\n"
            "OrchestraAI is live today. Self-host it with Docker in sixty seconds, "
            "or use Enterprise Cloud starting at ninety-nine dollars a month. "
            "Open-core. Apache two-point-oh licensed.\n\n"
            "Stop managing nine dashboards. Start orchestrating. "
            "Visit use orchestra dot dev."
        ),
        "voice": "Roger",
        "prompt": (
            "A confident male tech founder in his early thirties presents a product "
            "to the camera. He wears a dark navy crew-neck sweater over a white "
            "collared shirt. He is seated in a modern, dimly lit studio with a solid "
            "matte charcoal background. Soft key light illuminates his face from the "
            "left. A subtle cool rim light separates him from the dark background. "
            "He speaks directly to the camera with natural hand gestures, occasional "
            "nods, and steady eye contact. His expression shifts from serious concern "
            "when describing a problem to confident enthusiasm when presenting the "
            "solution. The framing is a medium shot from the chest up. The mood is "
            "professional, modern, and authoritative -- like a YC demo day pitch."
        ),
        "num_frames": 241,
        "resolution": "720p",
        "seed": 42,
        "acceleration": "regular",
    },
    with_logs=True,
    on_queue_update=lambda update: (
        [print(log["message"]) for log in update.logs]
        if isinstance(update, fal_client.InProgress)
        else None
    ),
)
print("Video URL:", result["video"]["url"])
```

Before running, set your API key: `export FAL_KEY=<your-fal-api-key>`

---

## Section 2: Transcript -- Annotated by Act

Total word count: ~195 words. Target delivery: 60-70 seconds at ~155 wpm (slightly brisk, energetic pace).

### Act 1 -- The Problem (0:00 - 0:12)

> Marketing teams are drowning. Nine platforms. Nine dashboards. Nine separate budgets -- and none of them talk to each other. One misconfigured bid on Google Ads can drain five thousand dollars before anyone notices. Your Instagram campaign doesn't know your LinkedIn one is underperforming. Budget gets wasted in silos.

**Tone:** Serious, empathetic. Slow pace. Let the pain resonate.
**Avatar expression:** Slight frown, steady eye contact, small head shake on "none of them talk to each other."

### Act 2 -- The Solution (0:12 - 0:32)

> We built OrchestraAI to fix this.
>
> One AI layer that connects Twitter, YouTube, TikTok, Pinterest, Facebook, Instagram, LinkedIn, Snapchat, and Google Ads -- all nine -- under a single intelligent orchestrator. You type a natural language command like "generate a video ad for our summer sale," and our ten-node LangGraph agent handles everything: intent classification, compliance checking, content generation, AI video creation with Seedance two-point-oh, automated copyright scanning with GPT-4o Vision, policy validation, and cross-platform publishing. All in one request.

**Tone:** Confident, building energy. Pace picks up slightly when listing the nine platforms. Brief pause after "all nine" for emphasis.
**Avatar expression:** Leans in slightly. Gestures with one hand when listing platforms.

### Act 3 -- The Differentiator (0:32 - 0:50)

> But here is what no other tool does: financial guardrails.
>
> Three-phase bidding that starts fully human-approved and earns autonomy over time. Three-tier spend caps -- daily, weekly, monthly -- that cannot be overridden. Statistical anomaly detection using Z-scores and IQR. And a kill switch that halts all spend across every platform in one click.
>
> Every campaign you run makes the AI smarter for your business. Our data moat compounds your advantage over time -- your competitors cannot replicate your performance data.

**Tone:** Authoritative, decisive. This is the section that separates OrchestraAI from every competitor. Slow down on "cannot be overridden" and "one click" for gravity.
**Avatar expression:** Direct gaze, slight forward lean, confident nod on "kill switch."

### Act 4 -- The CTA (0:50 - 0:60)

> OrchestraAI is live today. Self-host it with Docker in sixty seconds, or use Enterprise Cloud starting at ninety-nine dollars a month. Open-core. Apache two-point-oh licensed.
>
> Stop managing nine dashboards. Start orchestrating. Visit use orchestra dot dev.

**Tone:** Warm, inviting, energetic. The closing line ("Stop managing... Start orchestrating.") should land like a tagline -- brief pause before it, then deliver with conviction.
**Avatar expression:** Slight smile returns. Nods once on the final sentence.

---

## Section 3: Post-Production -- Combining Avatar with Screen Recordings

The raw AI Avatar video is a talking head on a dark background. To make a polished marketing video, overlay screen recordings of the actual product UI at key moments. This creates a "founder narrates while you see the product" format used by top SaaS launches.

### Screen Recordings to Capture

Record these from the live app at `useorchestra.dev` (or localhost) using OBS, Loom, or any screen recorder. Record at 1920x1080 in a browser with no bookmarks bar visible.

| Clip | What to Record | Duration | Overlay During |
|------|---------------|----------|---------------|
| **A** | Login page -- show the dark OrchestraAI Cloud login screen with the indigo logo | 3 seconds | Act 1 opening (0:02 - 0:05) |
| **B** | AI Orchestrator -- type "Generate a video ad for our summer sale" and show the response streaming in with intent badge, compliance check, generated content, video player, and policy validation | 8 seconds | Act 2 (0:16 - 0:24) |
| **C** | Generated video playing -- the Seedance-generated video clip playing inline in the orchestrator chat | 4 seconds | Act 2 (0:24 - 0:28) |
| **D** | Billing page -- show the Starter ($99) and Agency ($999) plan cards with the indigo and amber styling | 3 seconds | Act 4 (0:52 - 0:55) |
| **E** | Dashboard -- show the metrics cards and platform performance bar chart | 3 seconds | Act 4 (0:55 - 0:58) |

### Editing Timeline

```
0:00 ─────── Avatar speaks (full frame) ─────── 0:12
0:12 ── Avatar (left 40%) + Screen recording B (right 60%) ── 0:28
0:28 ─────── Avatar speaks (full frame) ─────── 0:50
0:50 ── Avatar (left 40%) + Screen recordings D & E ── 0:58
0:58 ─────── Avatar speaks final line (full frame) ─────── 0:60
```

### Lower-Third Text Overlays

Add these as subtle white-on-transparent text at the bottom of the frame during the corresponding acts:

| Timestamp | Text |
|-----------|------|
| 0:03 | 9 Platforms. 9 Dashboards. Zero Visibility. |
| 0:14 | Twitter / YouTube / TikTok / Pinterest / Facebook / Instagram / LinkedIn / Snapchat / Google Ads |
| 0:20 | 10-Node LangGraph AI Agent |
| 0:34 | 3-Phase Guardrailed Bidding |
| 0:40 | Anomaly Detection + Kill Switch |
| 0:46 | Your Data Moat. Your Competitive Advantage. |
| 0:52 | Starter $99/mo -- Agency $999/mo |
| 0:58 | useorchestra.dev |

### Recommended Free Editors

- **CapCut Desktop** (free, supports overlays, text, transitions, export to 1080p)
- **DaVinci Resolve** (free, professional-grade, steeper learning curve)
- **Canva Video Editor** (free tier, browser-based, drag-and-drop)

### Export Settings

- **Resolution:** 1920x1080 (1080p)
- **Frame rate:** 30 fps
- **Codec:** H.264
- **Bitrate:** 10-15 Mbps
- **Audio:** AAC 192 kbps stereo
- **Format:** MP4

### Where to Upload the Final Video

| Platform | Specs | Notes |
|----------|-------|-------|
| Product Hunt | MP4, 1080p, under 3 minutes | Upload as "Video" media in the listing |
| Twitter/X | MP4, 1080p, under 2:20 | Pin as first tweet in the launch thread |
| LinkedIn | MP4, 1080p, under 10 minutes | Native upload (not YouTube link) for better reach |
| Landing page | MP4 or embed from YouTube | Host on YouTube (unlisted) and embed, or self-host |
| GitHub README | GIF or link | Convert to GIF for README, or link to YouTube |

---

## Quick-Start Checklist

1. Find or generate a headshot image matching the specifications in Section 1
2. Upload the image to fal.ai storage and get the URL
3. Copy the complete API call JSON from Section 1, replacing `<YOUR_UPLOADED_IMAGE_URL>`
4. Run the API call via the fal.ai playground or the Python script
5. Download the generated video
6. Record the 5 screen captures listed in Section 3
7. Combine avatar video + screen recordings in CapCut or DaVinci Resolve
8. Add lower-third text overlays per the timing table
9. Export as 1080p MP4
10. Upload to Product Hunt, Twitter, LinkedIn, and the landing page
