import { History, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { Button, buttonVariants } from "@/components/ui/button";
import { ConfirmDialog, EmptyState, ErrorPanel, PageSkeleton } from "@/components/ui/misc";
import { VerdictBadge } from "@/features/analysis/VerdictBadge";
import { useAsync } from "@/hooks/useAsync";
import { analysisApi, errorMessage } from "@/services/api";
import type { AnalysisSummary } from "@/types/api";
import { date, MODE_LABEL, pct } from "@/utils/format";

const PAGE_SIZE = 10;

export default function HistoryPage() {
  const [page, setPage] = useState(1);
  const { data, error, loading, reload } = useAsync(() => analysisApi.list(page, PAGE_SIZE), [page]);
  const [toDelete, setToDelete] = useState<AnalysisSummary | null>(null);

  const remove = async () => {
    if (!toDelete) return;
    try {
      await analysisApi.remove(toDelete.id);
      toast.success("Analysis deleted");
      setToDelete(null);
      if (data && data.items.length === 1 && page > 1) setPage(page - 1);
      else void reload();
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };

  if (loading && !data) return <PageSkeleton />;
  if (error || !data) return <ErrorPanel message={error ?? "Could not load history."} onRetry={reload} />;
  const pages = Math.max(1, Math.ceil(data.total / PAGE_SIZE));

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold">Analysis history</h1>
          <p className="mt-1 text-muted">{data.total} {data.total === 1 ? "analysis" : "analyses"}</p>
        </div>
        <Link to="/analyses/new" className={buttonVariants()}>New analysis</Link>
      </div>
      {data.total === 0 ? (
        <EmptyState icon={<History className="h-10 w-10" />} title="Nothing here yet" action={<Link to="/analyses/new" className={buttonVariants()}>Run an analysis</Link>}>
          Every analysis you run is saved here until you delete it or it passes your retention period.
        </EmptyState>
      ) : (
        <>
          <div className="overflow-x-auto rounded-xl border border-line bg-surface">
            <table className="w-full min-w-[48rem] text-left text-sm">
              <thead className="border-b border-line bg-paper text-xs text-muted">
                <tr>
                  <th className="px-4 py-2 font-semibold">Date</th><th className="px-4 py-2 font-semibold">Target role</th>
                  <th className="px-4 py-2 font-semibold">Coverage</th><th className="px-4 py-2 font-semibold">Skill coverage</th>
                  <th className="px-4 py-2 font-semibold">Method</th><th className="px-4 py-2"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((a) => (
                  <tr key={a.id} className="border-b border-line last:border-0">
                    <td className="px-4 py-3 whitespace-nowrap text-muted">{date(a.created_at)}</td>
                    <td className="px-4 py-3"><Link to={`/analyses/${a.id}`} className="font-semibold hover:text-pine hover:underline">{a.job_title || a.target_role || `Analysis ${a.id}`}</Link></td>
                    <td className="px-4 py-3 font-display text-lg font-bold tabular-nums">{pct(a.coverage_score, 1)}</td>
                    <td className="px-4 py-3"><span className="mr-2 tabular-nums">{a.direct_count}/{a.requirement_count}</span>{a.missing_count > 0 && <VerdictBadge verdict="missing" />} {a.missing_count > 0 && <span className="text-xs text-muted">{a.missing_count}</span>}</td>
                    <td className="px-4 py-3 text-muted">{MODE_LABEL[a.mode]}{a.fallback_used && <span className="block text-xs text-[#8a5c0a]">TF-IDF fallback used</span>}</td>
                    <td className="px-4 py-3 text-right">
                      <Button variant="ghost" size="icon" aria-label={`Delete analysis ${a.job_title ?? a.id}`} onClick={() => setToDelete(a)}><Trash2 className="h-4 w-4" /></Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {pages > 1 && (
            <nav aria-label="Pagination" className="mt-4 flex items-center justify-end gap-2 text-sm">
              <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</Button>
              <span className="tabular-nums text-muted">Page {page} of {pages}</span>
              <Button variant="secondary" size="sm" disabled={page >= pages} onClick={() => setPage(page + 1)}>Next</Button>
            </nav>
          )}
        </>
      )}
      <ConfirmDialog open={!!toDelete} title="Delete this analysis?" body="Its evidence, roadmap and stored resume text are removed permanently."
        confirmLabel="Delete analysis" onConfirm={remove} onCancel={() => setToDelete(null)} />
    </div>
  );
}
