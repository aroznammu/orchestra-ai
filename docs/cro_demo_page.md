# Addendum: /Demo Page Interactive Upgrades

## Objective
Act as a Principal UX/UI Engineer. Review the `frontend/src/app/demo/page.tsx` (or equivalent demo page file). We need to upgrade the static 4-step walkthrough into a highly interactive experience that highlights our newly added Seedance 2.0 video capabilities and strict financial guardrails.

## Execution Steps

### 1. The "Trigger" Interaction (Hero Section)
- The hero section currently says "Waiting for command...". 
- Create a mock "Chat Input" component at the top of the walkthrough. 
- Add a button labeled "Try an Example Prompt". When clicked, use a typing effect (e.g., Framer Motion or a React `useEffect` interval) to type out: *"Generate a 10-second video ad for our Summer Sale, allocate $500, and publish to TikTok and Instagram."*
- When the typing finishes, make the UI "scroll down" to Step 1 automatically to simulate the pipeline kicking off.

### 2. Inject Seedance 2.0 into Step 1
- Step 1 currently only mentions text copy ("Drafting, Reviewing, Optimizing").
- Add a new visual state for **"🎬 Video Generation (Seedance 2.0)"**.
- Render a skeleton loader that transitions into a placeholder HTML5 `<video>` player to prove the platform generates rich media, not just text.

### 3. Highlight the "Visual Compliance Gate" in Step 2
- Step 2 lists 6 compliance gates. This is great, but we need to emphasize our biggest moat.
- Add a visually distinct UI element for the **"Visual IP Compliance Scan."** - Create a mock UI animation showing video frames being scanned for "Celebrity Likeness" and "Copyrighted Logos" with green "Safe" checkmarks appearing next to them.

### 4. Inject the "Kill Switch" into Step 4 (Dashboard)
- Step 4 shows a great dashboard mockup, but we need to emphasize the *financial safety* value prop.
- Add a prominent, red **"EMERGENCY KILL SWITCH: HALT ALL SPEND"** button to the dashboard UI mockup. 
- Add a visual badge next to the ROI metrics that says "⚡ Autonomous Budget Reallocation Active".

### 5. Add the "Watch the Video" Fallback
- At the very bottom of the page, above the final CTA, add a section for users who don't want to scroll through the interactive UI.
- Add an embedded video player component (placeholder for a Loom iframe) with the headline: *"Rather just watch? See OrchestraAI in action in 90 seconds."*

## Instructions for Cursor:
Please scan the demo page code and implement these 5 interactive upgrades using Next.js, Tailwind CSS, and Framer Motion. Ensure the interactive typing effect in Step 1 feels snappy and responsive.
