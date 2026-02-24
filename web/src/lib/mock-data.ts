import type { ClinicalRecord, Flags, AnalyticsData } from "./types";

export const SAMPLE_NOTE_EN = `Patient: Maria Gonzalez, 54F
Chief Complaint: "I've been having chest pain for the past 3 days"
HPI: 54-year-old female presents with substernal chest pain, described as pressure-like, radiating to the left arm. Pain is worse with exertion and relieved by rest. No associated shortness of breath, nausea, or diaphoresis. Patient has a history of hypertension and type 2 diabetes.
ROS: Negative for fever, weight loss, cough, palpitations. Positive for occasional dizziness.
PMH: Hypertension (10 years), Type 2 DM (5 years), Hyperlipidemia
Medications: Metformin 1000mg BID, Lisinopril 20mg daily, Atorvastatin 40mg daily
Allergies: Penicillin (rash)
Social History: Non-smoker, occasional alcohol use, sedentary lifestyle
Family History: Father had MI at age 60, mother has HTN
Vital Signs: BP 145/92, HR 88, RR 16, Temp 98.6F, SpO2 98%
Physical Exam: Alert, oriented. Heart: RRR, no murmurs. Lungs: CTAB. Abdomen: soft, non-tender.
Assessment/Plan:
1. Chest pain - rule out ACS. Order troponin, EKG, CXR. Start aspirin 325mg.
2. Hypertension - poorly controlled. Increase lisinopril to 40mg daily.
3. Diabetes - continue metformin. Check HbA1c.
Follow-up in 1 week or sooner if symptoms worsen.`;

export const SAMPLE_NOTE_ES = `Paciente: María González, 54F
Motivo de consulta: "He tenido dolor en el pecho durante los últimos 3 días"
Historia: Mujer de 54 años presenta dolor torácico subesternal, descrito como presión, irradiado al brazo izquierdo. El dolor empeora con el esfuerzo y se alivia con el reposo.
Antecedentes: Hipertensión (10 años), DM tipo 2 (5 años), Hiperlipidemia
Medicamentos: Metformina 1000mg BID, Lisinopril 20mg diario, Atorvastatina 40mg diario
Alergias: Penicilina (erupción)
Plan: Descartar SCA. Troponina, EKG, RX tórax. Aspirina 325mg.`;

export const MOCK_RECORD: ClinicalRecord = {
  chief_complaint: "Chest pain for the past 3 days",
  hpi: "54-year-old female with substernal chest pain, pressure-like, radiating to left arm. Worse with exertion, relieved by rest. No SOB, nausea, or diaphoresis. History of HTN and T2DM.",
  assessment: [
    { description: "Chest pain, unspecified", icd10: "R07.9", confidence: "high" },
    { description: "Essential hypertension", icd10: "I10", confidence: "high" },
    { description: "Type 2 diabetes mellitus", icd10: "E11.9", confidence: "high" },
  ],
  plan: "1. Rule out ACS: order troponin, EKG, CXR. Start aspirin 325mg.\n2. Increase lisinopril to 40mg daily for blood pressure control.\n3. Continue metformin, check HbA1c.",
  medications: [
    { name: "Metformin", dose: "1000mg", frequency: "BID", status: "continue" },
    { name: "Lisinopril", dose: "40mg", frequency: "daily", status: "increased" },
    { name: "Atorvastatin", dose: "40mg", frequency: "daily", status: "continue" },
    { name: "Aspirin", dose: "325mg", frequency: "once", status: "new" },
  ],
  allergies: [{ substance: "Penicillin", reaction: "Rash" }],
  red_flags: [
    "Chest pain with exertion — evaluate for ACS",
    "Poorly controlled hypertension (BP 145/92)",
  ],
  follow_up: "1 week or sooner if symptoms worsen",
  patient_summary_plain_language:
    "María González es una mujer de 54 años que acude por dolor en el pecho durante 3 días. El dolor se siente como presión en el centro del pecho y se extiende al brazo izquierdo. Empeora con actividad física. Tiene antecedentes de presión alta y diabetes. Se ordenaron exámenes para descartar un problema cardíaco grave. Se inició aspirina y se ajustó la medicina para la presión.",
};

export const MOCK_FLAGS: Flags = {
  missing_fields: ["Social determinants of health", "BMI / Weight"],
  contradictions: [],
  confidence_by_field: {
    chief_complaint: "high",
    hpi: "high",
    assessment: "high",
    medications: "high",
    allergies: "high",
    plan: "high",
    follow_up: "high",
    social_history: "medium",
  },
  completeness_score: 0.87,
};

export const MOCK_RECORDS_LIST = [
  { note_id: "demo-001", created_at: "2026-02-22T10:30:00Z", completeness: 0.87, flags_count: 2, status: "saved" },
  { note_id: "demo-002", created_at: "2026-02-21T14:15:00Z", completeness: 0.92, flags_count: 1, status: "saved" },
  { note_id: "demo-003", created_at: "2026-02-20T09:00:00Z", completeness: 0.74, flags_count: 4, status: "saved" },
  { note_id: "demo-004", created_at: "2026-02-19T16:45:00Z", completeness: 0.95, flags_count: 0, status: "saved" },
  { note_id: "demo-005", created_at: "2026-02-18T11:20:00Z", completeness: 0.68, flags_count: 5, status: "saved" },
];

export const MOCK_ANALYTICS: AnalyticsData = {
  avg_latency_ms: 1247,
  avg_completeness: 83.2,
  extraction_success_rate: 97.8,
  requests_per_minute: 12,
  missing_fields_frequency: [
    { field: "Social History", count: 34 },
    { field: "BMI / Weight", count: 28 },
    { field: "Family History Detail", count: 22 },
    { field: "Review of Systems", count: 18 },
    { field: "Immunization Status", count: 15 },
  ],
  contradictions_frequency: 4.2,
};

export const MOCK_SYNC_EVENTS = [
  { id: 1, record_id: "demo-001", status: "synced", timestamp: "2026-02-22T10:31:00Z", latency_ms: 340 },
  { id: 2, record_id: "demo-002", status: "synced", timestamp: "2026-02-21T14:16:00Z", latency_ms: 280 },
  { id: 3, record_id: "demo-003", status: "synced", timestamp: "2026-02-20T09:02:00Z", latency_ms: 510 },
  { id: 4, record_id: "local-006", status: "queued", timestamp: "2026-02-22T10:45:00Z", latency_ms: null },
  { id: 5, record_id: "local-007", status: "failed", timestamp: "2026-02-22T10:40:00Z", latency_ms: null },
];
