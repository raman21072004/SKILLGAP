import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown } from "lucide-react";
import { useState } from "react";
import type { Classification, Requirement } from "@/types/api";
import { cn } from "@/utils/cn";
import { num, SECTION_LABEL, VERDICT } from "@/utils/format";
import { VerdictBadge } from "./VerdictBadge";

export function RequirementRow({ req, onCorrect, onFocusEvidence, active }: {
  req: Requirement;
  onCorrect: (req: Requirement, value: Classification | null) => void;
  onFocusEvidence: (skill: string) => void;
  active: boolean;
}) {
  const [open, setOpen] = useState(false);
  const id = `req-${req.match_id}`;
  return (
    <li className={cn("border-b border-line last:border-0", active && "bg-paper")}>
      <button
        className="flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-paper"
        aria-expanded={open}
        aria-controls={id}
        onClick={() => { setOpen((o) => !o); if (req.evidence) onFocusEvidence(req.canonical); }}
      >
        <span className="h-8 w-1 shrink-0 rounded-full" style={{ background: VERDICT[req.effective_classification].color, opacity: req.importance === "nice_to_have" ? 0.6 : 1 }} aria-hidden />
        <span className="min-w-0 flex-1">
          <span className="block font-semibold">{req.canonical}</span>
          <span className="block text-xs text-muted">{req.category}, {req.importance === "must_have" ? "must have" : "nice to have"}, weight {req.weight}</span>
        </span>
        <VerdictBadge verdict={req.effective_classification} corrected={!!req.user_classification} />
        <ChevronDown className={cn("h-4 w-4 shrink-0 text-muted transition-transform", open && "rotate-180")} aria-hidden />
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div id={id} initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
            <div className="space-y-3 px-4 pb-4 pl-8 text-sm">
              <p>{req.explanation}</p>
              {req.evidence ? (
                <blockquote className="rounded-lg border-l-4 bg-paper px-3 py-2" style={{ borderColor: VERDICT[req.effective_classification].color }}>
                  <p className="text-xs font-semibold text-muted">
                    From your {SECTION_LABEL[req.evidence.section ?? "body"] ?? req.evidence.section} section
                    {req.evidence.kind !== "exact" && ` (${req.evidence.kind} evidence)`}
                  </p>
                  <p className="mt-1">“{req.evidence.text}”</p>
                </blockquote>
              ) : (
                <p className="text-muted">No supporting passage was found in the resume.</p>
              )}
              {req.uncertainty && <p className="text-xs text-[#8a5c0a]">Uncertainty: {req.uncertainty}</p>}
              <p><span className="font-semibold">Next step: </span>{req.next_action}</p>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-muted sm:grid-cols-4">
                <div><dt>Method</dt><dd className="text-ink">{req.method ?? "n/a"}</dd></div>
                <div><dt>TF-IDF cosine</dt><dd className="text-ink">{num(req.tfidf_similarity)}</dd></div>
                <div><dt>Semantic cosine</dt><dd className="text-ink">{num(req.semantic_similarity)}</dd></div>
                <div><dt>Job ad says</dt><dd className="truncate text-ink" title={req.requirement_text ?? ""}>{req.requirement_text ?? "n/a"}</dd></div>
              </dl>
              <div className="flex flex-wrap items-center gap-2">
                <label htmlFor={`fix-${req.match_id}`} className="text-xs font-semibold">Correct this result</label>
                <select
                  id={`fix-${req.match_id}`}
                  className="h-8 rounded-md border border-line bg-surface px-2 text-xs"
                  value={req.user_classification ?? ""}
                  onChange={(e) => onCorrect(req, (e.target.value || null) as Classification | null)}
                >
                  <option value="">System result ({VERDICT[req.classification].short})</option>
                  {(Object.keys(VERDICT) as Classification[]).filter((k) => k !== req.classification).map((k) => (
                    <option key={k} value={k}>{VERDICT[k].label}</option>
                  ))}
                </select>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </li>
  );
}
