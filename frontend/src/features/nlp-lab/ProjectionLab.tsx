import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input, Label, Select } from "@/components/ui/form";
import { ProjectionPlot } from "@/charts/ProjectionPlot";
import { labApi } from "@/services/api";
import { Explain, LabError, splitWords, useLabCall } from "./shared";

/* eslint-disable @typescript-eslint/no-explicit-any */
const DEFAULT_ITEMS = "python, java, javascript, react, node.js, sql, postgresql, mysql, mongodb, docker, kubernetes, aws, azure, pytorch, tensorflow, keras, pandas, numpy, nlp, embeddings";

export function ProjectionLab() {
  const [source, setSource] = useState("word2vec-skipgram");
  const [method, setMethod] = useState("pca");
  const [items, setItems] = useState(DEFAULT_ITEMS);
  const [perplexity, setPerplexity] = useState(5);
  const [seed, setSeed] = useState(42);
  const { data, error, loading, run } = useLabCall<any>();
  return (
    <div className="space-y-5">
      <Explain>
        <p>Embeddings have 50 to 384 dimensions, so we project them to 2-D to look at them. <b>PCA</b> is a linear projection onto the two directions of greatest variance; the explained-variance ratio tells you how much information the picture keeps, and the rest is lost.</p>
        <p><b>t-SNE</b> is non-linear and preserves local neighbourhoods: points that are close were close in the original space. Distances between clusters and cluster sizes are not meaningful, results change with perplexity and random seed (fixed here for reproducibility), and it is slow on large sets. Both are visualisation tools only; they are not used to match skills.</p>
      </Explain>
      <div className="grid gap-3 md:grid-cols-4">
        <div><Label htmlFor="pr-source">Embeddings</Label><Select id="pr-source" value={source} onChange={(e) => setSource(e.target.value)}>
          <option value="word2vec-skipgram">Word2Vec Skip-Gram (demo)</option><option value="word2vec-cbow">Word2Vec CBOW (demo)</option>
          <option value="glove">GloVe (pretrained)</option><option value="sentence-transformer">Sentence transformer (skills)</option>
        </Select></div>
        <div><Label htmlFor="pr-method">Method</Label><Select id="pr-method" value={method} onChange={(e) => setMethod(e.target.value)}><option value="pca">PCA</option><option value="tsne">t-SNE</option></Select></div>
        <div><Label htmlFor="pr-perp">Perplexity (t-SNE)</Label><Input id="pr-perp" type="number" min={1} max={50} value={perplexity} disabled={method !== "tsne"} onChange={(e) => setPerplexity(Number(e.target.value) || 5)} /></div>
        <div><Label htmlFor="pr-seed">Random seed</Label><Input id="pr-seed" type="number" min={0} value={seed} disabled={method !== "tsne"} onChange={(e) => setSeed(Number(e.target.value) || 0)} /></div>
      </div>
      <div><Label htmlFor="pr-items">Words or skills</Label><Input id="pr-items" value={items} onChange={(e) => setItems(e.target.value)} /></div>
      <Button loading={loading} onClick={() => run(() => labApi.visualize({ source, method, items: splitWords(items), perplexity, seed }))}>Project to 2-D</Button>
      <LabError error={error} />
      {data && (
        <div className="space-y-3">
          {data.warnings.map((w: string) => <p key={w} className="rounded-lg bg-verify-soft px-3 py-2 text-sm text-[#6b4708]">{w}</p>)}
          <ProjectionPlot points={data.points} />
          <p className="text-sm text-muted">{data.explanation}</p>
          {data.method === "pca" && <p className="text-xs text-muted">Explained variance: PC1 {(data.explained_variance_ratio[0] * 100).toFixed(1)}%, PC2 {(data.explained_variance_ratio[1] * 100).toFixed(1)}%, from {data.original_dimensions} dimensions.</p>}
          {data.method === "tsne" && <p className="text-xs text-muted">Perplexity {data.perplexity}, seed {data.seed}, KL divergence {data.kl_divergence}, from {data.original_dimensions} dimensions.</p>}
        </div>
      )}
    </div>
  );
}
