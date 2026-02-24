export interface Medication {
  name: string;
  dose?: string;
  frequency?: string;
  route?: string;
  status?: string;
}

export interface Allergy {
  substance: string;
  reaction?: string;
  severity?: string;
}

export interface Problem {
  description: string;
  status?: string;
  icd10?: string;
  confidence?: "low" | "medium" | "high";
}

export interface ClinicalRecord {
  chief_complaint?: string;
  hpi?: string;
  assessment: Problem[];
  plan?: string;
  medications: Medication[];
  allergies: Allergy[];
  red_flags: string[];
  follow_up?: string;
  patient_summary_plain_language?: string;
}

export interface Flags {
  missing_fields: string[];
  contradictions: string[];
  confidence_by_field: Record<string, string>;
  completeness_score: number;
}

export interface ModelInfo {
  name: string;
  version: string;
  runtime: "cloud" | "local";
}

export interface ExtractRequest {
  note_id: string;
  note_text: string;
  locale: string;
  schema_version: string;
  mode: "demo" | "prod";
}

export interface ExtractResponse {
  record: ClinicalRecord;
  flags: Flags;
  model_info: ModelInfo;
  timing_ms: number;
}

export interface ChatRequest {
  note_id: string;
  question: string;
  record: ClinicalRecord;
  note_text?: string;
  mode: "demo" | "prod";
}

export interface ChatResponse {
  answer: string;
  grounded_on: string[];
  safety_notes: string[];
  timing_ms: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  model_loaded: boolean;
}

export interface AnalyticsData {
  avg_latency_ms: number;
  avg_completeness: number;
  extraction_success_rate: number;
  requests_per_minute: number;
  total_extractions?: number;
  missing_fields_frequency: { field: string; count: number }[];
  contradictions_frequency: number;
}

export interface InterpretImageRequest {
  image_base64: string;
  prompt_override?: string;
}

export interface InterpretImageResponse {
  interpretation: string;
  model_info: ModelInfo;
  timing_ms: number;
}

export interface PrescriptionFromImageRequest {
  image_base64: string;
}

export interface PrescriptionFromImageResponse {
  medications: Medication[];
  raw_text?: string;
  model_info: ModelInfo;
  timing_ms: number;
}
