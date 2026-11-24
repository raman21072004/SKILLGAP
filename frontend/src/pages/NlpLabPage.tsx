import { useState } from "react";
import { Card, CardBody } from "@/components/ui/card";
import { Tabs } from "@/components/ui/misc";
import { BowTfidfLab } from "@/features/nlp-lab/BowTfidfLab";
import { CompareLab } from "@/features/nlp-lab/CompareLab";
import { AnalogyLab, GloveLab, Word2VecLab } from "@/features/nlp-lab/EmbeddingsLab";
import { PreprocessingLab } from "@/features/nlp-lab/PreprocessingLab";
import { ProjectionLab } from "@/features/nlp-lab/ProjectionLab";
import { SimilarityLab } from "@/features/nlp-lab/SimilarityLab";
import { VectorsLab } from "@/features/nlp-lab/VectorsLab";
import { useAsync } from "@/hooks/useAsync";
import { labApi } from "@/services/api";

const MODULES = [
  { value: "pre", label: "Preprocessing", el: <PreprocessingLab /> },
  { value: "bow", label: "Bag of Words & TF-IDF", el: <BowTfidfLab /> },
  { value: "vsm", label: "Sparse vs dense", el: <VectorsLab /> },
  { value: "w2v", label: "Word2Vec: CBOW & Skip-Gram", el: <Word2VecLab /> },
  { value: "glove", label: "GloVe", el: <GloveLab /> },
  { value: "cos", label: "Cosine similarity", el: <SimilarityLab /> },
  { value: "ana", label: "Analogies", el: <AnalogyLab /> },
  { value: "viz", label: "PCA & t-SNE", el: <ProjectionLab /> },
  { value: "cmp", label: "Method comparison", el: <CompareLab /> },
] as const;
type ModuleKey = (typeof MODULES)[number]["value"];

/* eslint-disable @typescript-eslint/no-explicit-any */
function ModelStatus() {
  const { data } = useAsync<any>(() => labApi.status());
  if (!data) return null;
  const row = (label: string, ok: boolean, note?: string) => (
    <li className="flex items-start gap-2"><span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${ok ? "bg-pine" : "bg-verify"}`} /><span><b>{label}</b>{ok ? " ready" : ` unavailable${note ? `: ${note}` : ""}`}</span></li>
  );
  return (
    <ul className="space-y-1 text-xs text-muted">
      {row("Sentence transformer", !!data.sentence_transformer?.available, data.sentence_transformer?.error)}
      {row("Word2Vec (Gensim)", data.word2vec.available, data.word2vec.error)}
      {row("GloVe", data.glove.available, data.glove.error)}
    </ul>
  );
}

export default function NlpLabPage() {
  const [tab, setTab] = useState<ModuleKey>("pre");
  return (
    <div className="space-y-6">
      <div className="grid gap-4 lg:grid-cols-[1fr_22rem] lg:items-end">
        <div>
          <h1 className="text-3xl font-bold">NLP Lab</h1>
          <p className="mt-1 max-w-2xl text-muted">Run each technique from the NLP syllabus on your own text. Every module shows which library produced the result and explains the theory you may be asked about in a viva.</p>
        </div>
        <ModelStatus />
      </div>
      <Tabs label="NLP Lab modules" tabs={MODULES.map(({ value, label }) => ({ value, label }))} value={tab} onChange={setTab} />
      <Card><CardBody role="tabpanel">{MODULES.find((m) => m.value === tab)!.el}</CardBody></Card>
    </div>
  );
}
