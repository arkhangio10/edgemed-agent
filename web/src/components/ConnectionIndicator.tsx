import { useState, useEffect } from "react";
import { Wifi, WifiOff } from "lucide-react";
import { healthCheck } from "@/lib/api";

export function ConnectionIndicator() {
  const [online, setOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setOnline(true);
    const handleOffline = () => setOnline(false);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    healthCheck()
      .then(() => setOnline(true))
      .catch(() => setOnline(navigator.onLine));

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  return (
    <div
      className={`flex items-center gap-1.5 text-xs font-medium ${online ? "text-success" : "text-destructive"}`}
      aria-label={`Connection status: ${online ? "Online" : "Offline"}`}
    >
      {online ? <Wifi className="h-3.5 w-3.5" /> : <WifiOff className="h-3.5 w-3.5" />}
      <span>{online ? "Online" : "Offline"}</span>
    </div>
  );
}
