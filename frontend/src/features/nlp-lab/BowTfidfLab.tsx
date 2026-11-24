import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Label, Textarea } from "@/components/ui/form";
import { labApi } from "@/services/api";
import { Explain, LabError, SAMPLE_JOB_SNIPPET, SAMPLE_RESUME_SNIPPET, useLabCall } from "./shared";

/* eslint-disable @typescript-eslint/no-explicit-any */
export function BowTfidfLab() {
  const [a, setA] = useState(SAMPLE_RESUME_SNIPPET);
  const [b, setB] = useState(SAMPLE_JOB_SNIPPET);
  const bow = useLabCall<any>();
  const tfidf = useLabCall<any>();
  const go = () => {
    void bow.run(() => labApi.bow(a, b));
    void tfidf.run(() => labApi.tfidf(a, b));
  };
  return (
    <div className="space-y-5">
      <Explain>
        <p><b>Bag of Words</b> represents a document as a vector of term counts over the whole vocabulary. Word order is lost and there is no notion of meaning: “ML” and “machine learning” are different dimensions, and most entries are zero, so the matrix is <b>sparse</b>.</p>
        <p><b>TF-IDF</b> multiplies term frequency by inverse document frequency, idf(t) = ln((1+N)/(1+df(t))) + 1, so words found in every document get low weight. Rows are L2-normalised, so the dot product equals the cosine similarity. We use unigrams and bigrams so multi-word skills survive.</p>
      </Explain>
      <div className="grid gap-4 md:grid-cols-2">
        <div><Label htmlFor="doc-a">Document A (resume)</Label><Textarea id="doc-a" rows={5} value={a} onChange={(e) => setA(e.target.value)} /></div>
        <div><Label htmlFor="doc-b">Document B (job description)</Label><Textarea id="doc-b" rows={5} value={b} onChange={(e) => setB(e.target.value)} /></div>
      </div>
      <Button loading={bow.loading || tfidf.loading} disabled={!a.trim() || !b.trim()} onClick={go}>Vectorise both documents</Button>
      <LabError error={bow.error || tfidf.error} />
      {bow.data && (
        <div>
          <h3 className="font-bold">Bag of Words matrix</h3>
          <p className="text-sm text-muted">Shape {bow.data.shape.join(" × ")}, {bow.data.non_zero} non-zero values, sparsity {(bow.data.sparsity * 100).toFixed(1)}%. Showing the {bow.data.vocabulary.length} most frequent terms.</p>
          <div className="mt-2 overflow-x-auto rounded-lg border border-line">
            <table className="text-xs">
              <thead className="bg-paper"><tr><th className="px-2 py-1 text-left">Doc</th>{bow.data.vocabulary.map((v: string) => <th key={v} className="px-2 py-1 font-mono font-medium">{v}</th>)}</tr></thead>
              <tbody>{bow.data.matrix.map((row: number[], i: number) => (
                <tr key={i} className="border-t border-line"><td className="px-2 py-1 font-semibold">{i === 0 ? "A" : "B"}</td>{row.map((c, j) => <td key={j} className={`px-2 py-1 text-center tabular-nums ${c ? "bg-pine-soft font-semibold" : "text-muted"}`}>{c}</td>)}</tr>
              ))}</tbody>
            </table>
          </div>
        </div>
      )}
      {tfidf.data && (
        <div className="grid gap-4 md:grid-cols-3">
          {[["Top terms in A", tfidf.data.resume_top_terms], ["Top terms in B", tfidf.data.job_top_terms]].map(([title, terms]) => (
            <div key={title as string} className="rounded-lg border border-line p-3">
              <h3 className="font-bold">{title as string}</h3>
              <ul className="mt-2 space-y-1 text-sm">{(terms as { term: string; score: number }[]).slice(0, 10).map((t) => (
                <li key={t.term} className="flex items-center gap-2"><span className="w-36 truncate font-mono text-xs">{t.term}</span><span className="h-2 rounded bg-pine" style={{ width: `${t.score * 160}px` }} /><span className="text-xs tabular-nums text-muted">{t.score.toFixed(3)}</span></li>
              ))}</ul>
            </div>
          ))}
          <div className="rounded-lg border border-line p-3 text-sm">
            <h3 className="font-bold">Document similarity</h3>
            <p className="mt-2">TF-IDF cosine: <b className="tabular-nums">{tfidf.data.tfidf_cosine_similarity}</b></p>
            <p>Bag of Words cosine: <b className="tabular-nums">{tfidf.data.bow_cosine_similarity}</b></p>
            <p className="mt-2 text-muted">Vocabulary size {tfidf.data.vocabulary_size}. Shared terms: {tfidf.data.shared_terms.slice(0, 12).join(", ") || "none"}.</p>
            <p className="mt-2 text-xs text-muted">{tfidf.data.formula}</p>
          </div>
        </div>
      )}
    </div>
  );
}
