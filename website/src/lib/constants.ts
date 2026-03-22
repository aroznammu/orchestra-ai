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
export const GITHUB_URL = "https://github.com/aroznammu/orchestra-ai";

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
      "Every campaign compounds your performance intelligence. Your data moat grows over time \u2014 competitors can\u2019t copy your advantage.",
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
  code?: string;
}

export const FEATURES_DETAILED: FeatureDetail[] = [
  {
    id: "orchestration",
    icon: BrainCircuit,
    title: "AI Agent Orchestration",
    subtitle: "10-Node LangGraph Multi-Agent System",
    description:
      "A single natural-language command triggers a sophisticated 10-node agent graph that classifies intent, checks compliance, generates content, creates video, validates IP, enforces platform rules, publishes, collects analytics, optimizes performance, and responds \u2014 all automatically.",
    bullets: [
      "Classify \u2014 LLM intent classification with OpenAI \u2192 Anthropic \u2192 Ollama fallback",
      "Compliance Gate \u2014 Pre-action checks for prohibited content, targeting rules, budget limits",
      "Content Agent \u2014 Multi-provider LLM content generation with automatic fallback",
      "Video Node \u2014 AI video via Seedance 2.0 (text-to-video & image-to-video)",
      "Visual Compliance Gate \u2014 Keyframe extraction + GPT-4o Vision IP scanning",
      "Policy Node \u2014 Platform-specific rules (character limits, hashtags, media constraints)",
      "Platform Node \u2014 Publish/schedule dispatch to all 9 platform connectors",
      "Analytics Node \u2014 Cross-platform metrics aggregation and benchmarking",
      "Optimize Node \u2014 Thompson Sampling, UCB, and Bayesian budget allocation",
      "Respond \u2014 Final response assembly and execution trace cleanup",
    ],
    code: 'orchestra ask "Launch a summer sale campaign across Instagram and TikTok with a $500 budget"',
  },
  {
    id: "video",
    icon: Video,
    title: "AI Video Pipeline",
    subtitle: "Text-to-Video and Image-to-Video with IP Scanning",
    description:
      "Generate marketing video ads from natural language descriptions or reference images. Every frame is scanned for intellectual property violations before delivery.",
    bullets: [
      "Seedance 2.0 via fal.ai \u2014 ~$0.26 per 5-second 720p clip",
      "Text-to-video and image-to-video generation modes",
      "Visual Compliance Gate with GPT-4o Vision keyframe analysis",
      "Automatic detection of celebrity likenesses, copyrighted characters, trademarked logos",
      "Safe videos delivered in HTML5 player; flagged content blocked with violation details",
      "Per-tenant audit logging of all scan results",
    ],
    code: 'orchestra ask "Generate a video ad for our summer sale"',
  },
  {
    id: "guardrails",
    icon: ShieldCheck,
    title: "Financial Guardrails",
    subtitle: "3-Phase Bidding with 3-Tier Risk Containment",
    description:
      "Your AI earns autonomy over time through a phased progression system. Combined with multi-tier spend caps, anomaly detection, and an emergency kill switch, your budget is always protected.",
    bullets: [
      "Hard Guardrail Phase \u2014 Every bid requires explicit human approval",
      "Semi-Autonomous Phase \u2014 AI executes within bounds, exceptions reviewed by humans",
      "Controlled Autonomous Phase \u2014 Full AI control within strict limits, monitoring only",
      "3-tier spend caps \u2014 Daily, weekly, and monthly limits that AI cannot override",
      "Statistical anomaly detection \u2014 Z-score and IQR-based flagging of unusual spend",
      "Kill Switch \u2014 Halt all spend across all platforms with a single click",
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
      "ROI normalization \u2014 Comparable returns across every platform",
      "Marginal return analysis \u2014 Budget allocated to highest-impact channels",
      "Attribution modeling \u2014 Credit allocation across platform touchpoints",
      "Saturation detection \u2014 Flags diminishing returns automatically",
      "Intelligent budget reallocation \u2014 Dynamic redistribution based on performance",
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
      "Campaign \u2192 Engagement \u2192 Normalize \u2192 Embed \u2192 Model update flywheel",
      "Per-platform engagement signal normalization",
      "Content + performance embedding for retrieval",
      "Tenant-specific model that improves with every campaign",
      "Maturity progression: cold_start \u2192 warming \u2192 learning \u2192 maturing \u2192 optimized",
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
      "Twitter/X v2 \u2014 Publish, analytics, audience targeting",
      "YouTube v3 \u2014 Video publishing, analytics, audience management",
      "TikTok v2 \u2014 Short-form video, analytics, audience targeting",
      "Pinterest v5 \u2014 Pin publishing, analytics, audience insights",
      "Facebook Graph v19 \u2014 Posts, ads, analytics, audiences",
      "Instagram Graph v19 \u2014 Stories, reels, analytics, audiences",
      "LinkedIn v2 \u2014 Professional content, analytics, targeting",
      "Snapchat Marketing v1 \u2014 Snap ads, analytics, audience reach",
      "Google Ads v16 \u2014 Search, display, video ads, full analytics",
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
      "4-tier role hierarchy: Owner \u2192 Admin \u2192 Member \u2192 Viewer",
      "26 granular permissions across campaigns, platforms, analytics, budget, and more",
      "Query-level tenant isolation \u2014 no cross-tenant data access possible",
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
      "OpenAI text-embedding-3-small \u2192 Ollama nomic-embed-text \u2192 hash fallback",
      "Campaign memory \u2014 index campaigns, content templates, and AI decisions",
      "Performance-weighted retrieval \u2014 successful campaigns rank higher",
      "Metric updates \u2014 embeddings refresh as campaign performance evolves",
    ],
  },
];

/* ------------------------------------------------------------------ */
/*  Comparison table                                                   */
/* ------------------------------------------------------------------ */

export interface ComparisonRow {
  capability: string;
  orchestra: boolean;
  hootsuite: boolean;
  buffer: boolean;
  diy: boolean;
}

export const COMPARISON_DATA: ComparisonRow[] = [
  { capability: "AI Agent Orchestration", orchestra: true, hootsuite: false, buffer: false, diy: false },
  { capability: "AI Video Generation", orchestra: true, hootsuite: false, buffer: false, diy: false },
  { capability: "Visual Compliance Gate", orchestra: true, hootsuite: false, buffer: false, diy: false },
  { capability: "Cross-Platform Intelligence", orchestra: true, hootsuite: false, buffer: false, diy: false },
  { capability: "Guardrailed Bidding", orchestra: true, hootsuite: false, buffer: false, diy: false },
  { capability: "Financial Risk Containment", orchestra: true, hootsuite: false, buffer: false, diy: false },
  { capability: "Self-Hostable", orchestra: true, hootsuite: false, buffer: false, diy: true },
  { capability: "CLI-First", orchestra: true, hootsuite: false, buffer: false, diy: true },
  { capability: "RAG Memory", orchestra: true, hootsuite: false, buffer: false, diy: false },
  { capability: "Open Source (Apache 2.0)", orchestra: true, hootsuite: false, buffer: false, diy: true },
  { capability: "9 Platform Connectors", orchestra: true, hootsuite: true, buffer: false, diy: false },
];

/* ------------------------------------------------------------------ */
/*  Architecture nodes                                                 */
/* ------------------------------------------------------------------ */

export interface ArchNode {
  id: string;
  label: string;
  description: string;
}

export const ARCHITECTURE_NODES: ArchNode[] = [
  { id: "input", label: "User Input", description: "Natural language command" },
  { id: "classify", label: "Classify", description: "Intent classification" },
  { id: "compliance", label: "Compliance", description: "Pre-action checks" },
  { id: "content", label: "Content", description: "LLM generation" },
  { id: "video", label: "Video", description: "Seedance 2.0" },
  { id: "vcg", label: "Vision Gate", description: "IP compliance scan" },
  { id: "policy", label: "Policy", description: "Platform rules" },
  { id: "platform", label: "Publish", description: "9-platform dispatch" },
  { id: "analytics", label: "Analytics", description: "Metrics collection" },
  { id: "respond", label: "Response", description: "Final output" },
];

/* ------------------------------------------------------------------ */
/*  Testimonials                                                       */
/* ------------------------------------------------------------------ */

export interface Testimonial {
  quote: string;
  role: string;
  company: string;
  initials: string;
  metric?: string;
}

export const TESTIMONIALS: Testimonial[] = [
  {
    quote: "OrchestraAI replaced five separate tools and cut our campaign setup time by 80%. What used to take a full day now happens in one prompt.",
    role: "Marketing Director",
    company: "Series B SaaS, 120 employees",
    initials: "JM",
    metric: "80% faster setup",
  },
  {
    quote: "The financial guardrails saved us from a $5,000 mistake on Google Ads in the first week. The 3-tier spend caps and anomaly detection are genuinely unique.",
    role: "Head of Digital Marketing",
    company: "E-Commerce Brand, $12M ARR",
    initials: "SK",
    metric: "$5K saved in week 1",
  },
  {
    quote: "We manage 40+ client accounts across 6 platforms. The kill switch and real-time spend caps give us confidence no other tool provides at this scale.",
    role: "Agency Principal",
    company: "Performance Marketing Agency",
    initials: "RA",
    metric: "40+ accounts managed",
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
      "4-tier role hierarchy: Owner \u2192 Admin \u2192 Member \u2192 Viewer",
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
      "Data export \u2014 Article 20 (Right to Data Portability)",
      "Data deletion \u2014 Article 17 (Right to Erasure)",
      "Consent management \u2014 Article 7 (Consent Recording & Status)",
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
      "Conservative policy \u2014 ambiguous content is blocked",
      "Temporary keyframe processing with automatic cleanup",
    ],
  },
  {
    icon: Database,
    title: "Multi-Tenant Isolation",
    description: "Your data never mixes with other organizations.",
    items: [
      "tenant_id scoping on all database tables",
      "Query-level isolation \u2014 no cross-tenant data access",
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
          "Navigate to Campaigns in the sidebar, click \u2018Create Campaign\u2019, fill in the name, select target platforms, set your budget, and click Create. You can then launch it from the campaign list. Alternatively, use the AI Orchestrator and type something like \u2018Create a summer sale campaign on Instagram and TikTok with a $500 budget.\u2019",
      },
      {
        question: "How do I connect my social media accounts?",
        answer:
          "Go to Settings > Platforms and click \u2018Connect\u2019 next to the platform you want to add. You will be redirected to the platform\u2019s OAuth flow to authorize OrchestraAI. Once connected, the platform appears as active in your dashboard.",
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
          "Yes. When creating a campaign, select multiple platforms (e.g., Instagram, TikTok, LinkedIn). OrchestraAI automatically adapts content for each platform\u2019s requirements and publishes across all of them. Cross-platform analytics are available in the Analytics dashboard.",
      },
      {
        question: "My platform connection shows as inactive. What should I do?",
        answer:
          "Platform connections can become inactive if the OAuth token expires. Go to Settings > Platforms, disconnect the inactive platform, and reconnect it. This will refresh your authorization tokens.",
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
          "Go to Settings > Billing, where you can see your current plan and click \u2018Upgrade\u2019 or \u2018Manage Subscription\u2019. This opens the Stripe customer portal where you can change plans, update payment methods, or cancel.",
      },
    ],
  },
  {
    category: "Security & Compliance",
    items: [
      {
        question: "What is the Kill Switch?",
        answer:
          "The Kill Switch is an emergency feature that instantly halts all ad spend across every connected platform with a single click. It\u2019s available in the sidebar and is designed for situations where you need to immediately stop all campaigns \u2014 for example, if you detect anomalous spending or need to respond to a brand safety incident.",
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
          "OrchestraAI provides cross-platform analytics including impressions, engagement, clicks, spend, ROI, and engagement rates for each connected platform. The dashboard shows aggregated metrics and per-platform breakdowns. You can also ask the AI Orchestrator for detailed reports by typing something like \u2018Show me analytics for last 30 days.\u2019",
      },
    ],
  },
  {
    category: "Troubleshooting",
    items: [
      {
        question: "The AI Orchestrator returned an error. What should I do?",
        answer:
          "First, try rephrasing your request more specifically. If the error persists, check that you have an active subscription (Settings > Billing) and that your platform connections are active. For persistent issues, use the contact form or email support.",
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
      'Tell OrchestraAI what you need in plain English. "Generate a video ad for our summer sale and publish to Instagram and TikTok."',
    icon: Zap,
  },
  {
    number: 2,
    title: "Orchestrate",
    description:
      "The 10-node AI agent classifies intent, generates content, creates video, checks compliance, and validates platform rules \u2014 all automatically.",
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

/* ------------------------------------------------------------------ */
/*  Tech Stack                                                         */
/* ------------------------------------------------------------------ */

export interface TechItem {
  layer: string;
  tech: string;
}

export const TECH_STACK: TechItem[] = [
  { layer: "API", tech: "FastAPI, Uvicorn, Pydantic" },
  { layer: "Agents", tech: "LangGraph, LangChain, OpenAI / Anthropic / Ollama" },
  { layer: "Video", tech: "Seedance 2.0 (fal.ai), ffmpeg, GPT-4o Vision" },
  { layer: "Vector DB", tech: "Qdrant (RAG, campaign memory, data moat)" },
  { layer: "Database", tech: "PostgreSQL 16, SQLAlchemy 2.0, Alembic" },
  { layer: "Cache", tech: "Redis 7, Apache Kafka" },
  { layer: "CLI", tech: "Typer, Rich" },
  { layer: "Security", tech: "JWT, bcrypt, Fernet encryption" },
  { layer: "Infra", tech: "Docker Compose (6 services)" },
];
