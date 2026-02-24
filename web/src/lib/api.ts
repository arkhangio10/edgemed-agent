import { auth } from "./firebase";
import type {
  ExtractRequest,
  ExtractResponse,
  ChatRequest,
  ChatResponse,
  HealthResponse,
  AnalyticsData,
  InterpretImageRequest,
  InterpretImageResponse,
  PrescriptionFromImageRequest,
  PrescriptionFromImageResponse,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function getHeaders(): Promise<Record<string, string>> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  const user = auth.currentUser;
  if (user) {
    const token = await user.getIdToken();
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = await getHeaders();
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...headers, ...(options.headers as Record<string, string>) },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body || res.statusText}`);
  }
  return res.json();
}

let noteCounter = 0;

export function generateNoteId(): string {
  noteCounter += 1;
  return `demo-${Date.now()}-${noteCounter}`;
}

export async function extractNote(
  noteText: string,
  locale: string = "en"
): Promise<ExtractResponse> {
  const body: ExtractRequest = {
    note_id: generateNoteId(),
    note_text: noteText,
    locale,
    schema_version: "1.0.0",
    mode: "demo",
  };
  return apiFetch<ExtractResponse>("/v1/extract", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function chatWithCopilot(
  noteId: string,
  question: string,
  record: ExtractResponse["record"],
  noteText?: string
): Promise<ChatResponse> {
  const body: ChatRequest = {
    note_id: noteId,
    question,
    record,
    note_text: noteText,
    mode: "demo",
  };
  return apiFetch<ChatResponse>("/v1/chat", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function healthCheck(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/v1/health");
}

export async function fetchAnalytics(): Promise<AnalyticsData> {
  return apiFetch<AnalyticsData>("/v1/analytics/overview");
}

export async function interpretImage(
  imageBase64: string,
  promptOverride?: string
): Promise<InterpretImageResponse> {
  const body: InterpretImageRequest = {
    image_base64: imageBase64,
    prompt_override: promptOverride,
  };
  return apiFetch<InterpretImageResponse>("/v1/interpret-image", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function prescriptionFromImage(
  imageBase64: string
): Promise<PrescriptionFromImageResponse> {
  const body: PrescriptionFromImageRequest = {
    image_base64: imageBase64,
  };
  return apiFetch<PrescriptionFromImageResponse>("/v1/prescription-from-image", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
