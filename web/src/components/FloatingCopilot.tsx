import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/StatusBadge";
import { chatWithCopilot } from "@/lib/api";
import { usePatientStore } from "@/lib/patient-store";
import { MOCK_RECORD } from "@/lib/mock-data";
import type { ClinicalRecord } from "@/lib/types";
import { Send, Bot, User, X, MessageSquare } from "lucide-react";
import { cn } from "@/lib/utils";

const STARTERS = [
  "What's missing before I finalize?",
  "Rewrite the plan in clean clinical format",
  "Generate SBAR referral summary",
];

interface Message {
  role: "user" | "assistant";
  content: string;
  grounded?: string;
}

export default function FloatingCopilot() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { selectedPatientId, records } = usePatientStore();

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, typing]);

  const getCurrentRecord = (): ClinicalRecord => {
    if (selectedPatientId) {
      const patientRecs = records.filter((r) => r.patientId === selectedPatientId);
      if (patientRecs.length > 0) {
        return patientRecs[patientRecs.length - 1].extractedData as ClinicalRecord;
      }
    }
    return MOCK_RECORD;
  };

  const send = async (text: string) => {
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setTyping(true);

    try {
      const resp = await chatWithCopilot(`float-${Date.now()}`, text, getCurrentRecord());
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: resp.answer, grounded: resp.grounded_on.join(" + ") || "Record" },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "I can help with that. Based on the current record, some information is **not documented**. Could you provide more details?",
          grounded: "JSON Record (demo)",
        },
      ]);
    } finally {
      setTyping(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setOpen(!open)}
        className={cn(
          "fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full shadow-lg transition-all hover:scale-105",
          "bg-gradient-hero text-primary-foreground"
        )}
        aria-label="Open Copilot Chat"
      >
        {open ? <X className="h-6 w-6" /> : <MessageSquare className="h-6 w-6" />}
      </button>

      {open && (
        <div className="fixed bottom-24 right-6 z-50 flex w-[380px] max-h-[500px] flex-col rounded-xl border border-border bg-card shadow-2xl">
          <div className="flex items-center justify-between border-b border-border px-4 py-3">
            <div className="flex items-center gap-2">
              <Bot className="h-5 w-5 text-primary" />
              <span className="font-semibold text-sm text-foreground">Clinician Copilot</span>
            </div>
            <StatusBadge variant="info">Documentation only</StatusBadge>
          </div>

          <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-3" style={{ maxHeight: 340 }}>
            {messages.length === 0 && (
              <div className="flex flex-col items-center gap-3 py-6">
                <Bot className="h-8 w-8 text-muted-foreground/40" />
                <p className="text-xs text-muted-foreground text-center">Ask about the extracted record</p>
                <div className="flex flex-wrap gap-1.5 justify-center">
                  {STARTERS.map((s) => (
                    <Button key={s} variant="outline" size="sm" className="text-[10px] h-7" onClick={() => send(s)}>
                      {s}
                    </Button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`flex gap-2 ${m.role === "user" ? "justify-end" : ""}`}>
                {m.role === "assistant" && (
                  <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                    <Bot className="h-3 w-3" />
                  </div>
                )}
                <div className={cn("max-w-[80%] rounded-lg px-3 py-2 text-xs", m.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted text-foreground")}>
                  <div className="whitespace-pre-wrap">{m.content}</div>
                  {m.grounded && (
                    <div className="mt-1">
                      <StatusBadge variant="info">Grounded: {m.grounded}</StatusBadge>
                    </div>
                  )}
                </div>
                {m.role === "user" && (
                  <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
                    <User className="h-3 w-3" />
                  </div>
                )}
              </div>
            ))}
            {typing && (
              <div className="flex gap-2">
                <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <Bot className="h-3 w-3" />
                </div>
                <div className="rounded-lg bg-muted px-3 py-2">
                  <div className="flex gap-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/40 animate-pulse" />
                    <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/40 animate-pulse" style={{ animationDelay: "0.2s" }} />
                    <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/40 animate-pulse" style={{ animationDelay: "0.4s" }} />
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="border-t border-border p-3 flex gap-2">
            <Input
              placeholder="Ask about the record..."
              className="text-xs h-8"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && input.trim() && !typing && send(input)}
            />
            <Button
              size="icon"
              className="h-8 w-8 bg-gradient-hero hover:opacity-90 text-primary-foreground shrink-0"
              onClick={() => input.trim() && send(input)}
              disabled={typing}
            >
              <Send className="h-3 w-3" />
            </Button>
          </div>
        </div>
      )}
    </>
  );
}
