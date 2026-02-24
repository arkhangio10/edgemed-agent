import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type StatusVariant = "success" | "warning" | "error" | "info" | "neutral";

const variantStyles: Record<StatusVariant, string> = {
  success: "bg-success/10 text-success border-success/20 hover:bg-success/15",
  warning: "bg-warning/10 text-warning border-warning/20 hover:bg-warning/15",
  error: "bg-destructive/10 text-destructive border-destructive/20 hover:bg-destructive/15",
  info: "bg-info/10 text-info border-info/20 hover:bg-info/15",
  neutral: "bg-muted text-muted-foreground border-border hover:bg-muted/80",
};

export function StatusBadge({
  variant = "neutral",
  children,
  className,
}: {
  variant?: StatusVariant;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <Badge
      variant="outline"
      className={cn("font-medium text-xs", variantStyles[variant], className)}
    >
      {children}
    </Badge>
  );
}

export function ConfidenceBadge({ level }: { level: "low" | "medium" | "high" }) {
  const map: Record<string, StatusVariant> = { low: "error", medium: "warning", high: "success" };
  return <StatusBadge variant={map[level]}>{level}</StatusBadge>;
}
