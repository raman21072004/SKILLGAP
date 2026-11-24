import { motion } from "framer-motion";
import type { Classification } from "@/types/api";
import { VERDICT } from "@/utils/format";

export interface BarItem { skill: string; weight: number; verdict: Classification; importance?: string }

/**
 * The evidence bar: one segment per job requirement, width proportional to the
 * requirement's weight, colour = verdict. The share of the bar that is "shown"
 * is exactly the coverage score, so the formula is visible, not hidden.
 */
export function EvidenceBar({ items, height = 44, animate = true, onSelect }: { items: BarItem[]; height?: number; animate?: boolean; onSelect?: (skill: string) => void }) {
  const total = items.reduce((s, i) => s + i.weight, 0) || 1;
  const order: Classification[] = ["direct_match", "strong_semantic", "related", "missing"];
  const sorted = [...items].sort((a, b) => order.indexOf(a.verdict) - order.indexOf(b.verdict) || b.weight - a.weight);
  return (
    <div>
      <div className="flex w-full gap-[3px]" style={{ height }} role="list" aria-label="Requirements by verdict">
        {sorted.map((it, i) => (
          <motion.button
            type="button"
            role="listitem"
            key={it.skill}
            title={`${it.skill}: ${VERDICT[it.verdict].label} (weight ${it.weight})`}
            aria-label={`${it.skill}: ${VERDICT[it.verdict].label}`}
            onClick={() => onSelect?.(it.skill)}
            initial={animate ? { scaleY: 0 } : false}
            animate={{ scaleY: 1 }}
            transition={{ delay: animate ? i * 0.025 : 0, duration: 0.3 }}
            className="group relative min-w-[6px] origin-bottom rounded-[5px] outline-offset-2"
            style={{ flexGrow: it.weight / total, flexBasis: 0, background: VERDICT[it.verdict].color, opacity: it.importance === "nice_to_have" ? 0.62 : 1, cursor: onSelect ? "pointer" : "default" }}
          />
        ))}
      </div>
      <ul className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted">
        {order.map((v) => (
          <li key={v} className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-sm" style={{ background: VERDICT[v].color }} aria-hidden />
            {VERDICT[v].short} ({items.filter((i) => i.verdict === v).length})
          </li>
        ))}
        <li className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-ink/50" aria-hidden />Faded = nice to have</li>
      </ul>
    </div>
  );
}
