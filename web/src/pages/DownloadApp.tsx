import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, Terminal, Shield, Copy, Check } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useState } from "react";

const steps = [
  { step: "1", title: "Install Docker Desktop", desc: "Download from docker.com and ensure Docker is running." },
  { step: "2", title: "Clone the repository", desc: "Open a terminal and run the commands below. This downloads the project to your machine." },
  { step: "3", title: "Start the local app", desc: "In the project folder run: docker compose up local-app (API + UI run in one container)." },
  { step: "4", title: "Open the app", desc: "In your browser go to http://localhost:8501" },
  { step: "5", title: "Use offline", desc: "Extraction works without internet. To test: once the app is open, disconnect the network. Sync resumes when connectivity returns." },
];

const REPO_URL = "https://github.com/arkhangio10/edgemed-agent";

export default function DownloadApp() {
  const { toast } = useToast();
  const [copied, setCopied] = useState(false);

  const cloneCommand = `git clone ${REPO_URL}.git\ncd edgemed-agent\ndocker compose up local-app`;

  const handleCopyCommand = async () => {
    try {
      await navigator.clipboard.writeText(cloneCommand);
      setCopied(true);
      toast({ title: "Commands copied to clipboard" });
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast({ title: "Could not copy — please select and copy manually", variant: "destructive" });
    }
  };

  const handleDownloadDocker = () => {
    // Same as repo: local-app (API + Streamlit) + optional cloud-api
    const dockerCompose = `# EdgeMed Agent — Docker Compose
# Place in project root after cloning. Run: docker compose up local-app
version: "3.9"

services:
  cloud-api:
    build:
      context: .
      dockerfile: cloud/Dockerfile
    ports:
      - "8080:8080"
    env_file:
      - .env
    environment:
      - PYTHONPATH=/app
    volumes:
      - ./shared:/app/shared

  local-app:
    build:
      context: .
      dockerfile: local/Dockerfile
    ports:
      - "8501:8501"
      - "8000:8000"
    volumes:
      - ./shared:/app/shared
      - ./local/keys:/app/local/keys
      - local-data:/app/local/data
    environment:
      - EDGEMED_CLOUD_API_URL=http://cloud-api:8080
      - EDGEMED_MODE=prod
      - EDGEMED_USE_MEDGEMMA_LOCAL=true
      - EDGEMED_MEDGEMMA_MODEL_ID=google/medgemma-1.5-4b-it
      - EDGEMED_MEDGEMMA_DEVICE=cpu
      - PYTHONPATH=/app

volumes:
  local-data:
`;

    const blob = new Blob([dockerCompose], { type: "text/yaml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "docker-compose.yml";
    a.click();
    URL.revokeObjectURL(url);
    toast({
      title: "docker-compose.yml downloaded",
      description: "Place it in the cloned repo root. Then run: docker compose up local-app",
    });
  };

  const handleDownloadNotes = () => {
    const notes = [
      {
        filename: "sample_en.txt",
        content: `Patient: Maria Gonzalez, 54F\nChief Complaint: "I've been having chest pain for the past 3 days"\nHPI: 54-year-old female presents with substernal chest pain, described as pressure-like, radiating to the left arm. Pain is worse with exertion and relieved by rest. No associated shortness of breath, nausea, or diaphoresis. Patient has a history of hypertension and type 2 diabetes.\nMedications: Metformin 1000mg BID, Lisinopril 20mg daily, Atorvastatin 40mg daily\nAllergies: Penicillin (rash)\nAssessment/Plan:\n1. Chest pain - rule out ACS. Order troponin, EKG, CXR. Start aspirin 325mg.\n2. Hypertension - poorly controlled. Increase lisinopril to 40mg daily.\n3. Diabetes - continue metformin. Check HbA1c.\nFollow-up in 1 week or sooner if symptoms worsen.`,
      },
      {
        filename: "sample_es.txt",
        content: `Paciente: María González, 54F\nMotivo de consulta: "He tenido dolor en el pecho durante los últimos 3 días"\nHistoria: Mujer de 54 años presenta dolor torácico subesternal, descrito como presión, irradiado al brazo izquierdo.\nMedicamentos: Metformina 1000mg BID, Lisinopril 20mg diario, Atorvastatina 40mg diario\nAlergias: Penicilina (erupción)\nPlan: Descartar SCA. Troponina, EKG, RX tórax. Aspirina 325mg.`,
      },
    ];

    // Download each as a separate text file
    notes.forEach((note) => {
      const blob = new Blob([note.content], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = note.filename;
      a.click();
      URL.revokeObjectURL(url);
    });
    toast({ title: "Demo notes downloaded", description: "2 sample clinical notes (EN + ES)" });
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h2 className="text-lg font-semibold text-foreground">Download Offline App</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Run EdgeMed Agent locally for full offline clinical documentation.
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <Button
          id="download-docker-btn"
          className="gap-2 bg-gradient-hero hover:opacity-90 text-primary-foreground"
          onClick={handleDownloadDocker}
        >
          <Download className="h-4 w-4" />
          Download docker-compose.yml
        </Button>
        <Button
          id="download-notes-btn"
          variant="outline"
          className="gap-2"
          onClick={handleDownloadNotes}
        >
          <Download className="h-4 w-4" />
          Download Demo Notes Bundle
        </Button>
      </div>
      <p className="text-xs text-muted-foreground">
        The repo already includes docker-compose.yml. Download the file above only if you want this config elsewhere. Run the terminal commands to clone and start the app.
      </p>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Setup Instructions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {steps.map((s) => (
            <div key={s.step} className="flex gap-4">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-sm font-bold">
                {s.step}
              </div>
              <div>
                <p className="font-medium text-foreground text-sm">{s.title}</p>
                <p className="text-sm text-muted-foreground">{s.desc}</p>
              </div>
            </div>
          ))}

          <div className="rounded-lg bg-muted p-4 relative group">
            <div className="flex items-center gap-2 mb-2">
              <Terminal className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs font-medium text-muted-foreground">Terminal</span>
              <Button
                variant="ghost"
                size="sm"
                className="ml-auto h-7 px-2 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={handleCopyCommand}
              >
                {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
              </Button>
            </div>
            <pre className="text-sm font-mono text-foreground">
              {`git clone ${REPO_URL}.git
cd edgemed-agent
docker compose up local-app`}
            </pre>
          </div>
        </CardContent>
      </Card>

      <Card className="border-amber-200/50 bg-amber-50/50 dark:border-amber-800/50 dark:bg-amber-950/20">
        <CardContent className="flex items-start gap-4 pt-6">
          <div>
            <p className="font-medium text-foreground text-sm">MedGemma on Hugging Face (gated)</p>
            <p className="text-sm text-muted-foreground mt-1">
              The local app uses MedGemma from Hugging Face. You must accept the Health AI Developer Foundation terms on the{" "}
              <a href="https://huggingface.co/google/medgemma-1.5-4b-it" target="_blank" rel="noopener noreferrer" className="underline">model page</a>
              {" "}and be logged in. For Docker, set your token: <code className="text-xs bg-muted px-1 rounded">HF_TOKEN=hf_... docker compose up local-app</code> or add <code className="text-xs bg-muted px-1 rounded">EDGEMED_HF_TOKEN</code> to your environment.
            </p>
          </div>
        </CardContent>
      </Card>

      <Card className="border-success/20 bg-success/5">
        <CardContent className="flex items-start gap-4 pt-6">
          <Shield className="h-5 w-5 text-success shrink-0" />
          <div>
            <p className="font-medium text-foreground text-sm">Offline Privacy</p>
            <p className="text-sm text-muted-foreground mt-1">
              When running locally, all processing happens on your machine. No clinical notes leave the device.
              MedGemma runs entirely on-device, and sync to the cloud is opt-in and encrypted end-to-end.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
