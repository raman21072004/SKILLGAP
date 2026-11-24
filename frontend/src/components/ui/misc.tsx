import * as React from "react";
import { cn } from "@/utils/cn";

export function Badge({ className, style, children }: { className?: string; style?: React.CSSProperties; children: React.ReactNode }) {
  return <span className={cn("inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-semibold", className)} style={style}>{children}</span>;
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-lg bg-line/70", className)} aria-hidden />;
}

export function PageSkeleton() {
  return (
    <div className="space-y-4" aria-busy="true" aria-label="Loading">
      <Skeleton className="h-9 w-64" />
      <div className="grid gap-4 md:grid-cols-3">
        <Skeleton className="h-28" /><Skeleton className="h-28" /><Skeleton className="h-28" />
      </div>
      <Skeleton className="h-72" />
    </div>
  );
}

export function Progress({ value, className, color = "var(--color-pine)" }: { value: number; className?: string; color?: string }) {
  const v = Math.max(0, Math.min(100, value));
  return (
    <div className={cn("h-2 w-full overflow-hidden rounded-full bg-line", className)} role="progressbar" aria-valuenow={Math.round(v)} aria-valuemin={0} aria-valuemax={100}>
      <div className="h-full rounded-full transition-[width] duration-500" style={{ width: `${v}%`, background: color }} />
    </div>
  );
}

export function EmptyState({ icon, title, children, action }: { icon?: React.ReactNode; title: string; children?: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center rounded-xl border border-dashed border-line bg-surface px-6 py-12 text-center">
      {icon && <div className="mb-3 text-pine">{icon}</div>}
      <h3 className="text-lg font-bold">{title}</h3>
      {children && <p className="mt-1 max-w-md text-sm text-muted">{children}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function ErrorPanel({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="rounded-xl border border-missing/30 bg-missing-soft p-5 text-sm">
      <p className="font-semibold text-missing">{message}</p>
      {onRetry && <button onClick={onRetry} className="mt-2 font-semibold text-ink underline">Try again</button>}
    </div>
  );
}

export function Notice({ tone = "info", children }: { tone?: "info" | "warn"; children: React.ReactNode }) {
  return (
    <div className={cn("rounded-lg border px-4 py-3 text-sm", tone === "warn" ? "border-verify/40 bg-verify-soft text-[#6b4708]" : "border-line bg-paper text-muted")}>
      {children}
    </div>
  );
}

export function Tabs<T extends string>({ tabs, value, onChange, label }: { tabs: { value: T; label: string }[]; value: T; onChange: (v: T) => void; label: string }) {
  const refs = React.useRef<(HTMLButtonElement | null)[]>([]);
  const onKey = (e: React.KeyboardEvent, i: number) => {
    const dir = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
    if (!dir) return;
    const next = (i + dir + tabs.length) % tabs.length;
    onChange(tabs[next].value);
    refs.current[next]?.focus();
  };
  return (
    <div role="tablist" aria-label={label} className="flex gap-1 overflow-x-auto rounded-lg border border-line bg-surface p-1">
      {tabs.map((t, i) => (
        <button
          key={t.value}
          ref={(el) => { refs.current[i] = el; }}
          role="tab"
          aria-selected={value === t.value}
          tabIndex={value === t.value ? 0 : -1}
          onKeyDown={(e) => onKey(e, i)}
          onClick={() => onChange(t.value)}
          className={cn("whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-semibold transition-colors",
            value === t.value ? "bg-pine text-white" : "text-muted hover:bg-paper hover:text-ink")}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

export function ConfirmDialog({ open, title, body, confirmLabel, onConfirm, onCancel, danger = true, children }: {
  open: boolean; title: string; body: string; confirmLabel: string; onConfirm: () => void; onCancel: () => void; danger?: boolean; children?: React.ReactNode;
}) {
  const ref = React.useRef<HTMLDialogElement>(null);
  React.useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) {
      if (typeof d.showModal === "function") d.showModal();
      else d.setAttribute("open", "");
    }
    if (!open && d.open) {
      if (typeof d.close === "function") d.close();
      else d.removeAttribute("open");
    }
  }, [open]);
  return (
    <dialog ref={ref} onCancel={(e) => { e.preventDefault(); onCancel(); }} className="m-auto w-[min(92vw,28rem)] rounded-xl border border-line bg-surface p-0 text-ink backdrop:bg-ink/40">
      <div className="p-6">
        <h2 className="text-lg font-bold">{title}</h2>
        <p className="mt-2 text-sm text-muted">{body}</p>
        {children}
        <div className="mt-6 flex justify-end gap-2">
          <button onClick={onCancel} className="h-10 rounded-lg border border-line px-4 text-sm font-semibold hover:bg-paper">Cancel</button>
          <button onClick={onConfirm} className={cn("h-10 rounded-lg px-4 text-sm font-semibold text-white", danger ? "bg-missing" : "bg-pine")}>{confirmLabel}</button>
        </div>
      </div>
    </dialog>
  );
}
