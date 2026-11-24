import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Label, Textarea } from "@/components/ui/form";
import { labApi } from "@/services/api";
import { Explain, LabError, useLabCall } from "./shared";

/* eslint-disable @typescript-eslint/no-explicit-any */
function VectorCard({ title, v }: { title: string; v: any }) {
  return (
    <div className="rounded-lg border border-line p-4 text-sm">
      <h3 className="font-bold">{title}</h3>
      <p className="text-xs text-muted">{v.representation}</p>
      <dl className="mt-3 grid grid-cols-3 gap-2">
        <div><dt className="text-xs text-muted">Dimensions</dt><dd className="font-display text-xl font-bold">{v.dimensions}</dd></div>
        <div><dt className="text-xs text-muted">Non-zero</dt><dd className="font-display text-xl font-bold">{v.non_zero}</dd></div>
        <div><dt className="text-xs text-muted">Sparsity</dt><dd className="font-display text-xl font-bold">{(v.sparsity * 100).toFixed(0)}%</dd></div>
      </dl>
      <p className="mt-3 text-xs text-muted">First {v.head.length} values{v.truncated ? " (truncated)" : ""}:</p>
      <p className="mt-1 break-all font-mono text-xs">[{v.head.join(", ")}{v.truncated ? ", …" : ""}]</p>
      {v.non_zero_features && <p className="mt-3 text-xs"><span className="text-muted">Non-zero features: </span>{v.non_zero_features.map((f: any) => `${f.term} (${f.weight})`).join(", ")}</p>}
    </div>
  );
}

export function VectorsLab() {
  const [text, setText] = useState("Built REST APIs in Flask and deployed them with Docker.");
  const { data, error, loading, run } = useLabCall<any>();
  return (
    <div className="space-y-5">
      <Explain>
        <p>In a <b>vector space model</b> every text becomes a point in a high-dimensional space. A <b>sparse</b> vector (TF-IDF) has one dimension per vocabulary term and is mostly zeros; its dimensions are interpretable but unrelated words are always orthogonal.</p>
        <p>A <b>dense</b> sentence embedding (all-MiniLM-L6-v2, 384 dimensions) is produced by a transformer network. Almost every value is non-zero and no single dimension is interpretable, but texts with similar meaning land close together, which is what lets the matching engine recognise paraphrases.</p>
      </Explain>
      <div><Label htmlFor="vec-text">Text</Label><Textarea id="vec-text" rows={2} value={text} onChange={(e) => setText(e.target.value)} /></div>
      <Button loading={loading} disabled={!text.trim()} onClick={() => run(() => labApi.vectors(text, ["Trained neural networks in PyTorch.", "Wrote SQL queries on PostgreSQL."]))}>Build both vectors</Button>
      <LabError error={error} />
      {data && (
        <div className="grid gap-4 md:grid-cols-2">
          <VectorCard title="Sparse: TF-IDF" v={data.sparse} />
          {data.dense ? <VectorCard title="Dense: sentence embedding" v={data.dense} /> : <LabError error={`Dense vector unavailable: ${data.dense_error}`} />}
        </div>
      )}
    </div>
  );
}
