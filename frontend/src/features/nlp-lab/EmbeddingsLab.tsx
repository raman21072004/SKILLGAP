import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input, Label, Select } from "@/components/ui/form";
import { labApi } from "@/services/api";
import { Explain, LabError, splitWords, useLabCall } from "./shared";

/* eslint-disable @typescript-eslint/no-explicit-any */
function Neighbors({ words }: { words: any[] }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {words.map((w) => (
        <div key={w.word} className="rounded-lg border border-line p-3 text-sm">
          <p className="font-bold">{w.word}</p>
          {w.in_vocabulary === false || w.oov ? (
            <p className="mt-1 text-xs text-missing">{w.message ?? "Out of vocabulary (OOV): the model never saw this word, so it has no vector."}</p>
          ) : (
            <ol className="mt-1 space-y-0.5 text-xs">
              {w.neighbors.map((n: any) => <li key={n.word} className="flex justify-between gap-2"><span>{n.word}</span><span className="tabular-nums text-muted">{n.similarity.toFixed(3)}</span></li>)}
            </ol>
          )}
        </div>
      ))}
    </div>
  );
}

export function Word2VecLab() {
  const [words, setWords] = useState("python, docker, pytorch, postgresql, react, blockchain");
  const [window, setWindow] = useState(4);
  const [size, setSize] = useState(50);
  const { data, error, loading, run } = useLabCall<any>();
  return (
    <div className="space-y-5">
      <Explain>
        <p><b>Word2Vec</b> learns a dense vector per word from the contexts it appears in. <b>CBOW</b> predicts the centre word from the words in its context window; <b>Skip-Gram</b> predicts the context words from the centre word. CBOW trains faster and smooths frequent words; Skip-Gram handles rare words better.</p>
        <p>Here both are trained with Gensim on a small <b>synthetic</b> corpus of about 740 template sentences (data/corpus/tech_corpus.txt, fixed seed). It is far too small for production embeddings, so expect rough clusters, not reliable meaning. Words the corpus never contains are out of vocabulary.</p>
      </Explain>
      <div className="grid gap-4 sm:grid-cols-[1fr_8rem_8rem_auto] sm:items-end">
        <div><Label htmlFor="w2v-words">Words</Label><Input id="w2v-words" value={words} onChange={(e) => setWords(e.target.value)} /></div>
        <div><Label htmlFor="w2v-window">Context window</Label><Select id="w2v-window" value={window} onChange={(e) => setWindow(Number(e.target.value))}>{[2, 3, 4, 5, 6, 8].map((n) => <option key={n}>{n}</option>)}</Select></div>
        <div><Label htmlFor="w2v-size">Dimensions</Label><Select id="w2v-size" value={size} onChange={(e) => setSize(Number(e.target.value))}>{[20, 50, 100].map((n) => <option key={n}>{n}</option>)}</Select></div>
        <Button loading={loading} disabled={!splitWords(words).length} onClick={() => run(() => labApi.compareW2v(splitWords(words).slice(0, 20), window, size))}>Train and compare</Button>
      </div>
      <LabError error={error} />
      {data && (
        <div className="space-y-5">
          <p className="text-sm text-muted">Corpus: {data.corpus.sentences} sentences, {data.corpus.tokens} tokens, {data.corpus.vocabulary} distinct words (synthetic). Window {data.window}, {data.vector_size} dimensions.</p>
          {(["cbow", "skipgram"] as const).map((k) => (
            <div key={k}>
              <h3 className="mb-2 font-bold">{k === "cbow" ? "CBOW nearest neighbours" : "Skip-Gram nearest neighbours"} <span className="text-sm font-normal text-muted">(vocabulary {data.models[k].vocabulary_size})</span></h3>
              <Neighbors words={data.models[k].words} />
            </div>
          ))}
          <p className="text-xs text-muted">{data.note}</p>
        </div>
      )}
    </div>
  );
}

export function GloveLab() {
  const [words, setWords] = useState("python, java, database, cloud, neural, language");
  const { data, error, loading, run } = useLabCall<any>();
  return (
    <div className="space-y-5">
      <Explain>
        <p><b>GloVe</b> (Global Vectors) builds a global word-word co-occurrence matrix over a large corpus and fits vectors so that the dot product of two word vectors approximates the log of how often they co-occur. Word2Vec learns from local windows one at a time; GloVe uses global counts.</p>
        <p>This demo loads Stanford’s pretrained <b>glove-wiki-gigaword-50</b> (Wikipedia + Gigaword, 400k words, 50 dimensions). It is downloaded once with <code>python scripts/download_models.py --glove</code>. If it is missing, the API says so; Word2Vec vectors are never relabelled as GloVe.</p>
      </Explain>
      <div className="flex flex-wrap items-end gap-3">
        <div className="min-w-64 flex-1"><Label htmlFor="glove-words">Words</Label><Input id="glove-words" value={words} onChange={(e) => setWords(e.target.value)} /></div>
        <Button loading={loading} disabled={!splitWords(words).length} onClick={() => run(() => labApi.glove(splitWords(words).slice(0, 20)))}>Find neighbours</Button>
      </div>
      <LabError error={error} />
      {data && (
        <div className="space-y-4">
          <p className="text-sm text-muted">Pretrained GloVe: {data.vocabulary_size.toLocaleString()} words, {data.dimension} dimensions.</p>
          <Neighbors words={data.words} />
          {data.pairwise.length > 0 && (
            <div className="overflow-x-auto"><table className="text-sm"><thead className="text-xs text-muted"><tr><th className="pr-4 text-left">Pair</th><th className="text-left">Cosine</th></tr></thead>
              <tbody>{data.pairwise.slice(0, 15).map((p: any) => <tr key={p.a + p.b}><td className="pr-4">{p.a} / {p.b}</td><td className="tabular-nums">{p.similarity.toFixed(3)}</td></tr>)}</tbody></table></div>
          )}
        </div>
      )}
    </div>
  );
}

export function AnalogyLab() {
  const [model, setModel] = useState("glove");
  const [pos, setPos] = useState("king, woman");
  const [neg, setNeg] = useState("man");
  const { data, error, loading, run } = useLabCall<any>();
  return (
    <div className="space-y-5">
      <Explain>
        <p>If an embedding space encodes relations as directions, vector arithmetic can solve analogies: vec(king) − vec(man) + vec(woman) lands near vec(queen). We take the positive words, subtract the negative words, and return the nearest words by cosine similarity (excluding the inputs).</p>
        <p>This is an <b>embedding experiment</b>, not part of skill matching. Results depend entirely on the model and its training data: pretrained GloVe often reproduces classic analogies; the tiny Word2Vec demo corpus usually will not.</p>
      </Explain>
      <div className="grid gap-3 sm:grid-cols-[12rem_1fr_1fr_auto] sm:items-end">
        <div><Label htmlFor="an-model">Model</Label><Select id="an-model" value={model} onChange={(e) => setModel(e.target.value)}>
          <option value="glove">GloVe (pretrained)</option><option value="word2vec-skipgram">Word2Vec Skip-Gram (demo)</option><option value="word2vec-cbow">Word2Vec CBOW (demo)</option>
        </Select></div>
        <div><Label htmlFor="an-pos">Add</Label><Input id="an-pos" value={pos} onChange={(e) => setPos(e.target.value)} /></div>
        <div><Label htmlFor="an-neg">Subtract</Label><Input id="an-neg" value={neg} onChange={(e) => setNeg(e.target.value)} /></div>
        <Button loading={loading} disabled={!splitWords(pos).length} onClick={() => run(() => labApi.analogy(model, splitWords(pos), splitWords(neg)))}>Compute</Button>
      </div>
      <LabError error={error} />
      {data && (data.ok ? (
        <div className="rounded-lg border border-line p-4">
          <p className="text-sm text-muted">{data.expression} ≈</p>
          <ol className="mt-2 space-y-1">{data.results.map((r: any, i: number) => (
            <li key={r.word} className={`flex justify-between text-sm ${i === 0 ? "font-display text-xl font-bold text-pine" : ""}`}><span>{r.word}</span><span className="tabular-nums text-muted">{r.similarity.toFixed(3)}</span></li>
          ))}</ol>
          <p className="mt-3 text-xs text-muted">{data.note}</p>
        </div>
      ) : <LabError error={data.message} />)}
    </div>
  );
}
