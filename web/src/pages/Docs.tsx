import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

const faqs = [
  {
    q: "What is MedGemma used for?",
    a: "MedGemma is a medical-domain language model used to extract structured clinical information from free-text doctor notes. It identifies diagnoses, medications, allergies, plans, and red flags, outputting validated EHR-ready JSON.",
  },
  {
    q: "Privacy model: Demo vs Local",
    a: "In the web demo, synthetic notes are processed via a cloud API — no real patient data should ever be entered. In local mode, MedGemma runs entirely on-device inside a Docker container. Notes never leave the machine. Cloud sync is opt-in and encrypted.",
  },
  {
    q: "What data is stored?",
    a: "In demo mode, structured records are stored temporarily in the guest session and discarded on logout. No raw clinical notes are stored in analytics. In local mode, all data is stored on-device in a local SQLite database.",
  },
  {
    q: "Why offline-first?",
    a: "Clinical environments often have unreliable connectivity — rural clinics, ambulances, disaster response. Offline-first ensures documentation never stops. Records sync automatically when internet returns, with conflict resolution and audit trails.",
  },
  {
    q: "Limitations & safety boundaries",
    a: "EdgeMed Agent is a documentation assistant, not a diagnostic tool. It does not provide medical advice. Extraction accuracy depends on note quality. The copilot chatbot is grounded only on the extracted record and source note — it cannot access external medical knowledge. All outputs should be reviewed by a licensed clinician.",
  },
  {
    q: "What is HAI-DEF / MedGemma?",
    a: "MedGemma is a medical-domain AI model by Google, part of the Health AI Developer Foundations (HAI-DEF). It is provided under the HAI-DEF Terms of Use (https://developers.google.com/health-ai-developer-foundations/terms). Usage must comply with the Prohibited Use Policy (https://ai.google.dev/gemma/prohibited_use_policy). EdgeMed Agent uses MedGemma solely for clinical documentation assistance — never for diagnosis or treatment.",
  },
  {
    q: "What are the structured output fields?",
    a: "The extraction produces: patient demographics, chief complaint, HPI, diagnoses (with ICD-10 codes), medications, allergies, plan items, follow-up instructions, vitals, red flags, and a completeness score. Missing fields and contradictions are flagged automatically.",
  },
  {
    q: "How does rate limiting work?",
    a: "The cloud API enforces rate limiting at approximately 12 requests per minute per guest session. If exceeded, the UI displays a friendly 'Too many requests, please wait 30 seconds' message. This prevents abuse while allowing smooth demo workflows.",
  },
];

export default function Docs() {
  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h2 className="text-lg font-semibold text-foreground">Documentation & FAQ</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Everything you need to know about EdgeMed Agent.
        </p>
      </div>

      <Card className="border-warning/30 bg-warning/5">
        <CardContent className="pt-6">
          <p className="text-sm text-warning font-medium text-center">
            ⚠️ Documentation support only — not for diagnosis, treatment, or clinical decision-making. Does not substitute professional clinical judgment.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <Accordion type="single" collapsible className="w-full">
            {faqs.map((f, i) => (
              <AccordionItem key={i} value={`item-${i}`}>
                <AccordionTrigger className="text-sm font-medium text-left">
                  {f.q}
                </AccordionTrigger>
                <AccordionContent className="text-sm text-muted-foreground leading-relaxed">
                  {f.a}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </CardContent>
      </Card>
    </div>
  );
}
