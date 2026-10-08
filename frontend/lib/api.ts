export type VerdictType =
  | "Verified"
  | "False"
  | "Outdated"
  | "Partly supported"
  | "Cannot be confirmed";

export interface EvidenceItem {
  source_name: string;
  url: string;
  date?: string;
  quote_or_passage: string;
  stance: "supports" | "contradicts" | "neutral";
  is_verified_citation: boolean;
  allowlist_passed: boolean;
}

export interface ClaimResult {
  claim_id: string;
  claim_text: string;
  original_span: string;
  verdict: VerdictType;
  confidence: number;
  what_is_right: string;
  what_is_wrong_or_missing: string;
  evidence: EvidenceItem[];
  as_of_date: string;
  date_changed?: string | null;
  explanation: string;
  explanation_en?: string | null;
  audio_base64?: string | null;
  audio_mime?: string | null;
}

export interface OverallSummary {
  total_claims: number;
  verified_count: number;
  false_count: number;
  outdated_count: number;
  partly_supported_count: number;
  cannot_be_confirmed_count: number;
  summary_text: string;
  dominant_verdict: VerdictType;
}

export interface FactCheckResponse {
  id: string;
  raw_input: string;
  input_type: "text" | "image" | "voice" | "pdf" | "url";
  detected_language: string;
  target_language: string;
  claims: ClaimResult[];
  summary: OverallSummary;
  created_at: string;
  status: string;
  error?: string | null;
}

export interface HistoryItem {
  id: string;
  input_type: string;
  snippet: string;
  dominant_verdict: VerdictType;
  summary_text: string;
  created_at: string;
}

export interface ChannelStatus {
  channel: string;
  is_live: boolean;
  phone_number_id: string;
  webhook_endpoint: string;
  status_message: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchHistory(): Promise<HistoryItem[]> {
  const res = await fetch(`${API_BASE}/api/history`);
  if (!res.ok) throw new Error("Failed to fetch history");
  return res.json();
}

export async function fetchCheckById(id: string): Promise<FactCheckResponse> {
  const res = await fetch(`${API_BASE}/api/history/${id}`);
  if (!res.ok) throw new Error("Failed to load check");
  return res.json();
}

export async function deleteCheckById(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/history/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete check");
}

export async function fetchChannelStatus(): Promise<ChannelStatus> {
  try {
    const res = await fetch(`${API_BASE}/api/webhook/status`);
    if (!res.ok) throw new Error();
    return res.json();
  } catch {
    return {
      channel: "WhatsApp Cloud API",
      is_live: false,
      phone_number_id: "Not Configured",
      webhook_endpoint: "/api/webhook/whatsapp",
      status_message: "Webhook ready. Cloud API credentials pending in .env (WHATSAPP_API_TOKEN)."
    };
  }
}

export async function submitFeedback(payload: {
  check_id: string;
  claim_id: string;
  reported_verdict: string;
  expected_verdict: string;
  correction_url?: string;
  notes?: string;
}): Promise<void> {
  const res = await fetch(`${API_BASE}/api/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error("Failed to submit feedback");
}
