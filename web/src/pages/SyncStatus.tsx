import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/StatusBadge";
import { MOCK_SYNC_EVENTS } from "@/lib/mock-data";
import { healthCheck } from "@/lib/api";
import { RefreshCw, Cloud, HardDrive, ArrowRight, Wifi, WifiOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";

const statusVariant = (s: string) => {
  if (s === "synced") return "success";
  if (s === "queued") return "info";
  if (s === "failed") return "error";
  return "warning";
};

export default function SyncStatus() {
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [checking, setChecking] = useState(false);
  const { toast } = useToast();

  const checkApi = async () => {
    setChecking(true);
    try {
      await healthCheck();
      setApiOnline(true);
    } catch {
      setApiOnline(false);
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    checkApi();
  }, []);

  return (
    <div className="space-y-6 max-w-4xl">
      <h2 className="text-lg font-semibold text-foreground">Sync Status</h2>

      <Card className="border-primary/20 bg-primary/5">
        <CardContent className="flex items-start gap-4 pt-6">
          <div className="flex items-center gap-2 text-primary">
            <HardDrive className="h-5 w-5" />
            <ArrowRight className="h-4 w-4" />
            <Cloud className="h-5 w-5" />
          </div>
          <div>
            <p className="font-medium text-foreground text-sm">Offline-First Architecture</p>
            <p className="text-sm text-muted-foreground mt-1">
              In the local app, records are processed and stored on-device first. When internet connectivity returns,
              they sync automatically to the cloud. This ensures clinical workflows are never interrupted by network issues.
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Cloud API Status</CardTitle>
            <Button variant="outline" size="sm" className="gap-2" onClick={checkApi} disabled={checking}>
              <RefreshCw className={`h-3 w-3 ${checking ? "animate-spin" : ""}`} />
              Check
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3">
            {apiOnline === null ? (
              <span className="text-sm text-muted-foreground">Checking...</span>
            ) : apiOnline ? (
              <div className="flex items-center gap-2 text-success">
                <Wifi className="h-4 w-4" />
                <span className="text-sm font-medium">Cloud API is online</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-destructive">
                <WifiOff className="h-4 w-4" />
                <span className="text-sm font-medium">Cloud API unreachable</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4 text-primary" />
            <CardTitle className="text-base">Sync Queue (Simulated)</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {MOCK_SYNC_EVENTS.map((e) => (
              <div key={e.id} className="flex items-center justify-between rounded-lg border border-border px-4 py-3">
                <div className="flex items-center gap-3">
                  <StatusBadge variant={statusVariant(e.status) as any}>{e.status}</StatusBadge>
                  <span className="text-sm font-medium text-foreground">{e.record_id}</span>
                </div>
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  {e.latency_ms && <span>{e.latency_ms}ms</span>}
                  <span>{new Date(e.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">How Sync Works</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-muted-foreground">
          <p><strong className="text-foreground">1. Local Processing:</strong> MedGemma runs on your device. Notes are extracted into structured JSON without any network calls.</p>
          <p><strong className="text-foreground">2. Queue:</strong> Extracted records enter a local queue. Each record is assigned a sync status: queued → syncing → synced / failed.</p>
          <p><strong className="text-foreground">3. Auto-Sync:</strong> When connectivity is detected, the agent syncs records to the cloud in order. Failed syncs retry automatically with exponential backoff.</p>
          <p><strong className="text-foreground">4. Conflict Resolution:</strong> Server-side timestamps ensure no data is overwritten. Conflicts are flagged for clinician review.</p>
        </CardContent>
      </Card>
    </div>
  );
}
