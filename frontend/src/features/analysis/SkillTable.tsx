import { ArrowDownUp } from "lucide-react";
import { useMemo, useState } from "react";
import type { Classification, Requirement } from "@/types/api";
import { num, VERDICT } from "@/utils/format";
import { VerdictBadge } from "./VerdictBadge";

type SortKey = "canonical" | "category" | "weight" | "similarity" | "verdict";
const VERDICT_ORDER: Classification[] = ["missing", "related", "strong_semantic", "direct_match"];

export function filterRequirements(reqs: Requirement[], query: string, verdict: string, importance: string): Requirement[] {
  const q = query.trim().toLowerCase();
  return reqs.filter((r) =>
    (!q || r.canonical.toLowerCase().includes(q) || r.category.toLowerCase().includes(q) || (r.evidence?.text ?? "").toLowerCase().includes(q)) &&
    (verdict === "all" || r.effective_classification === verdict) &&
    (importance === "all" || r.importance === importance),
  );
}

export function SkillTable({ requirements }: { requirements: Requirement[] }) {
  const [query, setQuery] = useState("");
  const [verdict, setVerdict] = useState("all");
  const [importance, setImportance] = useState("all");
  const [sort, setSort] = useState<{ key: SortKey; dir: 1 | -1 }>({ key: "verdict", dir: 1 });

  const rows = useMemo(() => {
    const filtered = filterRequirements(requirements, query, verdict, importance);
    const val = (r: Requirement): string | number => {
      switch (sort.key) {
        case "canonical": return r.canonical.toLowerCase();
        case "category": return r.category;
        case "weight": return r.weight;
        case "similarity": return r.semantic_similarity ?? r.tfidf_similarity ?? 0;
        case "verdict": return VERDICT_ORDER.indexOf(r.effective_classification);
      }
    };
    return [...filtered].sort((a, b) => (val(a) > val(b) ? 1 : val(a) < val(b) ? -1 : 0) * sort.dir);
  }, [requirements, query, verdict, importance, sort]);

  const header = (key: SortKey, label: string) => (
    <th scope="col" className="py-2 pr-3 font-semibold" aria-sort={sort.key === key ? (sort.dir === 1 ? "ascending" : "descending") : "none"}>
      <button className="inline-flex items-center gap-1 hover:text-ink" onClick={() => setSort((s) => ({ key, dir: s.key === key ? (s.dir === 1 ? -1 : 1) : 1 }))}>
        {label} <ArrowDownUp className="h-3 w-3" aria-hidden />
      </button>
    </th>
  );

  return (
    <div>
      <div className="mb-4 grid gap-3 sm:grid-cols-[1fr_auto_auto]">
        <label className="sr-only" htmlFor="skill-search">Search skills</label>
        <input id="skill-search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search skill, category or evidence"
          className="h-10 rounded-lg border border-line bg-surface px-3 text-sm focus:border-pine focus:outline-none" />
        <label className="sr-only" htmlFor="verdict-filter">Filter by verdict</label>
        <select id="verdict-filter" value={verdict} onChange={(e) => setVerdict(e.target.value)} className="h-10 rounded-lg border border-line bg-surface px-3 text-sm">
          <option value="all">All verdicts</option>
          {(Object.keys(VERDICT) as Classification[]).map((k) => <option key={k} value={k}>{VERDICT[k].short}</option>)}
        </select>
        <label className="sr-only" htmlFor="importance-filter">Filter by importance</label>
        <select id="importance-filter" value={importance} onChange={(e) => setImportance(e.target.value)} className="h-10 rounded-lg border border-line bg-surface px-3 text-sm">
          <option value="all">Any importance</option>
          <option value="must_have">Must have</option>
          <option value="nice_to_have">Nice to have</option>
        </select>
      </div>
      <p className="mb-2 text-xs text-muted" aria-live="polite">{rows.length} of {requirements.length} requirements</p>
      <div className="overflow-x-auto rounded-xl border border-line bg-surface">
        <table className="w-full min-w-[56rem] text-left text-sm">
          <thead className="border-b border-line bg-paper text-xs text-muted">
            <tr>
              <th className="w-3" />
              {header("canonical", "Skill")}
              {header("category", "Category")}
              {header("weight", "Importance")}
              {header("verdict", "Status")}
              {header("similarity", "Similarity")}
              <th scope="col" className="py-2 pr-3 font-semibold">Resume evidence</th>
              <th scope="col" className="py-2 pr-3 font-semibold">Recommended action</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.match_id} className="border-b border-line align-top last:border-0">
                <td><span className="ml-2 mt-3 block h-6 w-1 rounded-full" style={{ background: VERDICT[r.effective_classification].color }} /></td>
                <td className="py-3 pr-3 font-semibold">{r.canonical}</td>
                <td className="py-3 pr-3 text-muted">{r.category}</td>
                <td className="py-3 pr-3">{r.importance === "must_have" ? "Must have" : "Nice to have"} <span className="text-muted">({r.weight})</span></td>
                <td className="py-3 pr-3"><VerdictBadge verdict={r.effective_classification} corrected={!!r.user_classification} /></td>
                <td className="py-3 pr-3 tabular-nums">{r.semantic_similarity !== null ? num(r.semantic_similarity) : num(r.tfidf_similarity)}</td>
                <td className="max-w-xs py-3 pr-3 text-muted">{r.evidence ? `“${r.evidence.text}”` : "None found"}</td>
                <td className="max-w-xs py-3 pr-3">{r.next_action}</td>
              </tr>
            ))}
            {!rows.length && (
              <tr><td colSpan={8} className="py-8 text-center text-muted">No requirements match these filters.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
