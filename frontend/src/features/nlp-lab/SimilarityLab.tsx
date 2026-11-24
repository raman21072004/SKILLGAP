import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Label, Textarea } from "@/components/ui/form";
import { labApi } from "@/services/api";
import { Explain, LabError, useLabCall } from "./shared";

/* eslint-disable @typescript-eslint/no-explicit-any */
function Breakdown({ title, r }: { title: string; r: any }) {
  return (
    <div className="rounded-lg border border-line p-4 text-sm">
      <h3 className="font-bold">{title}</h3>
      <p className="mt-2 font-display text-4xl font-bold text-pine tabular-nums">{r.cosine_similarity.toFixed(3)}</p>
      <dl className="mt-3 grid grid-cols-2 gap-1 text-xs">
        <dt className="text-muted">A · B</dt><dd className="tabular-nums">{r.dot_product}</dd>
        <dt className="text-muted">||A||</dt><dd className="tabular-nums">{r.norm_a}</dd>
        <dt className="text-muted">||B||</dt><dd className="tabular-nums">{r.norm_b}</dd>
        <dt className="text-muted">Angle</dt><dd className="tabular-nums">{r.angle_degrees}°</dd>
        <dt className="text-muted">Dimensions</dt><dd className="tabular-nums">{r.dimensions}</dd>
      </dl>
      {r.model && <p className="mt-2 text-xs text-muted">{r.model}</p>}
    </div>
  );
}

export function SimilarityLab() {
  const [a, setA] = useState("Trained a classifier that labels product reviews as positive or negative.");
  const [b, setB] = useState("Experience with text classification and sentiment analysis.");
  const { data, error, loading, run } = useLabCall<any>();
  return (
    <div className="space-y-5">
      <Explain>
        <p className="font-mono text-ink">cosine_similarity(A, B) = (A · B) / (||A|| × ||B||)</p>
        <p>Cosine similarity measures the <b>angle</b> between two vectors and ignores their <b>magnitude</b> (length), so a long resume and a short job ad can be compared. 1 means the same direction, 0 means orthogonal (unrelated). TF-IDF vectors are non-negative, so their cosine stays between 0 and 1.</p>
        <p>Thresholds are not universal: 0.3 can be high for TF-IDF and low for sentence embeddings. Try the example: TF-IDF sees almost no shared words, while dense embeddings recognise the paraphrase. Neither proves the skill.</p>
      </Explain>
      <div className="grid gap-4 md:grid-cols-2">
        <div><Label htmlFor="sim-a">Text A</Label><Textarea id="sim-a" rows={3} value={a} onChange={(e) => setA(e.target.value)} /></div>
        <div><Label htmlFor="sim-b">Text B</Label><Textarea id="sim-b" rows={3} value={b} onChange={(e) => setB(e.target.value)} /></div>
      </div>
      <Button loading={loading} disabled={!a.trim() || !b.trim()} onClick={() => run(() => labApi.similarity(a, b))}>Compare</Button>
      <LabError error={error} />
      {data && (
        <div className="space-y-3">
          <div className="grid gap-4 md:grid-cols-2">
            <Breakdown title="TF-IDF (sparse, lexical)" r={data.tfidf} />
            {data.semantic ? <Breakdown title="Sentence embedding (dense, semantic)" r={data.semantic} /> : <LabError error={`Semantic similarity unavailable: ${data.semantic_error}`} />}
          </div>
          <p className="text-sm text-muted">{data.interpretation}</p>
        </div>
      )}
    </div>
  );
}
