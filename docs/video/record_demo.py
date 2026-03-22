"""
OrchestraAI Demo Video Generator v4
====================================
Playwright video recording with precise timing matched to each
animation on the website, plus ffmpeg post-processing.

Fixes from v3:
  - Scene 2: Wait for full typing + pipeline animation after clicking prompt
  - Scene 3: Wait for compliance checklist + cross-platform to fully animate
  - No grey/blank screens: overlay background matches site, resilient fade
  - Better scroll offsets to keep content centered in viewport
"""

import asyncio
import subprocess
import time
from pathlib import Path
from playwright.async_api import async_playwright

SITE = "https://www.useorchestra.dev"
VIDEO_DIR = Path(__file__).parent
RAW_VIDEO = VIDEO_DIR / "raw_recording.webm"
STABILIZED = VIDEO_DIR / "stabilized.mp4"
NARRATION = VIDEO_DIR / "narration_full.mp3"
FINAL_OUTPUT = VIDEO_DIR / "orchestraai_demo.mp4"

WIDTH = 1920
HEIGHT = 1080

SCENE_DURATIONS = {
    "hook": 16.8,
    "command": 14.6,
    "compliance": 25.0,
    "dashboard": 16.8,
    "cta": 12.3,
}


def log(msg):
    print(msg, flush=True)


async def wall_sleep(seconds: float):
    """Sleep for exactly `seconds` of wall-clock time."""
    await asyncio.sleep(seconds)


async def smooth_scroll(page, target_y: int, duration_s: float = 2.0):
    """JS rAF-driven smooth scroll, then sleep remaining wall time."""
    t0 = time.monotonic()
    await page.evaluate(f"""
        new Promise(resolve => {{
            const start = window.scrollY;
            const delta = {target_y} - start;
            const dur = {duration_s * 1000};
            const t0 = performance.now();
            function step(now) {{
                const t = Math.min((now - t0) / dur, 1);
                const e = t < 0.5 ? 4*t*t*t : 1 - Math.pow(-2*t+2, 3)/2;
                window.scrollTo(0, start + delta * e);
                if (t < 1) requestAnimationFrame(step); else resolve();
            }}
            requestAnimationFrame(step);
        }})
    """)
    remaining = duration_s - (time.monotonic() - t0)
    if remaining > 0:
        await asyncio.sleep(remaining)


async def scroll_to_text(page, text: str, offset: int = -200, duration_s: float = 2.5):
    """Find element by text and smooth-scroll to it."""
    safe = text.replace("'", "\\'")
    y = await page.evaluate(f"""(() => {{
        const els = [...document.querySelectorAll('h1,h2,h3,h4,span,button,p')];
        const el = els.find(e => e.textContent && e.textContent.includes('{safe}'));
        if (!el) return null;
        return window.scrollY + el.getBoundingClientRect().top;
    }})()""")
    if y is not None:
        await smooth_scroll(page, max(0, int(y) + offset), duration_s)
    else:
        cur = await page.evaluate("window.scrollY")
        await smooth_scroll(page, cur + 600, duration_s)


async def setup_page(page):
    """Inject overlay and disable CSS scroll-behavior after each navigation."""
    await page.evaluate("""(() => {
        let ov = document.getElementById('fade-overlay');
        if (!ov) {
            ov = document.createElement('div');
            ov.id = 'fade-overlay';
            document.body.appendChild(ov);
        }
        ov.style.cssText = 'position:fixed;inset:0;background:#000;opacity:0;z-index:999999;pointer-events:none;transition:opacity 0.5s ease;';
        document.documentElement.style.scrollBehavior = 'auto';
        document.body.style.scrollBehavior = 'auto';
    })()""")


async def fade_out(page, dur: float = 0.5):
    try:
        await page.evaluate("""(() => {
            const el = document.getElementById('fade-overlay');
            if (el) { el.style.transition = 'opacity 0.5s ease'; el.style.opacity = '1'; }
        })()""")
    except Exception:
        pass
    await wall_sleep(dur)


async def fade_in(page, dur: float = 0.5):
    try:
        await page.evaluate("""(() => {
            const el = document.getElementById('fade-overlay');
            if (el) { el.style.transition = 'opacity 0.5s ease'; el.style.opacity = '0'; }
        })()""")
    except Exception:
        pass
    await wall_sleep(dur)


async def navigate(page, url: str):
    """Navigate with fade transition."""
    await fade_out(page, 0.5)
    await page.goto(url, wait_until="networkidle", timeout=45000)
    await setup_page(page)
    await wall_sleep(0.3)
    await fade_in(page, 0.5)


async def record():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                f"--window-size={WIDTH},{HEIGHT}",
                "--disable-gpu",
                "--hide-scrollbars",
                "--force-dark-mode",
            ],
        )

        context = await browser.new_context(
            viewport={"width": WIDTH, "height": HEIGHT},
            record_video_dir=str(VIDEO_DIR / "_tmp_video"),
            record_video_size={"width": WIDTH, "height": HEIGHT},
            device_scale_factor=1,
            color_scheme="dark",
        )

        page = await context.new_page()

        # ============================================================
        # SCENE 1: THE HOOK  (0:00 - 0:17)
        # Landing page hero, scroll to comparison table
        # ============================================================
        log(f"[Scene 1/5] The Hook ({SCENE_DURATIONS['hook']}s)")

        await page.goto(SITE, wait_until="networkidle", timeout=45000)
        await setup_page(page)

        # Hold on hero for 3s
        await wall_sleep(3.0)

        # Gentle scroll down to show trust strip + product showcase
        await smooth_scroll(page, 600, duration_s=3.0)
        await wall_sleep(1.5)

        # Scroll to the comparison table
        await scroll_to_text(page, "Why Not Hootsuite", offset=-150, duration_s=3.5)
        await wall_sleep(3.5)

        # Slowly scroll past the table rows
        cur = await page.evaluate("window.scrollY")
        await smooth_scroll(page, cur + 400, duration_s=2.0)
        await wall_sleep(0.8)

        # ============================================================
        # SCENE 2: THE COMMAND  (0:17 - 0:32)
        # /demo page, click "Try an example prompt", watch pipeline
        # ============================================================
        log(f"[Scene 2/5] The Command ({SCENE_DURATIONS['command']}s)")

        await navigate(page, f"{SITE}/demo")
        await wall_sleep(1.5)

        # Scroll to Step 1 heading, keep it near top
        await scroll_to_text(page, "AI Content Generation", offset=-80, duration_s=1.5)
        await wall_sleep(1.0)

        # Click the prompt button
        try:
            btn = page.get_by_role("button", name="Try an example prompt")
            await btn.scroll_into_view_if_needed(timeout=3000)
            await wall_sleep(0.5)
            await btn.click(timeout=3000)
        except Exception:
            log("  (prompt button not found, continuing)")

        # Typing animation takes ~2.2s, then pipeline auto-scrolls
        # and steps animate over ~3.4s more. Wait for all of it.
        await wall_sleep(3.0)

        # Scroll down to see the pipeline panel with Drafting/Reviewing/Optimizing
        try:
            panel = page.locator("#demo-step-1-panel")
            await panel.scroll_into_view_if_needed(timeout=3000)
        except Exception:
            cur = await page.evaluate("window.scrollY")
            await smooth_scroll(page, cur + 400, duration_s=1.5)

        # Wait for pipeline steps to finish animating
        await wall_sleep(4.5)

        # ============================================================
        # SCENE 3: COMPLIANCE + CROSS-PLATFORM  (0:32 - 0:57)
        # Scroll to compliance checklist, then cross-platform
        # ============================================================
        log(f"[Scene 3/5] Compliance & Cross-Platform ({SCENE_DURATIONS['compliance']}s)")

        # Scroll to "Compliance Validation" - this triggers the animation (once, on in-view)
        await scroll_to_text(page, "Compliance Validation", offset=-80, duration_s=2.5)

        # Checklist animates over ~3.1s after coming into view
        # Plus IP scan takes ~2.4s. Hold for full animation.
        await wall_sleep(5.0)

        # Scroll down a bit to see the full checklist results
        cur = await page.evaluate("window.scrollY")
        await smooth_scroll(page, cur + 250, duration_s=1.5)
        await wall_sleep(3.0)

        # Scroll to "Cross-Platform Publishing"
        # This triggers platform activation animation (~3.8s total)
        await scroll_to_text(page, "Cross-Platform Publishing", offset=-80, duration_s=2.5)
        await wall_sleep(5.0)

        # Scroll a bit to see all 6 platforms activated
        cur = await page.evaluate("window.scrollY")
        await smooth_scroll(page, cur + 200, duration_s=1.5)
        await wall_sleep(3.0)

        # ============================================================
        # SCENE 4: DASHBOARD & GUARDRAILS  (0:57 - 1:14)
        # Scroll to Live Dashboard, hover kill switch + spend caps
        # ============================================================
        log(f"[Scene 4/5] Dashboard & Guardrails ({SCENE_DURATIONS['dashboard']}s)")

        # Scroll to "Live Dashboard" heading
        await scroll_to_text(page, "Live Dashboard", offset=-80, duration_s=2.5)
        await wall_sleep(2.5)

        # The BrowserMockup animates in with ~0.5s delay + 0.9s duration
        # Chart bars animate at 0.8 + i*0.06s, agent list at 1.2 + i*0.08s
        # Scroll into the mockup to see the full dashboard
        cur = await page.evaluate("window.scrollY")
        await smooth_scroll(page, cur + 350, duration_s=2.0)
        await wall_sleep(2.0)

        # Hover over the kill switch button
        try:
            kill = page.get_by_text("EMERGENCY KILL SWITCH").first
            await kill.scroll_into_view_if_needed(timeout=3000)
            await wall_sleep(0.5)
            await kill.hover(timeout=3000)
        except Exception:
            log("  (kill switch not found)")
        await wall_sleep(3.0)

        # Hover over spend metric
        try:
            spend = page.get_by_text("Monthly Spend").first
            await spend.hover(timeout=3000)
        except Exception:
            pass
        await wall_sleep(3.0)

        # ============================================================
        # SCENE 5: CTA CLOSE  (1:14 - 1:26)
        # Back to home, highlight "Start Free Trial"
        # ============================================================
        log(f"[Scene 5/5] CTA Close ({SCENE_DURATIONS['cta']}s)")

        await navigate(page, SITE)
        await wall_sleep(2.5)

        # Hover over the hero CTA
        try:
            cta = page.get_by_role("link", name="Start Free Trial").first
            await cta.hover(timeout=4000)
        except Exception:
            pass
        await wall_sleep(3.5)

        # Hold on the hero with CTA highlighted
        await wall_sleep(3.0)

        # Gentle fade to black for ending
        await fade_out(page, 1.5)
        await wall_sleep(1.0)

        # === END RECORDING ===
        log("Recording complete, closing browser...")
        await context.close()
        await browser.close()

        # Move video file
        tmp_dir = VIDEO_DIR / "_tmp_video"
        vids = list(tmp_dir.glob("*.webm"))
        if vids:
            if RAW_VIDEO.exists():
                RAW_VIDEO.unlink()
            vids[0].rename(RAW_VIDEO)
            log(f"Raw video: {RAW_VIDEO} ({RAW_VIDEO.stat().st_size / 1048576:.1f} MB)")
        else:
            log("ERROR: No video file!")
            return False

        try:
            tmp_dir.rmdir()
        except Exception:
            pass

        return True


def stabilize_video():
    """Re-encode at constant 30fps for smooth playback."""
    log("Stabilizing (constant 30fps, high-quality encode)...")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(RAW_VIDEO),
        "-vf", f"fps=30,scale={WIDTH}:{HEIGHT}:flags=lanczos",
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-an",
        "-movflags", "+faststart",
        str(STABILIZED),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        log(f"Error:\n{r.stderr[-500:]}")
        return False
    log(f"Stabilized: {STABILIZED.stat().st_size / 1048576:.1f} MB")
    return True


def merge_audio():
    """Merge stabilized video with narration, trimmed to shorter stream."""
    if not NARRATION.exists():
        log(f"ERROR: {NARRATION} missing")
        return False
    log("Merging narration audio...")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(STABILIZED),
        "-i", str(NARRATION),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(FINAL_OUTPUT),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        log(f"Error:\n{r.stderr[-500:]}")
        return False

    size = FINAL_OUTPUT.stat().st_size / 1048576
    dur = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(FINAL_OUTPUT)],
        capture_output=True, text=True,
    ).stdout.strip()
    log(f"DONE: {FINAL_OUTPUT}")
    log(f"  Size: {size:.1f} MB | Duration: {dur}s")
    return True


async def main():
    log("=" * 60)
    log("OrchestraAI Demo Video Generator v4")
    log(f"  {WIDTH}x{HEIGHT} | ~{sum(SCENE_DURATIONS.values()):.0f}s target")
    log("=" * 60)

    log("\n[1/3] Recording browser session...")
    if not await record():
        return

    log("\n[2/3] Stabilizing framerate...")
    if not stabilize_video():
        return

    log("\n[3/3] Merging narration...")
    if not merge_audio():
        return

    for f in [STABILIZED, RAW_VIDEO]:
        try:
            f.unlink()
        except Exception:
            pass

    log("\n" + "=" * 60)
    log(f"Video ready: {FINAL_OUTPUT}")
    log("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
