import type { Classification } from "@/types/api";
import { VERDICT } from "@/utils/format";

export function VerdictBadge({ verdict, corrected = false }: { verdict: Classification; corrected?: boolean }) {
  const v = VERDICT[verdict];
  return (
    <span className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-md px-2 py-0.5 text-xs font-semibold" style={{ background: v.soft, color: v.color }}>
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: v.color }} aria-hidden />
      {v.short}
      {corrected && <span className="font-medium opacity-80">(your edit)</span>}
    </span>
  );
}
