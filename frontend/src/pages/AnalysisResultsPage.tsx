import { Download, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { ConfirmDialog, ErrorPanel, Notice, PageSkeleton } from "@/components/ui/misc";
import { CategoryChart } from "@/charts/CategoryChart";
import { EvidenceBar } from "@/charts/EvidenceBar";
import { AnalysisNav } from "@/features/analysis/AnalysisNav";
import { EvidenceText } from "@/features/analysis/EvidenceText";
import { ModelComparison } from "@/features/analysis/ModelComparison";
import { RequirementRow } from "@/features/analysis/RequirementRow";
import { useAsync } from "@/hooks/useAsync";
import { analysisApi, downloadJson, errorMessage } from "@/services/api";
import type { Classification, Requirement } from "@/types/api";
import { date, MODE_LABEL, num, pct, VERDICT } from "@/utils/format";

const ORDER: Classification[] = ["direct_match", "strong_semantic", "related", "missing"];

export default function AnalysisResultsPage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const { data, setData, error, loading, reload } = useAsync(() => analysisApi.get(id), [id]);
  const [active, setActive] = useState<string | null>(null);
  const [confirm, setConfirm] = useState(false);

  const grouped = useMemo(() => {
    const out: Record<Classification, Requirement[]> = { direct_match: [], strong_semantic: [], related: [], missing: [] };
    data?.requirements.forEach((r) => out[r.effective_classification].push(r));
    return out;
  }, [data]);

  if (loading) return <PageSkeleton />;
  if (error || !data) return <ErrorPanel message={error ?? "Analysis not found."} onRetry={reload} />;

  const title = data.job_title || data.target_role || `Analysis ${data.id}`;
  const cov = data.coverage;

  const correct = async (req: Requirement, value: Classification | null) => {
    try {
      const updated = await analysisApi.correct(data.id, req.match_id, value);
      setData(updated);
      toast.success(value ? `Marked ${req.canonical} as “${VERDICT[value].short}”` : `Restored the system result for ${req.canonical}`);
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };

  const remove = async () => {
    try {
      await analysisApi.remove(data.id);
      toast.success("Analysis deleted");
      navigate("/history");
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };

  return (
    <div>
      <AnalysisNav id={data.id} title={title} />

      {data.model_info.fallback_used && (
        <div className="mb-6"><Notice tone="warn">
          <b>Deep semantic matching was not available, so TF-IDF similarity was used instead.</b> {data.model_info.fallback_reason}
        </Notice></div>
      )}
      {data.warnings.map((w) => <div key={w} className="mb-4"><Notice tone="warn">{w}</Notice></div>)}

      <section className="grid gap-6 lg:grid-cols-[18rem_1fr]">
        <Card>
          <CardBody>
            <p className="text-sm font-semibold">Requirement coverage</p>
            <p className="font-display text-6xl font-bold leading-none text-pine tabular-nums">{cov.coverage_score.toFixed(1)}<span className="text-3xl">%</span></p>
            <dl className="mt-5 space-y-2 text-sm">
              <div className="flex justify-between"><dt className="text-muted">Must-have coverage</dt><dd className="font-semibold">{pct(cov.must_have_coverage, 1)}</dd></div>
              <div className="flex justify-between"><dt className="text-muted">Nice-to-have coverage</dt><dd className="font-semibold">{pct(cov.nice_to_have_coverage, 1)}</dd></div>
              <div className="flex justify-between"><dt className="text-muted">Evidence weight</dt><dd className="font-semibold tabular-nums">{cov.accepted_weight} / {cov.total_weight}</dd></div>
            </dl>
            <p className="mt-4 rounded-lg bg-paper p-3 text-xs text-muted">{cov.formula}. Counted: {cov.accepted_classes.map((c) => VERDICT[c as Classification]?.short ?? c).join(" and ")} (plus your corrections).</p>
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Every requirement, weighted" description="Each block is one requirement from the job ad, sized by its weight. Select a block to see its evidence." />
          <CardBody>
            <EvidenceBar items={data.requirements.map((r) => ({ skill: r.canonical, weight: r.weight, verdict: r.effective_classification, importance: r.importance }))} onSelect={setActive} />
            <div className="mt-6 grid gap-4 text-sm sm:grid-cols-3">
              <div><p className="text-muted">Document similarity (TF-IDF)</p><p className="font-display text-2xl font-bold">{num(data.document_similarity.tfidf)}</p></div>
              <div><p className="text-muted">Document similarity (semantic)</p><p className="font-display text-2xl font-bold">{num(data.document_similarity.semantic)}</p></div>
              <div><p className="text-muted">Method</p><p className="font-semibold">{MODE_LABEL[data.mode]}</p><p className="text-xs text-muted">{data.model_info.similarity_backend ?? "taxonomy only"}, {date(data.created_at)}</p></div>
            </div>
            <p className="mt-3 text-xs text-muted">{data.document_similarity.note}</p>
          </CardBody>
        </Card>
      </section>

      <section className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Requirements" description="Open a requirement for the explanation, the evidence and to correct the result." />
          <div className="mt-3">
            {ORDER.filter((k) => grouped[k].length).map((k) => (
              <div key={k}>
                <h3 className="border-y border-line bg-paper px-4 py-1.5 font-sans text-xs font-bold" style={{ color: VERDICT[k].color }}>{VERDICT[k].label} ({grouped[k].length})</h3>
                <ul>{grouped[k].map((r) => <RequirementRow key={r.match_id} req={r} active={active === r.canonical} onCorrect={correct} onFocusEvidence={setActive} />)}</ul>
              </div>
            ))}
            {!data.requirements.length && <p className="p-5 text-sm text-muted">No requirements were detected. Add must-have skills manually in a new analysis.</p>}
          </div>
        </Card>
        <div className="lg:sticky lg:top-6 lg:self-start">
          <Card>
            <CardHeader title="Your resume, with evidence highlighted" description="Highlighted sentences support at least one requirement. The selected requirement is shown in amber." />
            <CardBody>{data.resume_text ? <EvidenceText text={data.resume_text} requirements={data.requirements} activeSkill={active} /> : <p className="text-sm text-muted">Resume text is no longer stored.</p>}</CardBody>
          </Card>
        </div>
      </section>

      <section className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Requirements by category" />
          <CardBody><CategoryChart requirements={data.requirements} /></CardBody>
        </Card>
        <Card>
          <CardHeader title="Next steps" description="The most important gaps, in learning order." />
          <CardBody>
            <ul className="space-y-3 text-sm">
              {data.requirements.filter((r) => r.effective_classification !== "direct_match")
                .sort((a, b) => (a.importance === b.importance ? b.weight - a.weight : a.importance === "must_have" ? -1 : 1))
                .slice(0, 5)
                .map((r) => (
                  <li key={r.match_id} className="flex gap-3"><span className="mt-1.5 h-2 w-2 shrink-0 rounded-full" style={{ background: VERDICT[r.effective_classification].color }} /><span><b>{r.canonical}:</b> {r.next_action}</span></li>
                ))}
            </ul>
            <Link to={`/analyses/${data.id}/roadmap`} className={buttonVariants({ variant: "secondary", className: "mt-5" })}>Open the learning roadmap</Link>
            {data.candidate_skills.length > 0 && (
              <div className="mt-6">
                <h3 className="text-sm font-bold">Skills found in your resume</h3>
                <p className="mt-1 text-sm text-muted">{data.candidate_skills.map((c) => c.canonical).join(", ")}</p>
              </div>
            )}
            {data.unrecognized_job_terms.length > 0 && (
              <div className="mt-4">
                <h3 className="text-sm font-bold">Job ad terms outside the skill taxonomy</h3>
                <p className="mt-1 text-sm text-muted">These important terms were not checked. Review them yourself: {data.unrecognized_job_terms.map((t) => t.term).join(", ")}.</p>
              </div>
            )}
          </CardBody>
        </Card>
      </section>

      <Card className="mt-6">
        <CardHeader title="Method comparison" description="Keyword, TF-IDF and dense-embedding matching on exactly the same resume and job ad." />
        <CardBody><ModelComparison methods={data.model_comparison} /></CardBody>
      </Card>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
        <p className="max-w-2xl text-xs text-muted">{data.disclaimer}</p>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => downloadJson(data, `skillgap-analysis-${data.id}.json`)}><Download className="h-4 w-4" aria-hidden /> Export JSON</Button>
          <Button variant="secondary" onClick={() => setConfirm(true)}><Trash2 className="h-4 w-4" aria-hidden /> Delete</Button>
        </div>
      </div>
      <ConfirmDialog open={confirm} title="Delete this analysis?" body="The analysis, its evidence, roadmap and stored resume text are removed permanently."
        confirmLabel="Delete analysis" onConfirm={remove} onCancel={() => setConfirm(false)} />
    </div>
  );
}
