import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Label, Textarea } from "@/components/ui/form";
import { ModelComparison } from "@/features/analysis/ModelComparison";
import { VerdictBadge } from "@/features/analysis/VerdictBadge";
import { labApi } from "@/services/api";
import { num } from "@/utils/format";
import { Explain, LabError, useLabCall } from "./shared";

/* eslint-disable @typescript-eslint/no-explicit-any */
export function CompareLab() {
  const [resume, setResume] = useState("PROJECTS\n- Trained a classifier that labels movie reviews as positive or negative using PyTorch.\n- Built backend services in Java with Spring Boot and MySQL.\n\nSKILLS\nPython, Git, Docker");
  const [job, setJob] = useState("Requirements:\n- Python and PyTorch\n- Text classification\n- PostgreSQL\n- REST APIs with FastAPI\nNice to have: Kubernetes");
  const { data, error, loading, run } = useLabCall<any>();
  return (
    <div className="space-y-5">
      <Explain>
        <p>The same resume and job ad run through three methods. <b>Keyword</b> matching finds skill names and aliases from the taxonomy. <b>TF-IDF</b> compares word overlap between each skill and each resume sentence. <b>Dense embeddings</b> compare meaning with a pretrained sentence transformer.</p>
        <p>The final verdict combines them with rules: a named skill is shown; high similarity is “verify”, unless the matching sentence names a different skill of the same kind (Java does not prove Python); related skills are transferable, not equal.</p>
      </Explain>
      <div className="grid gap-4 md:grid-cols-2">
        <div><Label htmlFor="cmp-r">Resume</Label><Textarea id="cmp-r" rows={8} value={resume} onChange={(e) => setResume(e.target.value)} /></div>
        <div><Label htmlFor="cmp-j">Job description</Label><Textarea id="cmp-j" rows={8} value={job} onChange={(e) => setJob(e.target.value)} /></div>
      </div>
      <Button loading={loading} disabled={resume.trim().length < 30 || job.trim().length < 30} onClick={() => run(() => labApi.compareModels(resume, job))}>Compare methods</Button>
      <LabError error={error} />
      {data && (
        <div className="space-y-6">
          {data.model_info.fallback_used && <LabError error={`Semantic model unavailable, hybrid verdicts used TF-IDF: ${data.model_info.fallback_reason}`} />}
          <div className="overflow-x-auto rounded-lg border border-line">
            <table className="w-full min-w-[36rem] text-left text-sm">
              <thead className="bg-paper text-xs text-muted"><tr><th className="px-3 py-2 font-semibold">Requirement</th><th className="px-3 py-2 font-semibold">TF-IDF</th><th className="px-3 py-2 font-semibold">Semantic</th><th className="px-3 py-2 font-semibold">Final verdict</th></tr></thead>
              <tbody>{data.requirements.map((r: any) => (
                <tr key={r.canonical} className="border-t border-line"><td className="px-3 py-2 font-semibold">{r.canonical}</td><td className="px-3 py-2 tabular-nums">{num(r.tfidf_similarity)}</td><td className="px-3 py-2 tabular-nums">{num(r.semantic_similarity)}</td><td className="px-3 py-2"><VerdictBadge verdict={r.classification} /></td></tr>
              ))}</tbody>
            </table>
          </div>
          <ModelComparison methods={data.methods} />
        </div>
      )}
    </div>
  );
}
