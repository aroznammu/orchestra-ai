export interface PipelineNodeData {
  id: string;
  label: string;
  description: string;
  x: number;
  y: number;
  z: number;
  status: "idle" | "running" | "success" | "failed";
  duration?: string;
  logs: string[];
}

export type NodeStatus = PipelineNodeData["status"];

export const INITIAL_NODES: PipelineNodeData[] = [
  { id: "classify", label: "Classify", description: "LLM intent classification with fallback chain", x: 5, y: 30, z: 0, status: "idle", duration: "12ms", logs: ["Received user prompt", "Routing to OpenAI gpt-4o-mini", "Intent: campaign_launch", "Depth: deep, Agent: orchestrator"] },
  { id: "compliance", label: "Compliance", description: "Pre-action regulatory and budget checks", x: 18, y: 65, z: 0.4, status: "idle", duration: "8ms", logs: ["Checking prohibited content rules", "Budget validation: $500 within daily cap", "Targeting rules: compliant", "All compliance gates passed ✓"] },
  { id: "content", label: "Content", description: "Multi-provider LLM content generation", x: 31, y: 25, z: -0.3, status: "idle", duration: "340ms", logs: ["Generating ad copy for Instagram", "Generating ad copy for TikTok", "Adapting tone for each platform", "Content generated: 2 variants per platform"] },
  { id: "video", label: "Video", description: "Seedance 2.0 text-to-video generation", x: 44, y: 70, z: 0.5, status: "idle", duration: "1.2s", logs: ["Initializing Seedance 2.0 via fal.ai", "Generating 5s clip from prompt", "Resolution: 720p, Cost: $0.26", "Video generated successfully"] },
  { id: "vision", label: "Vision Gate", description: "GPT-4o Vision IP compliance scanning", x: 57, y: 30, z: -0.2, status: "idle", duration: "420ms", logs: ["Extracting keyframes (5 frames)", "Scanning for celebrity likenesses", "Scanning for copyrighted content", "Scanning for trademarked logos", "All frames cleared ✓"] },
  { id: "policy", label: "Policy", description: "Platform-specific rules enforcement", x: 70, y: 65, z: 0.3, status: "idle", duration: "15ms", logs: ["Instagram: character limit OK", "Instagram: hashtag count OK", "TikTok: video duration OK", "TikTok: music policy compliant"] },
  { id: "publish", label: "Publish", description: "Multi-platform dispatch with retry", x: 83, y: 25, z: -0.4, status: "idle", duration: "890ms", logs: ["Publishing to Instagram...", "Instagram: POST 201 Created", "Publishing to TikTok...", "TikTok: POST 201 Created", "2/2 platforms published ✓"] },
  { id: "analytics", label: "Analytics", description: "Cross-platform metrics collection", x: 92, y: 60, z: 0.2, status: "idle", duration: "45ms", logs: ["Collecting baseline metrics", "Registering campaign for tracking", "Setting up ROI normalization", "Analytics pipeline active"] },
];

export const EDGES: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7],
];

export const STATUS_COLORS = {
  idle: { bg: "bg-zinc-800/80", border: "border-zinc-700/60", text: "text-zinc-500" },
  running: { bg: "bg-indigo-950/80", border: "border-indigo-500/50", text: "text-indigo-300" },
  success: { bg: "bg-emerald-950/60", border: "border-emerald-500/40", text: "text-emerald-400" },
  failed: { bg: "bg-red-950/60", border: "border-red-500/40", text: "text-red-400" },
};

export const GLOW_SHADOWS: Record<NodeStatus, string> = {
  idle: "none",
  running: "0 0 20px rgba(79,70,229,0.4), 0 0 40px rgba(79,70,229,0.15)",
  success: "0 0 16px rgba(16,185,129,0.3)",
  failed: "0 0 16px rgba(239,68,68,0.3)",
};

export const STATUS_HEX: Record<NodeStatus, string> = {
  idle: "#71717a",
  running: "#818cf8",
  success: "#34d399",
  failed: "#f87171",
};

export const STATUS_EMISSIVE: Record<NodeStatus, string> = {
  idle: "#27272a",
  running: "#4f46e5",
  success: "#059669",
  failed: "#dc2626",
};
