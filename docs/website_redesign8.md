# 🚀 Orchestra — Hybrid 2D/3D Optimized Interactive Demo Prompt

## 🎯 Objective

Upgrade the website to **top-tier SaaS interactive experience** by:

* Delivering **3D pipeline visualizations** on desktop
* Maintaining **fast-loading, responsive experience on all devices**
* Providing **2D fallback on mobile/low-performance devices**
* Implementing **lazy-load strategies** for 3D components
* Preserving brand identity (glow, gradients, premium UI)

---

# 🧠 CORE CONCEPT

* Desktop: Full 3D interactive pipeline demo
* Mobile / Low-performance: Simplified 2D visualization or static preview
* Lazy-load 3D scene **after key hero content is visible**
* Use Three.js + React Three Fiber for 3D, SVG / Canvas for 2D fallback
* Keep motion, glow, and pulse consistent across both modes

---

# 🧩 INTERACTIVE ELEMENTS

1. **3D Graph Canvas (Desktop)**

   * Nodes in 3D space with depth, pulse, and glow
   * Edges with animated particle flow
   * Interactive orbit controls (rotate, zoom, pan)

2. **2D Fallback (Mobile / Low-Perf)**

   * Flat DAG layout using Canvas or SVG
   * Animated edges simplified (line + glow)
   * Touch-friendly interactions

3. **Inspector Panels**

   * Slide-in panel for node details (logs, status)
   * Motion and glassmorphism consistent across 2D/3D

---

# ⚡ PERFORMANCE STRATEGIES

1. **Lazy Load 3D**

   * Load 3D component only after hero text + CTA visible
   * Use skeleton / placeholder for faster LCP

2. **Conditional Rendering**

   * Detect device performance / screen size
   * Render 3D on desktop
   * Render 2D fallback on mobile

3. **Optimize Geometry**

   * Instanced nodes for large graphs
   * Minimize polygons and particle count

4. **Throttle Animations**

   * Limit FPS on mobile
   * Smooth particle flow without frame drops

5. **Asset Optimization**

   * Compress textures
   * Use vector-based edges where possible

---

# 🎬 FRAMER MOTION SPEC

### Node Pulse

```jsx id="pulse1"
<motion.mesh
  animate={{ scale: [1, 1.05, 1] }}
  transition={{ repeat: Infinity, duration: 2 }}
/>
```

### Edge Flow (Desktop)

```jsx id="edge1"
<motion.line
  animate={{ dashOffset: [0, 100] }}
  transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
/>
```

### 2D Fallback Animation (Mobile)

```jsx id="edge2"
<motion.div
  animate={{ opacity: [0.5, 1, 0.5] }}
  transition={{ repeat: Infinity, duration: 2 }}
/>
```

---

# 🧱 COMPONENT ARCHITECTURE

```id="structure1"
/components
  HeroHybrid.tsx        // Hero with 3D/2D conditional demo
  GraphCanvas3D.tsx     // Desktop 3D canvas
  GraphCanvas2D.tsx     // Mobile / low-perf 2D fallback
  Node.tsx              // Node component (shared logic)
  Edge.tsx              // Edge component (shared logic)
  InspectorPanel.tsx    // Node details
  LogsViewer.tsx        // Optional streaming logs
```

---

# 🔵 UX INTERACTIONS

* Hover nodes → glow + tooltip
* Click → inspector panel with smooth slide/fade
* Scroll-triggered section reveals
* Camera: orbit + zoom (desktop only)
* Touch gestures (mobile 2D fallback)

---

# 🎨 VISUAL IDENTITY

* Maintain **brand glow + gradient system**
* Glow states consistent across 2D/3D nodes:

  * Running: Indigo
  * Success: Green
  * Failed: Red
* Glassmorphism for inspector and panels

---

# 📱 RESPONSIVE STRATEGY

* Detect viewport/device
* Desktop: Full 3D pipeline demo
* Mobile / low-perf: Simplified 2D DAG + touch interactions
* Lazy-load heavy 3D scene **only on capable devices**

---

# ⚡ PERFORMANCE & SECURITY

* Lazy load 3D scene after hero content
* Optimize meshes and particle count
* Client-only mock state for inspector
* Secure CSP headers, no exposed API keys
* Reduce JS bundle size, optimize images

---

# 🏁 SUCCESS CRITERIA

* Desktop: rich 3D pipeline demo
* Mobile: fast, responsive 2D fallback
* Hero section captures attention
* Interactive nodes and edges
* Premium, memorable visual identity
* Smooth motion and high FPS
* Fully secure and deploy-ready

---

# 🚀 IMPLEMENTATION STEPS

1. Build `GraphCanvas3D` with optimized geometry + particle flow
2. Build `GraphCanvas2D` fallback for mobile
3. Conditional rendering based on device/performance
4. Lazy-load 3D after hero visible
5. Implement Node + Edge interactions for both 3D/2D
6. Integrate Inspector panel with glassmorphism + animation
7. Apply brand glow + gradient system
8. Test performance and responsiveness across devices

---

## 👉 START NOW

Cursor AI should:

1. Implement hybrid 3D/2D interactive demo
2. Optimize for desktop and mobile
3. Apply motion, glow, and pulse consistently
4. Lazy-load 3D scene
5. Deliver **production-ready React + Tailwind + Framer Motion code**

---

If ready, next step can be:

* Generate **full working hybrid 3D/2D Next.js demo repo**, deployable, with advanced animations and responsive fallback baked in.
