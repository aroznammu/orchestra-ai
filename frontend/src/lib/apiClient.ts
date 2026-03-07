const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

const TOKEN_KEY = "orchestra_token";

// ---------------------------------------------------------------------------
// Token helpers
// ---------------------------------------------------------------------------

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

// ---------------------------------------------------------------------------
// TypeScript interfaces mirroring FastAPI Pydantic models
// ---------------------------------------------------------------------------

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface PlatformMetrics {
  impressions: number;
  engagement: number;
  clicks: number;
  engagement_rate: number;
  click_rate: number;
  spend: number;
  roi: number;
}

export interface OverviewResponse {
  total_impressions: number;
  total_engagement: number;
  total_clicks: number;
  total_spend: number;
  average_engagement_rate: number;
  platforms: Record<string, PlatformMetrics>;
  insights: string[];
  recommendations: string[];
}

export interface CampaignResponse {
  id: string;
  name: string;
  description: string | null;
  status: string;
  platforms: string[];
  budget: number;
  spent: number;
  start_date: string | null;
  end_date: string | null;
  target_audience: Record<string, unknown>;
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface CampaignListResponse {
  campaigns: CampaignResponse[];
  total: number;
}

// ---------------------------------------------------------------------------
// Internal fetch helpers
// ---------------------------------------------------------------------------

function headers(): HeadersInit {
  const h: Record<string, string> = {
    "Content-Type": "application/json",
  };
  const token = getToken();
  if (token) {
    h["Authorization"] = `Bearer ${token}`;
  }
  return h;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    throw new ApiError(401, "Unauthorized");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    const msg = body.detail ?? `Request failed (${res.status})`;
    throw new ApiError(res.status, msg);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Generic HTTP methods
// ---------------------------------------------------------------------------

export async function get<T = unknown>(
  path: string,
  params?: Record<string, string>,
): Promise<T> {
  const url = new URL(`${BASE_URL}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  }
  const res = await fetch(url.toString(), { headers: headers() });
  return handleResponse<T>(res);
}

export async function post<T = unknown>(
  path: string,
  body?: unknown,
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: headers(),
    body: body ? JSON.stringify(body) : undefined,
  });
  return handleResponse<T>(res);
}

export async function patch<T = unknown>(
  path: string,
  body?: unknown,
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "PATCH",
    headers: headers(),
    body: body ? JSON.stringify(body) : undefined,
  });
  return handleResponse<T>(res);
}

// ---------------------------------------------------------------------------
// Orchestrator types
// ---------------------------------------------------------------------------

export interface OrchestrateResponse {
  trace_id: string;
  intent: string | null;
  is_complete: boolean;
  error: string | null;
  compliance: Record<string, unknown> | null;
  content: Record<string, unknown> | null;
  analytics: Record<string, unknown> | null;
  optimization: Record<string, unknown> | null;
  policy: Record<string, unknown> | null;
  platform: Record<string, unknown> | null;
  video: Record<string, unknown> | null;
  video_compliance: Record<string, unknown> | null;
}

// ---------------------------------------------------------------------------
// Auth convenience functions
// ---------------------------------------------------------------------------

export async function login(
  email: string,
  password: string,
): Promise<TokenResponse> {
  const data = await post<TokenResponse>("/auth/login", { email, password });
  setToken(data.access_token);
  return data;
}

export async function loginWithApiKey(apiKey: string): Promise<void> {
  setToken(apiKey);
  try {
    await get("/auth/me");
  } catch {
    clearToken();
    throw new Error("Invalid API key");
  }
}

// ---------------------------------------------------------------------------
// Orchestrator
// ---------------------------------------------------------------------------

export async function askOrchestrator(
  prompt: string,
): Promise<OrchestrateResponse> {
  return post<OrchestrateResponse>("/orchestrator", { input: prompt });
}

// ---------------------------------------------------------------------------
// Billing types & functions
// ---------------------------------------------------------------------------

export interface PlanInfo {
  key: string;
  name: string;
  price_monthly: number;
  features: string[];
}

export interface SubscriptionStatus {
  plan: string;
  status: string;
  stripe_customer_id: string | null;
  has_subscription: boolean;
  plan_expires_at: string | null;
}

export async function getPlans(): Promise<{ plans: PlanInfo[] }> {
  return get<{ plans: PlanInfo[] }>("/billing/plans");
}

export async function getSubscriptionStatus(): Promise<SubscriptionStatus> {
  return get<SubscriptionStatus>("/billing/status");
}

export async function createCheckout(plan: string): Promise<{ url: string }> {
  return post<{ url: string }>("/billing/checkout", { plan });
}

export async function createPortalSession(): Promise<{ url: string }> {
  return post<{ url: string }>("/billing/portal");
}

// ---------------------------------------------------------------------------
// Campaigns
// ---------------------------------------------------------------------------

export interface CampaignCreatePayload {
  name: string;
  description?: string;
  platforms?: string[];
  budget?: number;
  start_date?: string;
  end_date?: string;
  target_audience?: Record<string, unknown>;
  settings?: Record<string, unknown>;
}

export async function listCampaigns(): Promise<CampaignListResponse> {
  return get<CampaignListResponse>("/campaigns");
}

export async function createCampaign(
  payload: CampaignCreatePayload,
): Promise<CampaignResponse> {
  return post<CampaignResponse>("/campaigns", payload);
}

export async function launchCampaign(id: string): Promise<CampaignResponse> {
  return post<CampaignResponse>(`/campaigns/${id}/launch`);
}

export async function pauseCampaign(id: string): Promise<CampaignResponse> {
  return post<CampaignResponse>(`/campaigns/${id}/pause`);
}
