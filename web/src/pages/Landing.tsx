import { Link } from "react-router-dom";
import { Shield, WifiOff, CheckCircle, ArrowRight, FileText, Cpu, Cloud } from "lucide-react";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import edgemedLogo from "@/assets/edgemed-logo.svg";

const benefits = [
  {
    icon: Shield,
    title: "Privacy-First",
    desc: "Local processing keeps sensitive data on-device. Nothing leaves the machine.",
  },
  {
    icon: WifiOff,
    title: "Works Without Internet",
    desc: "Full extraction works offline with the downloadable local app.",
  },
  {
    icon: CheckCircle,
    title: "Structured & Validated",
    desc: "Outputs validated EHR-ready JSON with safety flags and completeness scores.",
  },
];

const steps = [
  { icon: FileText, label: "Paste clinical note", detail: "Free-text or dictation" },
  { icon: Cpu, label: "MedGemma extracts", detail: "Structured fields + flags" },
  { icon: Cloud, label: "Sync when ready", detail: "Offline-first, cloud-optional" },
];

const fade = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.1, duration: 0.5 } }),
};

export default function Landing() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-20">
        <div className="container flex h-14 items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <img src={edgemedLogo} alt="EdgeMed" className="h-10 w-10 rounded-lg object-contain" />
            <span className="font-semibold text-foreground">EdgeMed Agent</span>
          </Link>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" asChild>
              <Link to="/docs">Docs</Link>
            </Button>
            <Button size="sm" asChild>
              <Link to="/auth">Try Demo</Link>
            </Button>
          </div>
        </div>
      </header>

      <section className="relative py-20 md:py-28 text-center overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent" />
        <div className="relative z-10 container">
          <motion.div initial="hidden" animate="visible" variants={fade} custom={0.5}>
            <span className="inline-block rounded-full border border-border bg-muted px-3 py-1 text-xs font-medium text-muted-foreground mb-6">
              Built for Doctors · Powered by MedGemma · Offline-first
            </span>
          </motion.div>
          <motion.h1
            className="text-4xl md:text-6xl font-bold tracking-tight text-foreground max-w-3xl mx-auto leading-[1.1]"
            initial="hidden" animate="visible" variants={fade} custom={1}
          >
            Your AI clinical documentation{" "}
            <span className="text-gradient-hero">assistant</span>
          </motion.h1>
          <motion.p
            className="mt-6 text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto"
            initial="hidden" animate="visible" variants={fade} custom={2}
          >
            Paste your clinical note → Get structured EHR records → Sync securely when ready
          </motion.p>
          <motion.div
            className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-3"
            initial="hidden" animate="visible" variants={fade} custom={3}
          >
            <Button size="lg" asChild className="bg-gradient-hero hover:opacity-90 text-primary-foreground gap-2">
              <Link to="/auth">
                Try Live Demo
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link to="/download">Download Offline App</Link>
            </Button>
          </motion.div>
        </div>
      </section>

      <section className="container pb-20">
        <div className="grid gap-6 md:grid-cols-3">
          {benefits.map((b, i) => (
            <motion.div
              key={b.title}
              className="rounded-xl border border-border bg-card p-6"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              variants={fade}
              custom={i}
            >
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <b.icon className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-semibold text-foreground">{b.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground leading-relaxed">{b.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="bg-surface-elevated border-y border-border py-20">
        <div className="container text-center">
          <h2 className="text-2xl font-bold text-foreground mb-12">How it works</h2>
          <div className="flex flex-col md:flex-row items-center justify-center gap-4 md:gap-0">
            {steps.map((s, i) => (
              <div key={s.label} className="flex items-center">
                <motion.div
                  className="flex flex-col items-center gap-3 px-6"
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true }}
                  variants={fade}
                  custom={i}
                >
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                    <s.icon className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="font-semibold text-foreground text-sm">{s.label}</p>
                    <p className="text-xs text-muted-foreground">{s.detail}</p>
                  </div>
                </motion.div>
                {i < steps.length - 1 && (
                  <ArrowRight className="hidden md:block h-5 w-5 text-border mx-2" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="container py-12">
        <div className="rounded-lg border border-warning/30 bg-warning/5 p-4 text-center">
          <p className="text-sm text-warning font-medium">
            Demo uses synthetic notes only. Not for real patient data.
          </p>
        </div>
      </section>

      <footer className="border-t border-border py-8">
        <div className="container space-y-3 text-center text-xs text-muted-foreground">
          <p className="font-medium text-warning">
            Documentation support only — not for diagnosis, treatment, or clinical decision-making. Does not substitute professional clinical judgment.
          </p>
          <p>
            EdgeMed Agent · Offline-first Clinical Documentation ·{" "}
            <a
              href="https://developers.google.com/health-ai-developer-foundations"
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:text-foreground transition-colors"
            >
              MedGemma / HAI-DEF by Google
            </a>{" "}
            ·{" "}
            <a
              href="https://developers.google.com/health-ai-developer-foundations/terms"
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:text-foreground transition-colors"
            >
              HAI-DEF Terms of Use
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}
