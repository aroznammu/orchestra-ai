# 🎨 Orchestra — Pixel-Perfect UI Spec (Figma-Level)

## 🎯 Objective

Design a **visually elite, production-grade SaaS website UI** with:

* Pixel-perfect spacing
* Consistent typography system
* Modern visual depth
* High-end SaaS aesthetics (Stripe / Linear quality)

---

# 🧱 1. GLOBAL DESIGN SYSTEM

---

## 🧭 Layout Grid

* Max width: **1280px**
* Content width: **1200px**
* Grid: **12 columns**
* Column gap: **24px**
* Section padding: **py-24 (96px vertical)**

---

## 📐 Spacing Scale

Use strict spacing tokens:

* 4px, 8px, 12px, 16px
* 24px, 32px, 48px
* 64px, 80px, 96px, 120px

👉 No arbitrary spacing allowed

---

## 🎨 Color System

### Background

* Primary: `#0B0B0F`
* Secondary: `#111117`
* Card: `rgba(255,255,255,0.04)`

---

### Text

* Primary: `#FFFFFF`
* Secondary: `#A1A1AA`
* Muted: `#71717A`

---

### Accent Gradient

* Start: `#4F46E5` (Indigo)
* End: `#7C3AED` (Purple)

---

## 🔤 Typography

### Font

* Primary: Inter / Geist / SF Pro

---

### Scale

| Element | Size | Weight | Line Height |
| ------- | ---- | ------ | ----------- |
| H1      | 64px | 700    | 1.1         |
| H2      | 40px | 600    | 1.2         |
| H3      | 28px | 600    | 1.3         |
| Body    | 16px | 400    | 1.6         |
| Small   | 14px | 400    | 1.5         |

---

## 🧩 Components

### Buttons

Primary:

* Background: gradient
* Padding: `px-6 py-3`
* Radius: `rounded-xl`
* Shadow: `shadow-lg`
* Hover: glow + scale (1.03)

Secondary:

* Border: `border-white/20`
* Background: transparent

---

### Cards

* Background: `white/5`
* Border: `white/10`
* Radius: `rounded-2xl`
* Padding: `p-6`
* Blur: `backdrop-blur`

---

---

# 🟣 2. HERO SECTION

---

## 📐 Layout

* Height: **90vh**
* Center aligned (vertical + horizontal)
* Two-column grid (desktop)
* Stack (mobile)

---

## ✍️ Content

### Headline

AI-Native Data Orchestration for Modern Teams

---

### Subheadline

Build, run, and scale data pipelines without managing infrastructure. Faster, smarter, and production-ready.

---

## 🎯 CTA Layout

* Horizontal row
* Gap: `16px`

---

## 🎨 Background

* Gradient overlay
* Subtle radial glow behind product image

---

## 🖼️ Visual

* Product UI screenshot
* Width: 60% container
* Shadow: `shadow-2xl`

---

---

# 🔵 3. SOCIAL PROOF

---

## Layout

* Horizontal scroll (mobile)
* Centered row (desktop)

---

## Elements

* Logos: grayscale → color on hover
* Text: “Trusted by modern data teams”

---

---

# 🔴 4. PROBLEM SECTION

---

## Layout

* 3-column grid (desktop)
* Stack (mobile)

---

## Cards

Each card:

* Icon (top)
* Title
* Description

---

## Spacing

* Gap: `32px`
* Section padding: `py-24`

---

---

# 🟢 5. SOLUTION SECTION

---

## Layout

* Alternating rows (image left/right)

---

## Content

* Title
* 3–4 bullet points
* Supporting visual

---

---

# 🟡 6. PRODUCT SHOWCASE

---

## Layout

* Full-width container
* Centered image

---

## Behavior

* Hover: slight zoom (1.02)
* Fade-in animation

---

## Container

* Glassmorphism card
* Padding: `p-8`

---

---

# 🧠 7. HOW IT WORKS

---

## Layout

* Horizontal stepper

---

## Steps

1. Define
2. Orchestrate
3. Monitor
4. Scale

---

## UI

* Icon + label
* Connecting line

---

---

# 🟣 8. COMPARISON TABLE

---

## Layout

* Table with 3 columns

---

## Styling

* Borders: subtle (`white/10`)
* Highlight Orchestra column

---

---

# 🔵 9. DEVELOPER SECTION

---

## Layout

* Split screen

---

## Left

* Code snippet

---

## Right

* Text + CTA

---

---

# 🟢 10. TESTIMONIALS

---

## Layout

* Carousel or 3-column grid

---

## Cards

* Quote
* Name
* Role

---

---

# 🟠 11. FINAL CTA

---

## Layout

* Centered

---

## Background

* Strong gradient
* Glow effect

---

## CTA

* Large primary button

---

---

# ⚡ ANIMATIONS

---

## Use Framer Motion

* Fade-in (opacity + y)
* Hover scale
* Smooth transitions (0.3s)

---

---

# 📱 MOBILE SPEC

---

## Rules

* Stack all grids
* Reduce padding to `py-16`
* Full-width buttons
* Larger touch targets

---

---

# 🔐 SECURITY UI NOTES

---

* Avoid inline scripts
* Sanitize user inputs
* Secure form fields
* No exposed API keys in frontend

---

---

# ⚡ PERFORMANCE UI NOTES

---

* Use optimized images (WebP)
* Lazy loading
* Minimal JS

---

---

# 🏁 FINAL DESIGN PRINCIPLES

---

## Must Feel:

* Minimal
* Confident
* Technical
* Premium

---

## Avoid:

* Clutter
* Over-animation
* Inconsistent spacing

---

---

# 🚀 IMPLEMENTATION CHECKLIST

---

1. Apply grid system
2. Implement typography scale
3. Build reusable components
4. Add animations
5. Ensure responsiveness
6. Optimize performance
7. Validate spacing consistency

---

---

# 🎯 FINAL GOAL

---

A website that feels like:

* Stripe
* Linear
* Vercel

But uniquely **Orchestra**

---

## 👉 START IMPLEMENTATION

Focus first on:

1. Hero section
2. Design system
3. Product showcase
