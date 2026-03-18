import {
  BrainCircuit,
  Video,
  ShieldCheck,
  BarChart3,
  Eye,
  Database,
  Globe,
  Lock,
  Users,
  Search,
  Zap,
  type LucideIcon,
} from "lucide-react";

/* ------------------------------------------------------------------ */
/*  Navigation                                                         */
/* ------------------------------------------------------------------ */

export const NAV_ITEMS = [
  { href: "/features", label: "Features" },
  { href: "/pricing", label: "Pricing" },
  { href: "/security", label: "Security" },
  { href: "/faq", label: "FAQ" },
  { href: "/contact", label: "Contact" },
] as const;

export const DASHBOARD_URL = "https://useorchestra.dev";
export const SUPPORT_EMAIL = "support@useorchestra.dev";

/* ------------------------------------------------------------------ */
/*  Platforms                                                           */
/* ------------------------------------------------------------------ */

export const PLATFORMS = [
  "Twitter / X",
  "YouTube",
  "TikTok",
  "Pinterest",
  "Facebook",
  "Instagram",
  "LinkedIn",
  "Snapchat",
  "Google Ads",
] as const;

/* ------------------------------------------------------------------ */
/*  Stats (landing page counters)                                      */
/* ------------------------------------------------------------------ */

export interface Stat {
  value: number;
  suffix?: string;
  prefix?: string;
  label: string;
}

export const STATS: Stat[] = [
  { value: 9, label: "Platforms Connected" },
  { value: 10, label: "AI Agent Nodes" },
  { value: 3, label: "Tier Financial Protection", suffix: "-Tier" },
  { value: 0.26, prefix: "$", label: "Per AI Video", suffix: "" },
];

/* ------------------------------------------------------------------ */
/*  Feature highlights (landing page)                                  */
/* ------------------------------------------------------------------ */

export interface FeatureHighlight {
  icon: LucideIcon;
  title: string;
  description: string;
}

export const FEATURE_HIGHLIGHTS: FeatureHighlight[] = [
  {
    icon: BrainCircuit,
    title: "AI Agent Orchestration",
    description:
      "10-node LangGraph agent handles intent classification, compliance, content generation, publishing, and optimization in a single request.",
  },
  {
    icon: Video,
    title: "AI Video Generation",
    description:
      "Generate marketing videos from text or images via Seedance 2.0 at just $0.26 per 5-second clip with automatic IP compliance scanning.",
  },
  {
    icon: ShieldCheck,
    title: "Financial Guardrails",
    description:
      "3-phase bidding progression with 3-tier spend caps, statistical anomaly detection, and a one-click kill switch to halt all spend.",
  },
  {
    icon: BarChart3,
    title: "Cross-Platform Intelligence",
    description:
      "Normalized ROI across all 9 platforms, marginal return analysis, budget allocation optimization, and saturation detection.",
  },
  {
    icon: Eye,
    title: "Visual Compliance Gate",
    description:
      "GPT-4o Vision scans every AI-generated video frame for celebrity likenesses, copyrighted characters, and trademarked logos.",
  },
  {
    icon: Database,
    title: "Data Moat Engine",
    description:
      "Every campaign compounds your performance intelligence. Your data moat grows over time — competitors can't copy your advantage.",
  },
];

/* ------------------------------------------------------------------ */
/*  Features page (detailed)                                           */
/* ------------------------------------------------------------------ */

export interface FeatureDetail {
  id: string;
  icon: LucideIcon;
  title: string;
  subtitle: string;
  description: string;
  bullets: string[];
}

export const FEATURES_DETAILED: FeatureDetail[] = [
  {
    id: "orchestration",
    icon: BrainCircuit,
    title: "AI Agent Orchestration",
    subtitle: "10-Node LangGraph Multi-Agent System",
    description:
      "A single natural-language command triggers a sophisticated 10-node agent graph that classifies intent, checks compliance, generates content, creates video, validates IP, enforces platform rules, publishes, collects analytics, optimizes performance, and responds — all automatically.",
    bullets: [
      "Classify — LLM intent classification with OpenAI → Anthropic → Ollama fallback",
      "Compliance Gate — Pre-action checks for prohibited content, targeting rules, budget limits",
      "Content Agent — Multi-provider LLM content generation with automatic fallback",
      "Video Node — AI video via Seedance 2.0 (text-to-video & image-to-video)",
      "Visual Compliance Gate — Keyframe extraction + GPT-4o Vision IP scanning",
      "Policy Node — Platform-specific rules (character limits, hashtags, media constraints)",
      "Platform Node — Publish/schedule dispatch to all 9 platform connectors",
      "Analytics Node — Cross-platform metrics aggregation and benchmarking",
      "Optimize Node — Thompson Sampling, UCB, and Bayesian budget allocation",
      "Respond — Final response assembly and execution trace cleanup",
    ],
  },
  {
    id: "video",
    icon: Video,
    title: "AI Video Pipeline",
    subtitle: "Text-to-Video and Image-to-Video with IP Scanning",
    description:
      "Generate marketing video ads from natural language descriptions or reference images. Every frame is scanned for intellectual property violations before delivery.",
    bullets: [
      "Seedance 2.0 via fal.ai — ~$0.26 per 5-second 720p clip",
      "Text-to-video and image-to-video generation modes",
      "Visual Compliance Gate with GPT-4o Vision keyframe analysis",
      "Automatic detection of celebrity likenesses, copyrighted characters, trademarked logos",
      "Safe videos delivered in HTML5 player; flagged content blocked with violation details",
      "Per-tenant audit logging of all scan results",
    ],
  },
  {
    id: "guardrails",
    icon: ShieldCheck,
    title: "Financial Guardrails",
    subtitle: "3-Phase Bidding with 3-Tier Risk Containment",
    description:
      "Your AI earns autonomy over time through a phased progression system. Combined with multi-tier spend caps, anomaly detection, and an emergency kill switch, your budget is always protected.",
    bullets: [
      "Hard Guardrail Phase — Every bid requires explicit human approval",
      "Semi-Autonomous Phase — AI executes within bounds, exceptions reviewed by humans",
      "Controlled Autonomous Phase — Full AI control within strict limits, monitoring only",
      "3-tier spend caps — Daily, weekly, and monthly limits that AI cannot override",
      "Statistical anomaly detection — Z-score and IQR-based flagging of unusual spend",
      "Kill Switch — Halt all spend across all platforms with a single click",
    ],
  },
  {
    id: "intelligence",
    icon: BarChart3,
    title: "Cross-Platform Intelligence",
    subtitle: "Normalized ROI and Intelligent Budget Allocation",
    description:
      "Compare apples to apples across all 9 platforms with normalized metrics. The optimization engine uses marginal return curves to allocate budget where it delivers the most impact.",
    bullets: [
      "ROI normalization — Comparable returns across every platform",
      "Marginal return analysis — Budget allocated to highest-impact channels",
      "Attribution modeling — Credit allocation across platform touchpoints",
      "Saturation detection — Flags diminishing returns automatically",
      "Intelligent budget reallocation — Dynamic redistribution based on performance",
    ],
  },
  {
    id: "data-moat",
    icon: Database,
    title: "Data Moat Engine",
    subtitle: "Compounding Performance Intelligence",
    description:
      "Every campaign you run makes OrchestraAI smarter for your business. Your performance data compounds into a proprietary competitive advantage that grows over time.",
    bullets: [
      "Campaign → Engagement → Normalize → Embed → Model update flywheel",
      "Per-platform engagement signal normalization",
      "Content + performance embedding for retrieval",
      "Tenant-specific model that improves with every campaign",
      "Maturity progression: cold_start → warming → learning → maturing → optimized",
    ],
  },
  {
    id: "connectors",
    icon: Globe,
    title: "9 Platform Connectors",
    subtitle: "Publish, Analyze, and Target Across Every Major Platform",
    description:
      "Connect all nine major advertising and social media platforms with OAuth2 authentication, automatic retry with exponential backoff, rate-limit handling, and Fernet-encrypted token storage.",
    bullets: [
      "Twitter/X v2 — Publish, analytics, audience targeting",
      "YouTube v3 — Video publishing, analytics, audience management",
      "TikTok v2 — Short-form video, analytics, audience targeting",
      "Pinterest v5 — Pin publishing, analytics, audience insights",
      "Facebook Graph v19 — Posts, ads, analytics, audiences",
      "Instagram Graph v19 — Stories, reels, analytics, audiences",
      "LinkedIn v2 — Professional content, analytics, targeting",
      "Snapchat Marketing v1 — Snap ads, analytics, audience reach",
      "Google Ads v16 — Search, display, video ads, full analytics",
    ],
  },
  {
    id: "rbac",
    icon: Users,
    title: "RBAC & Multi-Tenancy",
    subtitle: "4-Role Hierarchy with 26 Granular Permissions",
    description:
      "Enterprise-grade access control with complete tenant isolation. Every query is scoped to the tenant, every action is permission-checked, and every operation is audit-logged.",
    bullets: [
      "4-tier role hierarchy: Owner → Admin → Member → Viewer",
      "26 granular permissions across campaigns, platforms, analytics, budget, and more",
      "Query-level tenant isolation — no cross-tenant data access possible",
      "Qdrant vector collections namespaced per tenant",
      "Complete audit trail of all operations with user attribution",
    ],
  },
  {
    id: "rag",
    icon: Search,
    title: "RAG Memory",
    subtitle: "Campaign Memory with Performance-Weighted Retrieval",
    description:
      "OrchestraAI remembers your campaigns, content, and decisions using vector search. Past performance is factored into every recommendation, so the system learns what works for your brand.",
    bullets: [
      "Qdrant vector database for campaign and content embeddings",
      "OpenAI text-embedding-3-small → Ollama nomic-embed-text → hash fallback",
      "Campaign memory — index campaigns, content templates, and AI decisions",
      "Performance-weighted retrieval — successful campaigns rank higher",
      "Metric updates — embeddings refresh as campaign performance evolves",
    ],
  },
];

/* ------------------------------------------------------------------ */
/*  Pricing                                                            */
/* ------------------------------------------------------------------ */

export interface PricingTier {
  name: string;
  price: number;
  period: string;
  description: string;
  features: string[];
  cta: string;
  popular?: boolean;
}

export const PRICING_TIERS: PricingTier[] = [
  {
    name: "Starter",
    price: 99,
    period: "/month",
    description: "For small teams getting started with AI-powered marketing.",
    features: [
      "5 active campaigns",
      "3 platform connections",
      "Basic AI orchestration",
      "Content generation",
      "Standard analytics",
      "Email support",
    ],
    cta: "Start Free Trial",
  },
  {
    name: "Agency",
    price: 999,
    period: "/month",
    description:
      "For agencies and enterprises managing campaigns at scale.",
    features: [
      "Unlimited campaigns",
      "All 9 platform connections",
      "Full AI orchestration & bidding",
      "AI video generation",
      "Advanced analytics & optimization",
      "Priority support",
      "Custom compliance rules",
      "Data Moat Engine",
      "Kill Switch access",
    ],
    cta: "Start Free Trial",
    popular: true,
  },
];

/* ------------------------------------------------------------------ */
/*  Security features                                                  */
/* ------------------------------------------------------------------ */

export interface SecurityFeature {
  icon: LucideIcon;
  title: string;
  description: string;
  items: string[];
}

export const SECURITY_FEATURES: SecurityFeature[] = [
  {
    icon: Lock,
    title: "Authentication & Encryption",
    description: "Industry-standard authentication and encryption at every layer.",
    items: [
      "Dual authentication: JWT bearer tokens + hashed API keys",
      "bcrypt password hashing with per-user salts",
      "Fernet (AES-128-CBC + HMAC-SHA256) encryption for OAuth tokens at rest",
      "Secure token refresh and revocation",
    ],
  },
  {
    icon: Users,
    title: "Role-Based Access Control",
    description: "Fine-grained permissions ensure the right people have the right access.",
    items: [
      "4-tier role hierarchy: Owner → Admin → Member → Viewer",
      "26 granular permissions across all platform features",
      "Kill switch restricted to Owner role only",
      "Data export and audit restricted to Admin and above",
    ],
  },
  {
    icon: Globe,
    title: "GDPR Compliance",
    description: "Full compliance with EU data protection regulations.",
    items: [
      "Data export — Article 20 (Right to Data Portability)",
      "Data deletion — Article 17 (Right to Erasure)",
      "Consent management — Article 7 (Consent Recording & Status)",
      "Complete data lineage and processing records",
    ],
  },
  {
    icon: Search,
    title: "Audit Trail",
    description: "Every action is logged, attributed, and auditable.",
    items: [
      "Full operation logging with user ID, tenant ID, and timestamp",
      "Financial audit entries with platform, amount, currency, and utilization",
      "Fire-and-forget persistence for zero-impact audit logging",
      "Queryable audit history for compliance reviews",
    ],
  },
  {
    icon: Eye,
    title: "Visual IP Protection",
    description: "AI-generated video is scanned for intellectual property issues before delivery.",
    items: [
      "GPT-4o Vision keyframe analysis for every generated video",
      "Celebrity likeness, copyright, and trademark detection",
      "Conservative policy — ambiguous content is blocked",
      "Temporary keyframe processing with automatic cleanup",
    ],
  },
  {
    icon: Database,
    title: "Multi-Tenant Isolation",
    description: "Your data never mixes with other organizations.",
    items: [
      "tenant_id scoping on all database tables",
      "Query-level isolation — no cross-tenant data access",
      "Qdrant vector collections namespaced per tenant",
      "No superuser bypass of tenant scoping",
    ],
  },
  {
    icon: ShieldCheck,
    title: "SOC 2 Readiness",
    description: "Built with SOC 2 compliance requirements in mind.",
    items: [
      "Logical access controls implemented",
      "User authentication and authorization enforcement",
      "26 granular permissions in RBAC",
      "Complete audit trail and change management",
    ],
  },
];

/* ------------------------------------------------------------------ */
/*  FAQ                                                                */
/* ------------------------------------------------------------------ */

export interface FAQItem {
  question: string;
  answer: string;
}

export interface FAQCategory {
  category: string;
  items: FAQItem[];
}

export const FAQ_DATA: FAQCategory[] = [
  {
    category: "Getting Started",
    items: [
      {
        question: "What is OrchestraAI?",
        answer:
          "OrchestraAI is an AI-Native Marketing Orchestration Platform that connects nine major advertising platforms (Twitter, YouTube, TikTok, Pinterest, Facebook, Instagram, LinkedIn, Snapchat, and Google Ads) under a single intelligent orchestrator. You issue natural language commands and OrchestraAI handles intent classification, compliance checking, content generation, publishing, and analytics.",
      },
      {
        question: "How do I create my first campaign?",
        answer:
          "Navigate to Campaigns in the sidebar, click 'Create Campaign', fill in the name, select target platforms, set your budget, and click Create. You can then launch it from the campaign list. Alternatively, use the AI Orchestrator and type something like 'Create a summer sale campaign on Instagram and TikTok with a $500 budget.'",
      },
      {
        question: "How do I connect my social media accounts?",
        answer:
          "Go to Settings > Platforms and click 'Connect' next to the platform you want to add. You will be redirected to the platform's OAuth flow to authorize OrchestraAI. Once connected, the platform appears as active in your dashboard.",
      },
    ],
  },
  {
    category: "AI & Orchestration",
    items: [
      {
        question: "What can the AI Orchestrator do?",
        answer:
          "The AI Orchestrator accepts natural language commands and can: create and launch campaigns, generate content (text, images, video), publish or schedule posts across platforms, run analytics reports, optimize campaign performance, check compliance, and reallocate budgets. Simply type your instruction and the AI handles the multi-step workflow automatically.",
      },
      {
        question: "What AI models does OrchestraAI use?",
        answer:
          "OrchestraAI uses a cost-aware routing system that selects the best model for each task. Cloud providers include OpenAI and Anthropic, and there is support for self-hosted models via Ollama for organizations that prefer local inference. The system automatically routes simple tasks to faster, cheaper models and complex tasks to more capable ones.",
      },
    ],
  },
  {
    category: "Platform Connections",
    items: [
      {
        question: "Can I run campaigns on multiple platforms simultaneously?",
        answer:
          "Yes. When creating a campaign, select multiple platforms (e.g., Instagram, TikTok, LinkedIn). OrchestraAI automatically adapts content for each platform's requirements and publishes across all of them. Cross-platform analytics are available in the Analytics dashboard.",
      },
      {
        question: "My platform connection shows as inactive. What should I do?",
        answer:
          "Platform connections can become inactive if the OAuth token expires. Go to Settings > Platforms, disconnect the inactive platform, and reconnect it. This will refresh your authorization tokens. If the issue persists, contact support@useorchestra.dev.",
      },
    ],
  },
  {
    category: "Billing & Pricing",
    items: [
      {
        question: "What pricing plans are available?",
        answer:
          "OrchestraAI offers two plans: Starter at $99/month and Agency at $999/month. The Starter plan is designed for small teams and includes core features. The Agency plan includes advanced features, higher limits, and priority support. OrchestraAI is also open-core with an Apache 2.0 license, so you can self-host for free.",
      },
      {
        question: "How do I upgrade or change my subscription?",
        answer:
          "Go to Settings > Billing, where you can see your current plan and click 'Upgrade' or 'Manage Subscription'. This opens the Stripe customer portal where you can change plans, update payment methods, or cancel.",
      },
    ],
  },
  {
    category: "Security & Compliance",
    items: [
      {
        question: "What is the Kill Switch?",
        answer:
          "The Kill Switch is an emergency feature that instantly halts all ad spend across every connected platform with a single click. It's available in the sidebar and is designed for situations where you need to immediately stop all campaigns — for example, if you detect anomalous spending or need to respond to a brand safety incident.",
      },
      {
        question: "How does OrchestraAI prevent overspending?",
        answer:
          "OrchestraAI enforces three-tier spend caps: daily, weekly, and monthly limits that cannot be overridden by the AI. It also uses statistical anomaly detection (Z-scores and IQR) to flag unusual spending patterns. The three-phase bidding system starts fully human-approved and gradually earns autonomy over time.",
      },
      {
        question: "Is my data safe with OrchestraAI?",
        answer:
          "Yes. OrchestraAI encrypts all platform tokens at rest, enforces tenant isolation so your data is never mixed with other organizations, provides full GDPR compliance tools (data export and deletion), and maintains a complete audit trail of all actions. API keys are stored using industry-standard hashing.",
      },
    ],
  },
  {
    category: "Analytics",
    items: [
      {
        question: "What analytics does OrchestraAI provide?",
        answer:
          "OrchestraAI provides cross-platform analytics including impressions, engagement, clicks, spend, ROI, and engagement rates for each connected platform. The dashboard shows aggregated metrics and per-platform breakdowns. You can also ask the AI Orchestrator for detailed reports by typing something like 'Show me analytics for last 30 days.'",
      },
    ],
  },
  {
    category: "Troubleshooting",
    items: [
      {
        question: "The AI Orchestrator returned an error. What should I do?",
        answer:
          "First, try rephrasing your request more specifically. If the error persists, check that you have an active subscription (Settings > Billing) and that your platform connections are active. For persistent issues, contact support@useorchestra.dev with your trace ID (shown in the error response).",
      },
    ],
  },
];

/* ------------------------------------------------------------------ */
/*  How It Works steps                                                 */
/* ------------------------------------------------------------------ */

export interface Step {
  number: number;
  title: string;
  description: string;
  icon: LucideIcon;
}

export const HOW_IT_WORKS: Step[] = [
  {
    number: 1,
    title: "Describe",
    description:
      "Tell OrchestraAI what you need in plain English. \"Generate a video ad for our summer sale and publish to Instagram and TikTok.\"",
    icon: Zap,
  },
  {
    number: 2,
    title: "Orchestrate",
    description:
      "The 10-node AI agent classifies intent, generates content, creates video, checks compliance, and validates platform rules — all automatically.",
    icon: BrainCircuit,
  },
  {
    number: 3,
    title: "Publish",
    description:
      "Content goes live across your selected platforms with optimized settings. Analytics flow back to fuel the next campaign.",
    icon: Globe,
  },
];
