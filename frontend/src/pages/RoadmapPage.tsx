import { PartyPopper } from "lucide-react";
import { useState } from "react";
import { useParams } from "react-router-dom";
import { toast } from "sonner";
import { Card, CardBody } from "@/components/ui/card";
import { EmptyState, ErrorPanel, PageSkeleton, Progress } from "@/components/ui/misc";
import { AnalysisNav } from "@/features/analysis/AnalysisNav";
import { TaskCard } from "@/features/roadmap/TaskCard";
import { useAsync } from "@/hooks/useAsync";
import { analysisApi, errorMessage } from "@/services/api";
import type { Task, TaskStatus } from "@/types/api";
import { pct, STATUS_LABEL } from "@/utils/format";

export default function RoadmapPage() {
  const { id = "" } = useParams();
  const { data, setData, error, loading, reload } = useAsync(() => analysisApi.roadmap(id), [id]);
  const [busy, setBusy] = useState<number | null>(null);
  if (loading) return <PageSkeleton />;
  if (error || !data) return <ErrorPanel message={error ?? "Roadmap not found."} onRetry={reload} />;

  const save = async (task: Task, body: { status?: TaskStatus; checklist_done?: number[] }) => {
    setBusy(task.id);
    try {
      const res = await analysisApi.updateTask(task.id, body);
      setData({ ...data, tasks: data.tasks.map((t) => (t.id === task.id ? res.task : t)), progress: res.progress });
      if (body.status) toast.success(`${task.skill}: ${STATUS_LABEL[body.status]}`);
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setBusy(null);
    }
  };

  const toggle = (task: Task, i: number) => {
    const done = new Set(task.checklist_done);
    if (done.has(i)) done.delete(i);
    else done.add(i);
    void save(task, { checklist_done: [...done] });
  };

  return (
    <div>
      <AnalysisNav id={data.analysis_id} title={`Roadmap${data.target_role ? ` for ${data.target_role}` : ""}`} />
      {data.tasks.length === 0 ? (
        <EmptyState icon={<PartyPopper className="h-10 w-10" />} title="No gaps to close">Every requirement in this job ad is shown in your resume.</EmptyState>
      ) : (
        <>
          <Card className="mb-6">
            <CardBody className="grid gap-6 md:grid-cols-[1fr_auto] md:items-center">
              <div>
                <div className="flex items-baseline justify-between text-sm"><span className="font-semibold">Learning progress</span><span className="tabular-nums text-muted">{data.progress.by_status.completed} of {data.progress.total} completed</span></div>
                <Progress className="mt-2 h-3" value={data.progress.completed_percent} />
                <p className="mt-3 text-xs text-muted">{data.progress.note}</p>
              </div>
              <div className="rounded-lg bg-paper px-4 py-3 text-sm">
                <p className="text-muted">Verified resume coverage</p>
                <p className="font-display text-2xl font-bold text-pine">{pct(data.verified_coverage, 1)}</p>
              </div>
            </CardBody>
          </Card>
          <ol className="space-y-4">
            {data.tasks.map((t) => (
              <li key={t.id}><TaskCard task={t} busy={busy === t.id} onStatus={(s) => save(t, { status: s })} onToggle={(i) => toggle(t, i)} /></li>
            ))}
          </ol>
          <p className="mt-6 text-xs text-muted">{data.disclaimer}</p>
        </>
      )}
    </div>
  );
}
