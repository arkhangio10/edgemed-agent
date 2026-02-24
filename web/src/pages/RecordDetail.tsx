import { useParams, useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { usePatientStore } from "@/lib/patient-store";
import { MOCK_RECORD, MOCK_FLAGS } from "@/lib/mock-data";
import type { ClinicalRecord, Flags } from "@/lib/types";
import { ArrowLeft, Download, Trash2, Copy, Check } from "lucide-react";
import { StatusBadge, ConfidenceBadge } from "@/components/StatusBadge";
import { useToast } from "@/hooks/use-toast";
import { useState } from "react";

export default function RecordDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [copied, setCopied] = useState(false);
  const { records } = usePatientStore();

  const stored = records.find((r) => r.id === id);
  const record: ClinicalRecord = (stored?.extractedData as ClinicalRecord) || MOCK_RECORD;
  const flags: Flags = (stored?.safetyFlags as Flags) || MOCK_FLAGS;

  const completenessPercent = Math.round(
    typeof flags.completeness_score === "number" && flags.completeness_score <= 1
      ? flags.completeness_score * 100
      : flags.completeness_score
  );

  const copyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(record, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-4 max-w-4xl">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate("/app/records")} className="gap-1">
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
        <h2 className="text-lg font-semibold text-foreground">
          Record: {id && id.length > 20 ? `${id.slice(0, 20)}...` : id}
        </h2>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Structured Record</CardTitle>
            <StatusBadge variant="success">{completenessPercent}% complete</StatusBadge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {record.chief_complaint && <Field label="Chief Complaint" value={record.chief_complaint} />}
          {record.hpi && <Field label="HPI" value={record.hpi} />}
          {record.assessment.length > 0 && (
            <div>
              <Label>Assessment / Diagnoses</Label>
              {record.assessment.map((d, i) => (
                <div key={i} className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-sm mt-1">
                  <span>
                    {d.description}
                    {d.icd10 && <span className="text-muted-foreground"> ({d.icd10})</span>}
                  </span>
                  {d.confidence && <ConfidenceBadge level={d.confidence} />}
                </div>
              ))}
            </div>
          )}
          {record.medications.length > 0 && (
            <div>
              <Label>Medications</Label>
              {record.medications.map((m, i) => (
                <div key={i} className="rounded-md border border-border px-3 py-2 text-sm mt-1">
                  {m.name} {m.dose || ""} {m.frequency || ""}{" "}
                  {m.status && <span className="text-muted-foreground">— {m.status}</span>}
                </div>
              ))}
            </div>
          )}
          {record.allergies.length > 0 && (
            <Field
              label="Allergies"
              value={record.allergies.map((a) => `${a.substance}${a.reaction ? ` (${a.reaction})` : ""}`).join(", ")}
            />
          )}
          {record.plan && (
            <div>
              <Label>Plan</Label>
              <p className="text-sm whitespace-pre-wrap">{record.plan}</p>
            </div>
          )}
          {record.follow_up && <Field label="Follow-up" value={record.follow_up} />}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Raw JSON</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <Button variant="ghost" size="sm" className="absolute right-2 top-2" onClick={copyJson}>
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            </Button>
            <pre className="max-h-[300px] overflow-auto rounded-lg bg-muted p-4 text-xs font-mono">
              {JSON.stringify(record, null, 2)}
            </pre>
          </div>
        </CardContent>
      </Card>

      <div className="flex gap-2">
        <Button variant="outline" className="gap-2" onClick={() => { copyJson(); toast({ title: "JSON exported to clipboard" }); }}>
          <Download className="h-4 w-4" />
          Export JSON
        </Button>
        <Button variant="outline" className="gap-2" onClick={() => toast({ title: "FHIR export coming soon" })}>
          Export FHIR-ready
        </Button>
        <Button
          variant="outline"
          className="gap-2 text-destructive hover:text-destructive"
          onClick={() => { toast({ title: "Record deleted (demo)" }); navigate("/app/records"); }}
        >
          <Trash2 className="h-4 w-4" />
          Delete
        </Button>
      </div>
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
