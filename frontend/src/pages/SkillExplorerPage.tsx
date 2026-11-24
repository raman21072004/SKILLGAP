import { useParams } from "react-router-dom";
import { ErrorPanel, PageSkeleton } from "@/components/ui/misc";
import { AnalysisNav } from "@/features/analysis/AnalysisNav";
import { SkillTable } from "@/features/analysis/SkillTable";
import { useAsync } from "@/hooks/useAsync";
import { analysisApi } from "@/services/api";

export default function SkillExplorerPage() {
  const { id = "" } = useParams();
  const { data, error, loading, reload } = useAsync(() => analysisApi.get(id), [id]);
  if (loading) return <PageSkeleton />;
  if (error || !data) return <ErrorPanel message={error ?? "Analysis not found."} onRetry={reload} />;
  return (
    <div>
      <AnalysisNav id={data.id} title={data.job_title || data.target_role || `Analysis ${data.id}`} />
      <p className="mb-4 text-sm text-muted">Search, filter and sort every requirement. Similarity shows the semantic cosine when available, otherwise TF-IDF. To correct a result, open it on the Results tab.</p>
      <SkillTable requirements={data.requirements} />
    </div>
  );
}
