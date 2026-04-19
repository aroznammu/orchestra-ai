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
  /** Video completion rate (0–1), primarily for CTV / programmatic video */
  video_completion_rate?: number;
  /** Effective CPM ($), primarily for CTV / programmatic */
  effective_cpm?: number;
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

export async function put<T = unknown>(
  path: string,
  body?: unknown,
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "PUT",
    headers: headers(),
    body: body ? JSON.stringify(body) : undefined,
  });
  return handleResponse<T>(res);
}

export async function del<T = unknown>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "DELETE",
    headers: headers(),
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

export async function register(
  email: string,
  password: string,
  fullName: string,
  tenantName?: string,
): Promise<TokenResponse> {
  const data = await post<TokenResponse>("/auth/register", {
    email,
    password,
    full_name: fullName,
    tenant_name: tenantName || fullName + "'s Workspace",
  });
  setToken(data.access_token);
  return data;
}

export async function login(
  email: string,
  password: string,
): Promise<TokenResponse> {
  const data = await post<TokenResponse>("/auth/login", { email, password });
  setToken(data.access_token);
  return data;
}

export async function changePassword(
  currentPassword: string,
  newPassword: string,
): Promise<void> {
  await put("/auth/password", {
    current_password: currentPassword,
    new_password: newPassword,
  });
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

// ---------------------------------------------------------------------------
// Support Chat types & functions
// ---------------------------------------------------------------------------

export interface ChatSessionResponse {
  id: string;
  title: string;
  status: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ChatMessageResponse {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ChatReplyResponse {
  session_id: string;
  user_message: ChatMessageResponse;
  assistant_message: ChatMessageResponse;
  sources: string[];
}

export async function listSupportSessions(): Promise<ChatSessionResponse[]> {
  return get<ChatSessionResponse[]>("/support/sessions");
}

export async function createSupportSession(
  title?: string,
): Promise<ChatSessionResponse> {
  return post<ChatSessionResponse>("/support/sessions", { title });
}

export async function sendSupportMessage(
  sessionId: string,
  message: string,
): Promise<ChatReplyResponse> {
  return post<ChatReplyResponse>("/support/chat", {
    session_id: sessionId,
    message,
  });
}

export async function getSessionMessages(
  sessionId: string,
): Promise<ChatMessageResponse[]> {
  return get<ChatMessageResponse[]>(
    `/support/sessions/${sessionId}/messages`,
  );
}

export async function resolveSession(
  sessionId: string,
): Promise<ChatSessionResponse> {
  return post<ChatSessionResponse>(
    `/support/sessions/${sessionId}/resolve`,
  );
}

// ---------------------------------------------------------------------------
// FAQ types & functions
// ---------------------------------------------------------------------------

export interface FAQEntryResponse {
  id: string;
  category: string;
  question: string;
  answer: string;
  sort_order: number;
  is_published: boolean;
  created_at: string;
  updated_at: string;
}

export interface FAQGroupResponse {
  category: string;
  entries: FAQEntryResponse[];
}

export async function listFAQs(): Promise<FAQGroupResponse[]> {
  return get<FAQGroupResponse[]>("/faq");
}

export async function createFAQ(payload: {
  category?: string;
  question: string;
  answer: string;
  sort_order?: number;
  is_published?: boolean;
}): Promise<FAQEntryResponse> {
  return post<FAQEntryResponse>("/faq", payload);
}

export async function updateFAQ(
  id: string,
  payload: {
    category?: string;
    question?: string;
    answer?: string;
    sort_order?: number;
    is_published?: boolean;
  },
): Promise<FAQEntryResponse> {
  return patch<FAQEntryResponse>(`/faq/${id}`, payload);
}

export async function deleteFAQ(id: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/faq/${id}`, {
    method: "DELETE",
    headers: headers(),
  });
  if (!res.ok) {
    await handleResponse(res);
  }
}

// ---------------------------------------------------------------------------
// Platforms types & functions
// ---------------------------------------------------------------------------

export type PlatformKey =
  | "facebook"
  | "instagram"
  | "tiktok"
  | "twitter"
  | "youtube"
  | "google_ads"
  | "linkedin"
  | "snapchat"
  | "pinterest";

export interface PlatformLimits {
  max_text_length?: number;
  max_hashtags?: number;
  max_images?: number;
  max_video_seconds?: number;
  supports_video?: boolean;
  supports_images?: boolean;
  [key: string]: unknown;
}

export interface AvailablePlatform {
  platform: PlatformKey;
  name: string;
  limits: PlatformLimits;
  is_stub: boolean;
}

export interface AvailablePlatformsResponse {
  platforms: AvailablePlatform[];
}

export interface PlatformConnection {
  id: string;
  platform: PlatformKey;
  is_active: boolean;
  platform_user_id: string | null;
  connected_at: string;
}

export interface PlatformConnectionsResponse {
  connections: PlatformConnection[];
  available: PlatformKey[];
}

export interface PlatformAuthInitResponse {
  auth_url: string;
  state: string;
}

export async function listAvailablePlatforms(): Promise<AvailablePlatformsResponse> {
  return get<AvailablePlatformsResponse>("/platforms/available");
}

export async function listPlatformConnections(): Promise<PlatformConnectionsResponse> {
  return get<PlatformConnectionsResponse>("/platforms/connections");
}

export async function initPlatformAuth(
  platform: PlatformKey,
  redirectUri: string,
): Promise<PlatformAuthInitResponse> {
  return post<PlatformAuthInitResponse>("/platforms/auth/init", {
    platform,
    redirect_uri: redirectUri,
  });
}

export async function disconnectPlatform(
  platform: PlatformKey,
): Promise<{ status: string; platform: string }> {
  return del<{ status: string; platform: string }>(
    `/platforms/connections/${platform}`,
  );
}

// ---------------------------------------------------------------------------
// Kill Switch types & functions
// ---------------------------------------------------------------------------

export interface KillSwitchStatus {
  global_active: boolean;
  tenant_active: boolean;
  is_affected: boolean;
}

export interface KillSwitchEvent {
  id: string;
  tenant_id: string;
  action: string;
  triggered_by: string;
  reason: string;
  timestamp: string;
  affected_platforms: string[];
  affected_campaigns: string[];
}

export async function getKillSwitchStatus(): Promise<KillSwitchStatus> {
  return get<KillSwitchStatus>("/kill-switch/status");
}

export async function activateKillSwitch(
  reason: string,
): Promise<{ activated: boolean; event_id: string; reason: string }> {
  return post<{ activated: boolean; event_id: string; reason: string }>(
    "/kill-switch/activate",
    { reason },
  );
}

export async function deactivateKillSwitch(): Promise<{
  deactivated: boolean;
  event_id: string;
}> {
  return post<{ deactivated: boolean; event_id: string }>(
    "/kill-switch/deactivate",
  );
}

export async function getKillSwitchHistory(): Promise<KillSwitchEvent[]> {
  return get<KillSwitchEvent[]>("/kill-switch/history");
}

// ---------------------------------------------------------------------------
// API Keys types & functions
// ---------------------------------------------------------------------------

export type APIKeyRole = "viewer" | "member" | "admin";

export interface APIKey {
  id: string;
  name: string;
  role: string;
  is_active: boolean;
  last_used_at: string | null;
  expires_at: string | null;
  created_at: string;
}

export interface APIKeyListResponse {
  keys: APIKey[];
}

export interface APIKeyCreateResponse extends APIKey {
  /** Full plaintext key (returned exactly once at creation) */
  key: string;
  /** First 8 characters of the plaintext key, safe to echo back later */
  prefix: string;
}

export interface CreateAPIKeyPayload {
  name: string;
  role?: APIKeyRole;
  expires_in_days?: number | null;
}

export async function listAPIKeys(): Promise<APIKeyListResponse> {
  return get<APIKeyListResponse>("/api-keys");
}

export async function createAPIKey(
  payload: CreateAPIKeyPayload,
): Promise<APIKeyCreateResponse> {
  return post<APIKeyCreateResponse>("/api-keys", payload);
}

export async function revokeAPIKey(id: string): Promise<void> {
  await del<void>(`/api-keys/${id}`);
}
