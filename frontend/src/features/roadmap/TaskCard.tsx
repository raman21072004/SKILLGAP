import { ExternalLink } from "lucide-react";
import type { Task, TaskStatus } from "@/types/api";
import { cn } from "@/utils/cn";
import { STATUS_LABEL } from "@/utils/format";
import { VerdictBadge } from "@/features/analysis/VerdictBadge";

const PRIORITY_STYLE = { high: "bg-missing-soft text-missing", medium: "bg-verify-soft text-[#8a5c0a]", low: "bg-paper text-muted" };

export function TaskCard({ task, onStatus, onToggle, busy }: { task: Task; onStatus: (s: TaskStatus) => void; onToggle: (index: number) => void; busy: boolean }) {
  const done = new Set(task.checklist_done);
  return (
    <article className={cn("rounded-xl border border-line bg-surface p-5", task.status === "completed" && "opacity-75")}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-pine-soft text-sm font-bold text-pine" aria-label={`Step ${task.order}`}>{task.order}</span>
          <div>
            <h3 className="text-lg font-bold">{task.skill}</h3>
            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs">
              <span className={cn("rounded-md px-2 py-0.5 font-semibold capitalize", PRIORITY_STYLE[task.priority])}>{task.priority} priority</span>
              <VerdictBadge verdict={task.gap_type} />
              <span className="text-muted capitalize">{task.level} level</span>
            </div>
          </div>
        </div>
        <label className="flex items-center gap-2 text-sm">
          <span className="sr-only">Status for {task.skill}</span>
          <select value={task.status} disabled={busy} onChange={(e) => onStatus(e.target.value as TaskStatus)} className="h-9 rounded-lg border border-line bg-surface px-2 text-sm font-semibold">
            {(Object.keys(STATUS_LABEL) as TaskStatus[]).map((s) => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}
          </select>
        </label>
      </div>

      <p className="mt-4 text-sm">{task.reason}</p>

      <div className="mt-4 grid gap-5 md:grid-cols-2">
        <div className="space-y-3 text-sm">
          {task.prerequisites.length > 0 && (
            <div>
              <h4 className="font-semibold">Prerequisites</h4>
              <ul className="mt-1 space-y-0.5 text-muted">
                {task.prerequisites.map((p) => <li key={p.skill}>{p.skill}: <span className={p.status === "demonstrated" ? "text-pine" : ""}>{p.status}</span></li>)}
              </ul>
            </div>
          )}
          <div><h4 className="font-semibold">Practice project</h4><p className="mt-1 text-muted">{task.project}</p></div>
          <div><h4 className="font-semibold">Estimated effort</h4><p className="mt-1 text-muted">{task.estimated_effort}</p></div>
          <div>
            <h4 className="font-semibold">Suggested resources</h4>
            {task.resources.length ? (
              <ul className="mt-1 space-y-1">
                {task.resources.map((r) => (
                  <li key={r.url}><a href={r.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-pine hover:underline">{r.title}<ExternalLink className="h-3 w-3" aria-hidden /></a> <span className="text-xs text-muted">({r.type})</span></li>
                ))}
              </ul>
            ) : <p className="mt-1 text-muted">{task.resources_note}</p>}
          </div>
        </div>
        <fieldset>
          <legend className="text-sm font-semibold">Checklist</legend>
          <ul className="mt-2 space-y-2">
            {task.checklist.map((item, i) => (
              <li key={i}>
                <label className="flex cursor-pointer items-start gap-2 text-sm">
                  <input type="checkbox" className="mt-0.5 h-4 w-4 accent-[var(--color-pine)]" checked={done.has(i)} disabled={busy} onChange={() => onToggle(i)} />
                  <span className={done.has(i) ? "text-muted line-through" : ""}>{item}</span>
                </label>
              </li>
            ))}
          </ul>
        </fieldset>
      </div>
    </article>
  );
}
