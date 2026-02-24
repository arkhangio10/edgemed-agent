import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/StatusBadge";
import { chatWithCopilot } from "@/lib/api";
import { usePatientStore } from "@/lib/patient-store";
import { MOCK_RECORD } from "@/lib/mock-data";
import type { ClinicalRecord } from "@/lib/types";
import { Send, AlertTriangle, Bot, User } from "lucide-react";

const STARTERS = [
  "What's missing before I finalize?",
  "Rewrite the plan in clean clinical format",
  "Generate SBAR referral summary",
  "Generate patient instructions (simple Spanish)",
];

interface Message {
  role: "user" | "assistant";
  content: string;
  grounded?: string;
}

export default function CopilotChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { selectedPatientId, records } = usePatientStore();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  const getCurrentRecord = (): ClinicalRecord | null => {
    if (selectedPatientId) {
      const patientRecs = records.filter((r) => r.patientId === selectedPatientId);
      if (patientRecs.length > 0) {
        return patientRecs[patientRecs.length - 1].extractedData as ClinicalRecord;
      }
    }
    return null;
  };

  const send = async (text: string) => {
    const userMsg: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setTyping(true);

    const record = getCurrentRecord() || MOCK_RECORD;
    const noteId = `chat-${Date.now()}`;

    try {
      const resp = await chatWithCopilot(noteId, text, record);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: resp.answer,
          grounded: resp.grounded_on.join(" + ") || "Record",
        },
      ]);
    } catch (err) {
      console.warn("Chat API unavailable, using fallback:", err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "I can help with that. Based on the current record, here is what I found. However, some information is **not documented / unknown** in the current note. Could you provide more details about the patient's social history and immunization status?\n\n*(API currently unavailable — this is a demo response)*",
          grounded: "JSON Record (demo)",
        },
      ]);
    } finally {
      setTyping(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div className="flex items-start gap-2 rounded-lg border border-warning/30 bg-warning/5 p-3">
        <AlertTriangle className="h-4 w-4 text-warning shrink-0 mt-0.5" />
        <p className="text-xs text-warning">
          This assistant is for documentation support only. Not for diagnosis or clinical decision-making.
        </p>
      </div>

      <Card className="flex flex-col" style={{ minHeight: "500px" }}>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Clinician Copilot</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-1 flex-col">
          <div className="flex-1 space-y-4 overflow-y-auto mb-4">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full gap-4 py-8">
                <Bot className="h-10 w-10 text-muted-foreground/40" />
                <p className="text-sm text-muted-foreground text-center">
                  Ask me about the extracted record. I can help you finalize documentation.
                </p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {STARTERS.map((s) => (
                    <Button key={s} variant="outline" size="sm" className="text-xs" onClick={() => send(s)}>
                      {s}
                    </Button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`flex gap-3 ${m.role === "user" ? "justify-end" : ""}`}>
                {m.role === "assistant" && (
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                    <Bot className="h-4 w-4" />
                  </div>
                )}
                <div
                  className={`max-w-[80%] rounded-xl px-4 py-3 text-sm ${
                    m.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-foreground"
                  }`}
                >
                  <div className="whitespace-pre-wrap">{m.content}</div>
                  {m.grounded && (
                    <div className="mt-2">
                      <StatusBadge variant="info">Grounded on: {m.grounded}</StatusBadge>
                    </div>
                  )}
                </div>
                {m.role === "user" && (
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))}
            {typing && (
              <div className="flex gap-3">
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="rounded-xl bg-muted px-4 py-3">
                  <div className="flex gap-1">
                    <span className="h-2 w-2 rounded-full bg-muted-foreground/40 animate-pulse" />
                    <span className="h-2 w-2 rounded-full bg-muted-foreground/40 animate-pulse" style={{ animationDelay: "0.2s" }} />
                    <span className="h-2 w-2 rounded-full bg-muted-foreground/40 animate-pulse" style={{ animationDelay: "0.4s" }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="flex gap-2">
            <Input
              placeholder="Ask about the record..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && input.trim() && !typing && send(input)}
              aria-label="Chat input"
            />
            <Button
              size="icon"
              className="bg-gradient-hero hover:opacity-90 text-primary-foreground shrink-0"
              onClick={() => input.trim() && send(input)}
              disabled={typing}
              aria-label="Send message"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
