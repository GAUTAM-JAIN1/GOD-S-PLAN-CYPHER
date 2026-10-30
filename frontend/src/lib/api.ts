export function getApiBase(): string {
  if (typeof window !== "undefined") {
    if (process.env.NEXT_PUBLIC_API_URL && !process.env.NEXT_PUBLIC_API_URL.includes("127.0.0.1") && !process.env.NEXT_PUBLIC_API_URL.includes("localhost")) {
      return process.env.NEXT_PUBLIC_API_URL;
    }
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
}

export function getWsBase(): string {
  if (typeof window !== "undefined") {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${proto}//${window.location.hostname}:8000`;
  }
  return "ws://127.0.0.1:8000";
}

export const API_BASE = {
  toString() {
    return getApiBase();
  },
};


export interface CatalogItem {
  id: string;
  canonical_name: string;
  category: string;
  price_inr: number;
  unit_or_duration: string;
  phonetic_aliases: string[];
  allowed_modifiers: string[];
}

export interface StrictPolicy {
  id: string;
  rule: string;
  severity: string;
  enforcement_action: string;
}

export interface DomainProfile {
  id: string;
  name: string;
  domain_type: string;
  tagline: string;
  system_prompt: string;
  first_message: string;
  voice_id: string;
  language_code: string;
  turn_timeout_ms: number;
  catalog_items: CatalogItem[];
  strict_policies: StrictPolicy[];
  elevenlabs_agent_id?: string | null;
  compiled_by?: string;
  crew_execution_log_json?: string;
  created_at?: string;
  updated_at?: string;
}

export interface CompileDomainResponse {
  success: boolean;
  domain_id: string;
  system_prompt: string;
  first_message: string;
  catalog_items: CatalogItem[];
  strict_policies: StrictPolicy[];
  pydantic_literal_code: string;
  raw_tokens_used?: number;
  error?: string | null;
}

export interface LiveRefineResponse {
  success: boolean;
  diff_applied: string[];
  updated_system_prompt: string;
  updated_first_message: string;
  elevenlabs_synced: boolean;
  error?: string | null;
}

export interface ProvisionAgentResponse {
  success: boolean;
  agent_id?: string | null;
  status: string;
  payload_preview: Record<string, unknown>;
  message: string;
}

export interface ScribeSTTResponse {
  success: boolean;
  transcription: string;
  confidence: number;
  duration_seconds: number;
  engine: string;
  error?: string | null;
}

export interface PDFParseResponse {
  success: boolean;
  filename: string;
  page_count: number;
  extracted_text: string;
  preview_items_detected: number;
  error?: string | null;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  keys: {
    groq_configured: boolean;
    elevenlabs_configured: boolean;
    telegram_configured: boolean;
  };
  telemetry: {
    llm_engine: string;
    tts_engine: string;
    stt_engine: string;
    ws_active_clients: number;
  };
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function fetchDomains(): Promise<DomainProfile[]> {
  const res = await fetch(`${API_BASE}/api/domains`);
  if (!res.ok) throw new Error(`Failed to load domains: ${res.statusText}`);
  return res.json();
}

export async function fetchDomain(domainId: string): Promise<DomainProfile> {
  const res = await fetch(`${API_BASE}/api/domains/${domainId}`);
  if (!res.ok) throw new Error(`Domain not found: ${res.statusText}`);
  return res.json();
}

export async function compileDomain(data: {
  domain_id?: string;
  domain_type: string;
  business_name: string;
  owner_instructions: string;
  parsed_catalog_text?: string;
}): Promise<CompileDomainResponse> {
  const res = await fetch(`${API_BASE}/api/domains/compile`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function uploadCatalogPdf(file: File): Promise<PDFParseResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/domains/upload-pdf`, {
    method: "POST",
    body: formData,
  });
  return res.json();
}

export async function transcribeAudioScribe(audioBlob: Blob): Promise<ScribeSTTResponse> {
  const formData = new FormData();
  formData.append("file", audioBlob, "voice_prompt.wav");
  const res = await fetch(`${API_BASE}/api/domains/scribe-stt`, {
    method: "POST",
    body: formData,
  });
  return res.json();
}

export async function liveRefineAgent(
  domainId: string,
  instruction: string
): Promise<LiveRefineResponse> {
  const res = await fetch(`${API_BASE}/api/domains/live-refine`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ domain_id: domainId, refine_instruction: instruction }),
  });
  return res.json();
}

export async function provisionElevenLabsAgent(domainId: string): Promise<ProvisionAgentResponse> {
  const res = await fetch(`${API_BASE}/api/domains/provision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ domain_id: domainId }),
  });
  return res.json();
}

export interface ConvaiVoice {
  voice_id: string;
  name: string;
  accent: string;
  category: string;
  preview_url?: string;
}

export async function fetchConvaiVoices(): Promise<ConvaiVoice[]> {
  const res = await fetch(`${API_BASE}/api/convai/voices`);
  if (!res.ok) throw new Error("Failed to load voices");
  return res.json();
}

export async function fetchConvaiSignedUrl(domainId: string): Promise<{ signed_url: string; agent_id: string }> {
  const res = await fetch(`${API_BASE}/api/convai/signed-url?domain_id=${domainId}`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || `Signed URL error (${res.status})`);
  }
  return res.json();
}

export interface GuardrailCandidate {
  id: string;
  canonical_name: string;
  price_inr: number;
  score: number;
  probability_pct: number;
}

export interface GuardrailVerifyResult {
  success: boolean;
  match_type: "DETERMINISTIC_PASS" | "WHISPER_HOLD" | "VALIDATION_FAILED";
  score: number;
  verification_token?: string | null;
  filtered_entity?: string;
  matched_item: CatalogItem | null;
  quantity: number;
  unit_price_inr: number;
  total_price_inr: number;
  candidates: GuardrailCandidate[];
  instruction: string;
}

export async function verifyCatalogItemTool(data: {
  domain_id: string;
  spoken_entity: string;
  quantity?: number;
  modifiers?: string[];
  caller_utterance?: string;
  session_id?: string;
}): Promise<GuardrailVerifyResult> {
  const res = await fetch(`${API_BASE}/api/guardrail/verify-catalog-item`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Guardrail evaluation failed");
  }
  return res.json();
}

export interface CommitActionResult {
  success: boolean;
  message: string;
  ledger_id: string;
  status: string;
}

export async function commitActionTool(data: {
  domain_id: string;
  token?: string | null;
  session_id?: string;
  canonical_name?: string;
  quantity?: number;
  total_price_inr?: number;
  caller_phone?: string;
  caller_name?: string;
  delivery_address?: string;
}): Promise<CommitActionResult> {
  const res = await fetch(`${API_BASE}/api/guardrail/commit-action`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Action commit failed");
  }
  return res.json();
}

export async function requestHumanInterventionTool(data: {
  domain_id: string;
  reason?: string;
  caller_utterance?: string;
  session_id?: string;
}): Promise<{ success: boolean; hold_id: string; message: string }> {
  const res = await fetch(`${API_BASE}/api/guardrail/request-human-intervention`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to request human intervention");
  return res.json();
}

export interface InterceptHoldItem {
  id: string;
  session_id: string;
  domain_id: string;
  spoken_entity: string;
  caller_utterance: string;
  phonetic_score: number;
  candidate_1: GuardrailCandidate;
  candidate_2: GuardrailCandidate;
  hold_reason: string;
  status: string;
  created_at: string;
  remaining_sla_sec?: number;
  expires_at_epoch_ms?: number;
}

export async function fetchActiveHolds(): Promise<InterceptHoldItem[]> {
  const res = await fetch(`${API_BASE}/api/guardrail/active-holds`);
  if (!res.ok) throw new Error("Failed to load active holds");
  return res.json();
}

export async function resolveHold(
  holdId: string,
  action: string,
  customWhisper: string = "",
  resolvedBy: "DESKTOP_CONSOLE" | "MOBILE_COMPANION" | "TELEGRAM_BOT" = "DESKTOP_CONSOLE"
): Promise<{
  success: boolean;
  hold_id: string;
  resolution_action: string;
  resolved_by: string;
  agent_contextual_instruction: string;
}> {
  const res = await fetch(`${API_BASE}/api/guardrail/resolve-hold`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      hold_id: holdId,
      resolution_action: action,
      custom_whisper_text: customWhisper,
      resolved_by: resolvedBy,
    }),
  });
  if (!res.ok) throw new Error("Failed to resolve hold");
  return res.json();
}

export async function requestHumanIntervention(data: {
  domain_id: string;
  session_id: string;
  caller_info?: string;
  reason?: string;
  urgency?: string;
  caller_utterance?: string;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/api/guardrail/request-intervention`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to request human intervention");
  return res.json();
}

export interface NetworkInfoResponse {
  lan_ip: string;
  port: number;
  mobile_copilot_url: string;
  backend_url: string;
  telegram: {
    configured: boolean;
    running: boolean;
    paired_chat_id: string | null;
    bot_username: string | null;
  };
}

export async function fetchNetworkInfo(): Promise<NetworkInfoResponse> {
  const res = await fetch(`${API_BASE}/api/system/network-info`);
  if (!res.ok) throw new Error("Failed to load network info");
  return res.json();
}

export async function sendTelegramTestAlert(message?: string): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/api/telegram/test-alert`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error("Failed to send telegram test alert");
  return res.json();
}

export interface LedgerEntryItem {
  id?: string;
  sessionId: string;
  domainId?: string;
  callerPhone: string;
  language: string;
  action: string;
  totalInr: string;
  amountRaw?: number;
  phoneticScore?: number;
  phoneticGate: string;
  status: string;
  timestamp: string;
  details?: Record<string, any>;
  type: string;
}

export interface LedgerStatsResponse {
  completed_calls_24h: number;
  hallucinations_count: number;
  median_voice_latency_ms: number;
  interventions_count: number;
  avg_owner_response_sec: number;
  two_phase_commit_enforced: boolean;
}

export async function fetchLedgerEntries(): Promise<LedgerEntryItem[]> {
  const res = await fetch(`${API_BASE}/api/ledger/entries`);
  if (!res.ok) throw new Error("Failed to load ledger entries");
  return res.json();
}

export async function fetchLedgerStats(): Promise<LedgerStatsResponse> {
  const res = await fetch(`${API_BASE}/api/ledger/stats`);
  if (!res.ok) throw new Error("Failed to load ledger stats");
  return res.json();
}

export async function fetchLedgerInspector(sessionId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/ledger/entries/${encodeURIComponent(sessionId)}`);
  if (!res.ok) throw new Error("Failed to load session details");
  return res.json();
}

export interface GauntletScenarioItem {
  scenario_id: number;
  title: string;
  attack_vector: string;
  attacker_utterance: string;
  initial_agent_response: string;
  tool_validation_summary: string;
  status: "PASS" | "AUTO-PATCHED" | "FAIL" | "RUNNING";
  latency_ms: number;
  vulnerability_detected: boolean;
  patched_guardrail_rule?: string | null;
  post_patch_agent_response?: string | null;
  evaluator_diff: string;
  duel_transcript?: Array<{
    speaker?: string;
    sender?: string;
    text: string;
    stage?: string;
  }>;
}

export interface GauntletRunResult {
  success: boolean;
  run_id: string;
  domain_id: string;
  scenarios_passed: number;
  auto_healed_count: number;
  mean_latency_ms: number;
  scenarios: GauntletScenarioItem[];
  created_at: string;
}

export async function runGauntlet(
  domainId: string,
  forceVulnerabilityDemo: boolean = true
): Promise<GauntletRunResult> {
  const res = await fetch(`${API_BASE}/api/gauntlet/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      domain_id: domainId,
      force_vulnerability_demo: forceVulnerabilityDemo,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Gauntlet run failed");
  }
  return res.json();
}

export async function fetchLatestGauntlet(
  domainId: string
): Promise<{ has_run: boolean } & Partial<GauntletRunResult>> {
  const res = await fetch(`${API_BASE}/api/gauntlet/latest?domain_id=${domainId}`);
  if (!res.ok) throw new Error("Failed to load latest gauntlet run");
  return res.json();
}

export async function resetGauntletVulnerability(
  domainId: string
): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/api/gauntlet/reset-vulnerability`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ domain_id: domainId }),
  });
  if (!res.ok) throw new Error("Failed to reset vulnerability");
  return res.json();
}

export async function deleteDomain(domainId: string): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/api/domains/${encodeURIComponent(domainId)}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete domain");
  return res.json();
}

export async function extractBusinessName(rawText: string): Promise<{ clean_name: string; domain_id: string }> {
  const res = await fetch(`${API_BASE}/api/domains/extract-name`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw_text: rawText }),
  });
  if (!res.ok) throw new Error("Failed to extract business name");
  return res.json();
}

export async function pairTelegramChat(chatId: string): Promise<{ success: boolean; paired_chat_id: string; message: string }> {
  const res = await fetch(`${API_BASE}/api/telegram/pair`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chatId }),
  });
  if (!res.ok) throw new Error("Failed to pair Telegram chat");
  return res.json();
}

export async function sendTelegramTakeoverAlert(data: {
  domain_name: string;
  caller_info?: string;
  utterance?: string;
  order_summary?: string;
  hold_id?: string;
}): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/api/telegram/takeover-alert`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to send takeover alert");
  return res.json();
}

export async function callVoiceLiveTurn(data: {
  domain_id: string;
  user_utterance: string;
  session_id?: string;
  conversation_history?: Array<{ role: string; content: string }>;
}): Promise<{ success: boolean; reply: string; llm_latency_ms: number; total_latency_ms: number; model: string }> {
  const res = await fetch(`${API_BASE}/api/voice/live-turn`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to execute live turn");
  return res.json();
}

export async function runModule7Suite(domainId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/module7/run-all`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ domain_id: domainId }),
  });
  if (!res.ok) throw new Error("Failed to run Module 7 test suite");
  return res.json();
}

