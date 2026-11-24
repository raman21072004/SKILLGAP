import { FileSearch } from "lucide-react";
import { Link } from "react-router-dom";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { EmptyState, ErrorPanel, PageSkeleton, Progress } from "@/components/ui/misc";
import { useAsync } from "@/hooks/useAsync";
import { analysisApi } from "@/services/api";
import { useAuth } from "@/store/auth";
import { date, pct, STATUS_LABEL } from "@/utils/format";
import type { TaskStatus } from "@/types/api";

export default function DashboardPage() {
  const user = useAuth((s) => s.user);
  const { data, error, loading, reload } = useAsync(() => analysisApi.dashboard());
  if (loading) return <PageSkeleton />;
  if (error || !data) return <ErrorPanel message={error ?? "Could not load the dashboard."} onRetry={reload} />;

  const first = user?.full_name.split(" ")[0];
  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Hello, {first}</h1>
          <p className="mt-1 text-muted">{data.analysis_count ? "Here is where your resume stands." : "Run your first analysis to see where your resume stands."}</p>
        </div>
        <Link to="/analyses/new" className={buttonVariants()}>New analysis</Link>
      </div>

      {data.analysis_count === 0 ? (
        <EmptyState icon={<FileSearch className="h-10 w-10" />} title="No analyses yet"
          action={<Link to="/analyses/new" className={buttonVariants()}>Analyse a resume</Link>}>
          Upload or paste your resume and a job description. You will get a coverage score, the evidence behind each match and a learning roadmap.
        </EmptyState>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <Card><CardBody>
              <p className="text-sm text-muted">Analyses</p>
              <p className="mt-1 font-display text-4xl font-bold">{data.analysis_count}</p>
            </CardBody></Card>
            <Card><CardBody>
              <p className="text-sm text-muted">Average coverage</p>
              <p className="mt-1 font-display text-4xl font-bold text-pine">{pct(data.average_coverage, 1)}</p>
              <p className="text-xs text-muted">Best: {pct(data.best_coverage, 1)}</p>
            </CardBody></Card>
            <Card><CardBody>
              <p className="text-sm text-muted">Roadmap progress</p>
              <p className="mt-1 font-display text-4xl font-bold">{data.roadmap.total_tasks ? pct(data.roadmap.completed_percent) : "n/a"}</p>
              <Progress className="mt-2" value={data.roadmap.completed_percent ?? 0} />
            </CardBody></Card>
          </div>

          <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
            <Card>
              <CardHeader title="Recent analyses" action={<Link to="/history" className="text-sm font-semibold text-pine hover:underline">View all</Link>} />
              <CardBody className="pt-3">
                <ul className="divide-y divide-line">
                  {data.recent.map((a) => (
                    <li key={a.id}>
                      <Link to={`/analyses/${a.id}`} className="flex items-center justify-between gap-4 py-3 hover:text-pine">
                        <span className="min-w-0">
                          <span className="block truncate font-semibold">{a.job_title || a.target_role || `Analysis ${a.id}`}</span>
                          <span className="text-xs text-muted">{date(a.created_at)}, {a.direct_count} of {a.requirement_count} requirements shown</span>
                        </span>
                        <span className="font-display text-xl font-bold tabular-nums">{pct(a.coverage_score)}</span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </CardBody>
            </Card>
            <Card>
              <CardHeader title="Skills you most often lack" description="Requirements marked not shown, across all your analyses." />
              <CardBody>
                {data.frequently_missing.length ? (
                  <ul className="space-y-2">
                    {data.frequently_missing.map((m) => (
                      <li key={m.skill} className="flex items-center gap-3 text-sm">
                        <span className="w-40 truncate font-semibold">{m.skill}</span>
                        <span className="h-2 rounded-full bg-missing" style={{ width: `${(m.count / data.frequently_missing[0].count) * 100}%`, maxWidth: "9rem" }} />
                        <span className="text-muted tabular-nums">{m.count}</span>
                      </li>
                    ))}
                  </ul>
                ) : <p className="text-sm text-muted">No missing skills in your analyses.</p>}
              </CardBody>
            </Card>
          </div>

          <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
            {data.coverage_trend.length > 1 && (
              <Card>
                <CardHeader title="Coverage over time" description="Each point is one analysis." />
                <CardBody>
                  <div className="h-56">
                    <ResponsiveContainer>
                      <LineChart data={data.coverage_trend.map((t) => ({ ...t, day: date(t.date) }))}>
                        <CartesianGrid stroke="var(--color-line)" vertical={false} />
                        <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
                        <Tooltip formatter={(v: number) => `${v.toFixed(1)}%`} labelFormatter={(_, p) => p?.[0]?.payload?.label ?? ""} />
                        <Line type="monotone" dataKey="coverage" stroke="var(--color-pine)" strokeWidth={2} dot={{ r: 4 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </CardBody>
              </Card>
            )}
            <Card>
              <CardHeader title="Learning tasks" description="Self-reported progress across roadmaps." />
              <CardBody>
                {data.roadmap.total_tasks ? (
                  <dl className="grid grid-cols-2 gap-3">
                    {(Object.keys(STATUS_LABEL) as TaskStatus[]).map((s) => (
                      <div key={s} className="rounded-lg bg-paper p-3"><dt className="text-xs text-muted">{STATUS_LABEL[s]}</dt><dd className="font-display text-2xl font-bold">{data.roadmap.by_status[s]}</dd></div>
                    ))}
                  </dl>
                ) : <p className="text-sm text-muted">No learning tasks yet. Gaps from your analyses appear here.</p>}
              </CardBody>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
