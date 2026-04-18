# Addendum: Landing Page Conversion Optimization

## Objective
Act as a Principal UX Engineer and Conversion Rate Optimization (CRO) expert. Please review our main landing page components (likely `frontend/src/app/page.tsx` and associated UI components) and implement the following design and copy upgrades to maximize our conversion rate for Enterprise Agency clients.

## Execution Steps

### 1. Upgrade Social Proof & Testimonials
- Locate the Testimonials section. 
- Replace the generic attributions ("Marketing Director", "Agency Principal") with structured placeholder components that include:
  - A circular avatar image placeholder.
  - A specific name (e.g., "Sarah Jenkins").
  - A specific company name and placeholder logo (e.g., "Acme Digital").
  - Make the quotes highly specific to metrics: *"OrchestraAI's LangGraph engine replaced 5 tools and dropped our Meta CPA by 34% in week one."*

### 2. Embed the Product Demo 
- Locate the "How It Works" section.
- Instead of just a "Watch Demo" button that links out, build a beautifully styled, responsive Video Embed component right on the page.
- Add a subtle glass-morphism frame around it and an interactive play button. (Use a placeholder MP4 or iframe for now).
- The section should visually scream: "See the AI pause a bleeding campaign in 90 seconds."

### 3. Inject "Guardrailed Trial" Microcopy
- Seedance 2.0 and open-source LLM inference are expensive. We need to prevent trial abuse.
- Underneath every "Start Free Trial" CTA (in the Hero and Footer), add small, muted, trust-building microcopy:
  - `<p className="text-sm text-gray-500">14-Day Trial • Includes $50 in AI Video Credits • No Credit Card Required</p>`

### 4. Add "Enterprise Trust" Badges
- Just below the Hero section (or above the comparison table), add a "Powered By & Secured By" logo strip.
- Include subtle, greyscale icons/text for: "Stripe Verified", "SOC-2 Ready Architecture", "Meta Ads API", "ByteDance Seedance 2.0", and "Llama 3". 
- This visually signals to Enterprise buyers that our stack is industry-standard.

### 5. Sticky Navigation CTA
- Ensure the main Navbar is sticky (`fixed top-0 z-50` with a subtle backdrop blur).
- The "Get Started" button in the navbar must remain visible at all times as the user scrolls down the page, ensuring the checkout funnel is never more than one click away.

## Instructions for Cursor:
Please scan the `frontend/` directory, locate the relevant landing page files, and implement these 5 upgrades using Next.js best practices, Tailwind CSS, and Framer Motion (if already installed for subtle animations).
