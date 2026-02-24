import { useState, useCallback } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { StatusBadge, ConfidenceBadge } from "@/components/StatusBadge";
import { SAMPLE_NOTE_EN, SAMPLE_NOTE_ES, MOCK_RECORD, MOCK_FLAGS } from "@/lib/mock-data";
import { extractNote } from "@/lib/api";
import { usePatientStore } from "@/lib/patient-store";
import type { ClinicalRecord, Flags } from "@/lib/types";
import { Play, Copy, Check, RefreshCw, Loader2, ClipboardCheck, Stethoscope, ImagePlus, FileText } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { interpretImage, prescriptionFromImage } from "@/lib/api";
import type { Medication } from "@/lib/types";

export default function Workspace() {
  const [note, setNote] = useState("");
  const [language, setLanguage] = useState("en");
  const [extracting, setExtracting] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [record, setRecord] = useState<ClinicalRecord | null>(null);
  const [flags, setFlags] = useState<Flags | null>(null);
  const [noteId, setNoteId] = useState<string | null>(null);
  const [timingMs, setTimingMs] = useState(0);
  const [copied, setCopied] = useState<string | null>(null);
  const { toast } = useToast();
  const { selectedPatientId, addRecord } = usePatientStore();

  // Image interpretation
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [interpreting, setInterpreting] = useState(false);
  const [interpretationResult, setInterpretationResult] = useState<string | null>(null);
  const [interpretTimingMs, setInterpretTimingMs] = useState(0);

  // Prescription from image
  const [rxImageFile, setRxImageFile] = useState<File | null>(null);
  const [rxLoading, setRxLoading] = useState(false);
  const [rxMedications, setRxMedications] = useState<Medication[]>([]);
  const [rxTimingMs, setRxTimingMs] = useState(0);

  const handleExtract = useCallback(async () => {
    if (!note.trim()) {
      toast({ title: "Please enter a clinical note", variant: "destructive" });
      return;
    }
    setExtracting(true);
    setElapsed(0);
    setRecord(null);
    setFlags(null);
    setNoteId(null);

    const start = Date.now();
    const timer = setInterval(() => setElapsed(Date.now() - start), 100);

    try {
      const resp = await extractNote(note, language);
      clearInterval(timer);
      setElapsed(Date.now() - start);
      setRecord(resp.record);
      setFlags(resp.flags);
      setTimingMs(resp.timing_ms);
      setNoteId(`demo-${Date.now()}`);
      toast({
        title: "Extraction complete",
        description: `Completed in ${(resp.timing_ms / 1000).toFixed(1)}s via ${resp.model_info.runtime}`,
      });
    } catch (err) {
      clearInterval(timer);
      setElapsed(Date.now() - start);
      console.warn("API unavailable, using mock data:", err);
      setRecord(MOCK_RECORD);
      setFlags(MOCK_FLAGS);
      setTimingMs(Date.now() - start);
      setNoteId(`mock-${Date.now()}`);
      toast({
        title: "Extraction complete (demo fallback)",
        description: `API unavailable — showing sample results in ${((Date.now() - start) / 1000).toFixed(1)}s`,
      });
    } finally {
      setExtracting(false);
    }
  }, [note, language, toast]);

  const copyText = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopied(label);
    setTimeout(() => setCopied(null), 2000);
  };

  const loadSample = () => {
    setNote(language === "en" ? SAMPLE_NOTE_EN : SAMPLE_NOTE_ES);
    setRecord(null);
    setFlags(null);
  };

  const handleSave = () => {
    if (!record || !flags) return;
    if (selectedPatientId) {
      addRecord({
        patientId: selectedPatientId,
        note,
        extractedData: record,
        safetyFlags: flags,
        status: "saved",
      });
    }
    toast({ title: "Record saved" });
  };

  const completenessPercent = flags
    ? Math.round((typeof flags.completeness_score === "number" && flags.completeness_score <= 1
      ? flags.completeness_score * 100
      : flags.completeness_score))
    : 0;

  const fileToBase64 = (file: File): Promise<string> =>
    new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        const base64 = result.includes(",") ? result.split(",")[1] : result;
        resolve(base64 || "");
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });

  const handleInterpretImage = useCallback(async () => {
    if (!imageFile) {
      toast({ title: "Select an image first", variant: "destructive" });
      return;
    }
    setInterpreting(true);
    setInterpretationResult(null);
    try {
      const base64 = await fileToBase64(imageFile);
      const resp = await interpretImage(base64);
      setInterpretationResult(resp.interpretation);
      setInterpretTimingMs(resp.timing_ms);
      toast({ title: "Interpretation complete", description: `${(resp.timing_ms / 1000).toFixed(1)}s` });
    } catch (err) {
      toast({ title: "Interpretation failed", variant: "destructive", description: String(err) });
    } finally {
      setInterpreting(false);
    }
  }, [imageFile, toast]);

  const handlePrescriptionFromImage = useCallback(async () => {
    if (!rxImageFile) {
      toast({ title: "Select a prescription image first", variant: "destructive" });
      return;
    }
    setRxLoading(true);
    setRxMedications([]);
    try {
      const base64 = await fileToBase64(rxImageFile);
      const resp = await prescriptionFromImage(base64);
      setRxMedications(resp.medications);
      setRxTimingMs(resp.timing_ms);
      toast({
        title: "Extraction complete",
        description: `Found ${resp.medications.length} medication(s) in ${(resp.timing_ms / 1000).toFixed(1)}s`,
      });
    } catch (err) {
      toast({ title: "Extraction failed", variant: "destructive", description: String(err) });
    } finally {
      setRxLoading(false);
    }
  }, [rxImageFile, toast]);

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 flex items-center gap-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary shrink-0">
          <Stethoscope className="h-5 w-5" />
        </div>
        <div>
          <h2 className="text-sm font-semibold text-foreground">Welcome, Doctor</h2>
          <p className="text-xs text-muted-foreground">
            Extract from a note, interpret an image, or extract medications from a prescription.
          </p>
        </div>
      </div>

      <Tabs defaultValue="note" className="space-y-6">
        <TabsList className="grid w-full max-w-md grid-cols-3">
          <TabsTrigger value="note" className="gap-2">
            <Stethoscope className="h-4 w-4" />
            Note
          </TabsTrigger>
          <TabsTrigger value="image" className="gap-2">
            <ImagePlus className="h-4 w-4" />
            Image
          </TabsTrigger>
          <TabsTrigger value="prescription" className="gap-2">
            <FileText className="h-4 w-4" />
            Prescription
          </TabsTrigger>
        </TabsList>

        <TabsContent value="note" className="mt-0">
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Clinical Note Input</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Tabs defaultValue="paste">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="paste">Paste Note</TabsTrigger>
                  <TabsTrigger value="sample" onClick={loadSample}>Use Sample Note</TabsTrigger>
                </TabsList>
                <TabsContent value="paste" className="mt-3">
                  <Textarea
                    placeholder="Paste a clinical note here..."
                    className="min-h-[300px] font-mono text-sm"
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    aria-label="Clinical note input"
                  />
                </TabsContent>
                <TabsContent value="sample" className="mt-3">
                  <Textarea
                    className="min-h-[300px] font-mono text-sm"
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    aria-label="Clinical note input"
                  />
                </TabsContent>
              </Tabs>

              <div className="flex items-center gap-3">
                <Select value={language} onValueChange={setLanguage}>
                  <SelectTrigger className="w-32" aria-label="Language">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="es">Español</SelectItem>
                  </SelectContent>
                </Select>

                <Button
                  className="flex-1 gap-2 bg-gradient-hero hover:opacity-90 text-primary-foreground"
                  onClick={handleExtract}
                  disabled={extracting}
                >
                  {extracting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Extracting... {(elapsed / 1000).toFixed(1)}s
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      Extract Structured Record
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          {!record && !extracting && (
            <Card className="flex min-h-[400px] items-center justify-center">
              <p className="text-sm text-muted-foreground">
                Results will appear here after extraction
              </p>
            </Card>
          )}

          {extracting && (
            <Card className="flex min-h-[400px] flex-col items-center justify-center gap-4">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <div className="text-center">
                <p className="font-medium text-foreground">Processing with MedGemma</p>
                <p className="text-sm text-muted-foreground">{(elapsed / 1000).toFixed(1)}s elapsed</p>
              </div>
            </Card>
          )}

          {record && flags && (
            <>
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">Structured Record</CardTitle>
                    <StatusBadge variant="success">
                      {completenessPercent}% complete
                    </StatusBadge>
                  </div>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="readable">
                    <TabsList className="grid w-full grid-cols-2">
                      <TabsTrigger value="readable">Readable</TabsTrigger>
                      <TabsTrigger value="json">Raw JSON</TabsTrigger>
                    </TabsList>
                    <TabsContent value="readable" className="mt-3 space-y-4">
                      {record.chief_complaint && <Field label="Chief Complaint" value={record.chief_complaint} />}
                      {record.hpi && <Field label="HPI" value={record.hpi} />}
                      {(record.assessment?.length ?? 0) > 0 && (
                        <div>
                          <Label>Assessment / Diagnoses</Label>
                          <div className="space-y-1">
                            {record.assessment.map((d, i) => (
                              <div key={i} className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-sm">
                                <span>
                                  {d.description}
                                  {d.icd10 && <span className="text-muted-foreground"> ({d.icd10})</span>}
                                </span>
                                {d.confidence && <ConfidenceBadge level={d.confidence} />}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      {(record.medications?.length ?? 0) > 0 && (
                        <div>
                          <Label>Medications</Label>
                          <div className="space-y-1">
                            {record.medications.map((m, i) => (
                              <div key={i} className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-sm">
                                <span>{m.name} {m.dose || ""} {m.frequency || ""}</span>
                                {m.status && (
                                  <StatusBadge
                                    variant={m.status === "new" ? "info" : m.status === "increased" ? "warning" : "neutral"}
                                  >
                                    {m.status}
                                  </StatusBadge>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      {(record.allergies?.length ?? 0) > 0 && (
                        <Field
                          label="Allergies"
                          value={record.allergies.map((a) => `${a.substance}${a.reaction ? ` (${a.reaction})` : ""}`).join(", ")}
                        />
                      )}
                      {record.plan && (
                        <div>
                          <Label>Plan</Label>
                          <p className="text-sm text-foreground whitespace-pre-wrap">{record.plan}</p>
                        </div>
                      )}
                      {record.follow_up && <Field label="Follow-up" value={record.follow_up} />}
                      {(record.red_flags?.length ?? 0) > 0 && (
                        <div>
                          <Label>Red Flags</Label>
                          {record.red_flags.map((f, i) => (
                            <div key={i} className="rounded-md bg-destructive/5 border border-destructive/20 px-3 py-2 text-sm text-destructive mt-1">
                              {f}
                            </div>
                          ))}
                        </div>
                      )}
                    </TabsContent>
                    <TabsContent value="json" className="mt-3">
                      <div className="relative">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="absolute right-2 top-2"
                          onClick={() => copyText(JSON.stringify(record, null, 2), "json")}
                        >
                          {copied === "json" ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                        </Button>
                        <pre className="max-h-[400px] overflow-auto rounded-lg bg-muted p-4 text-xs font-mono">
                          {JSON.stringify(record, null, 2)}
                        </pre>
                      </div>
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Safety & Quality Flags</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {(flags.missing_fields?.length ?? 0) > 0 && (
                    <div>
                      <Label>Missing Fields</Label>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {flags.missing_fields.map((f) => (
                          <StatusBadge key={f} variant="warning">{f}</StatusBadge>
                        ))}
                      </div>
                    </div>
                  )}
                  {Object.keys(flags.confidence_by_field || {}).length > 0 && (
                    <div>
                      <Label>Field Confidence</Label>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {Object.entries(flags.confidence_by_field).map(([field, conf]) => (
                          <div key={field} className="flex items-center gap-1.5">
                            <span className="text-xs text-muted-foreground">{field}:</span>
                            <ConfidenceBadge level={conf as "low" | "medium" | "high"} />
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {(flags.contradictions?.length ?? 0) === 0 ? (
                    <div className="flex items-center gap-2 text-sm text-success">
                      <Check className="h-4 w-4" />
                      No contradictions detected
                    </div>
                  ) : (
                    <div>
                      <Label>Contradictions</Label>
                      {flags.contradictions.map((c, i) => (
                        <div key={i} className="rounded-md bg-destructive/5 border border-destructive/20 px-3 py-2 text-sm text-destructive mt-1">
                          {c}
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {record.patient_summary_plain_language && (
                <Card>
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base">Patient Summary (Plain Language)</CardTitle>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyText(record.patient_summary_plain_language!, "summary")}
                      >
                        {copied === "summary" ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-foreground leading-relaxed">{record.patient_summary_plain_language}</p>
                  </CardContent>
                </Card>
              )}

              <div className="flex flex-wrap gap-2">
                <Button
                  className="gap-2 bg-gradient-hero hover:opacity-90 text-primary-foreground"
                  onClick={handleSave}
                >
                  <ClipboardCheck className="h-4 w-4" />
                  Approve & Save
                </Button>
                <Button variant="outline" className="gap-2" onClick={() => toast({ title: "Edit mode enabled" })}>
                  Edit
                </Button>
                {(flags.missing_fields?.length ?? 0) > 0 && (
                  <Button variant="outline" className="gap-2" onClick={handleExtract}>
                    <RefreshCw className="h-4 w-4" />
                    Re-run Repair
                  </Button>
                )}
              </div>
            </>
          )}
        </div>
      </div>
        </TabsContent>

        <TabsContent value="image" className="mt-0">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Medical Image</CardTitle>
                <p className="text-xs text-muted-foreground">
                  Upload an image for documentation support. For informational use only — not a diagnosis.
                </p>
              </CardHeader>
              <CardContent className="space-y-4">
                <input
                  type="file"
                  accept="image/*"
                  className="text-sm"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    setImageFile(f || null);
                    if (!f) setInterpretationResult(null);
                  }}
                />
                <Button
                  className="w-full gap-2"
                  onClick={handleInterpretImage}
                  disabled={!imageFile || interpreting}
                >
                  {interpreting ? <Loader2 className="h-4 w-4 animate-spin" /> : <ImagePlus className="h-4 w-4" />}
                  {interpreting ? "Interpreting…" : "Interpret Image"}
                </Button>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Interpretation</CardTitle>
                {interpretTimingMs > 0 && (
                  <p className="text-xs text-muted-foreground">{interpretTimingMs}ms</p>
                )}
              </CardHeader>
              <CardContent>
                {interpretationResult ? (
                  <p className="text-sm whitespace-pre-wrap">{interpretationResult}</p>
                ) : (
                  <p className="text-sm text-muted-foreground">Result will appear here after interpretation.</p>
                )}
                <p className="mt-4 text-xs text-muted-foreground border-t pt-3">
                  This output is for documentation only. It does not constitute medical advice or diagnosis.
                </p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="prescription" className="mt-0">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Prescription / Handwritten List</CardTitle>
                <p className="text-xs text-muted-foreground">
                  Upload an image of a prescription or medication list to extract medications.
                </p>
              </CardHeader>
              <CardContent className="space-y-4">
                <input
                  type="file"
                  accept="image/*"
                  className="text-sm"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    setRxImageFile(f || null);
                    if (!f) setRxMedications([]);
                  }}
                />
                <Button
                  className="w-full gap-2"
                  onClick={handlePrescriptionFromImage}
                  disabled={!rxImageFile || rxLoading}
                >
                  {rxLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
                  {rxLoading ? "Extracting…" : "Extract Medications"}
                </Button>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Extracted Medications</CardTitle>
                {rxTimingMs > 0 && (
                  <p className="text-xs text-muted-foreground">{rxTimingMs}ms</p>
                )}
              </CardHeader>
              <CardContent>
                {rxMedications.length > 0 ? (
                  <div className="space-y-2">
                    {rxMedications.map((m, i) => (
                      <div key={i} className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-sm">
                        <span>{m.name} {m.dose || ""} {m.frequency || ""} {m.route ? `(${m.route})` : ""}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Medications will appear here after extraction.</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <Label>{label}</Label>
      <p className="text-sm text-foreground">{value}</p>
    </div>
  );
}

function Label({ children }: { children: React.ReactNode }) {
  return <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">{children}</p>;
}
