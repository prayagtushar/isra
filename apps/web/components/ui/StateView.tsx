import type { LucideIcon } from "lucide-react";
import { Button } from "./Button";

export function StateView({
  icon: Icon,
  title,
  hint,
  action,
}: {
  icon?: LucideIcon;
  title: string;
  hint?: string;
  action?: { label: string; onClick: () => void };
}) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-20 text-center">
      {Icon && <Icon size={22} className="text-faint" />}
      <p className="mt-3 text-[14px] font-medium text-ink">{title}</p>
      {hint && <p className="mt-1 max-w-sm text-[13px] leading-relaxed text-muted">{hint}</p>}
      {action && (
        <Button variant="outline" size="sm" className="mt-4" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
}
