import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Label, Textarea } from "@/components/ui/form";
import { labApi } from "@/services/api";
import { Explain, LabError, TokenList, useLabCall } from "./shared";

/* eslint-disable @typescript-eslint/no-explicit-any */
export function PreprocessingLab() {
  const [text, setText] = useState("The developers were building scalable REST APIs in Python, C++ and Node.js for 3 clients!");
  const [opts, setOpts] = useState({ lowercase: true, remove_stopwords: true, lemmatize: true, ngram_n: 2 });
  const { data, error, loading, run } = useLabCall<any>();

  return (
    <div className="space-y-5">
      <Explain>
        <p>Preprocessing turns raw text into tokens a model can count. <b>Normalisation</b> fixes Unicode and case; <b>tokenisation</b> splits text into units; <b>stop-word removal</b> drops frequent function words; <b>stemming</b> chops suffixes by rule (Porter), sometimes producing non-words; <b>lemmatisation</b> maps words to dictionary forms; <b>n-grams</b> keep short word sequences such as “machine learning”.</p>
        <p>This project does not apply every step everywhere: the original text is kept for evidence, technical tokens like C++ and Node.js are protected, and stemming is not used for skill matching because it turns “pandas” into “panda”. Tokens missing from the skill vocabulary are reported as out-of-vocabulary (OOV).</p>
      </Explain>
      <div>
        <Label htmlFor="pp-text">Sample text</Label>
        <Textarea id="pp-text" rows={3} value={text} onChange={(e) => setText(e.target.value)} />
      </div>
      <div className="flex flex-wrap items-center gap-5 text-sm">
        {([["lowercase", "Lower-case"], ["remove_stopwords", "Remove stop words"], ["lemmatize", "Use lemmas for n-grams"]] as const).map(([k, label]) => (
          <label key={k} className="flex items-center gap-2"><input type="checkbox" className="accent-[var(--color-pine)]" checked={opts[k]} onChange={(e) => setOpts({ ...opts, [k]: e.target.checked })} />{label}</label>
        ))}
        <label className="flex items-center gap-2">n =
          <select className="h-8 rounded border border-line px-1" value={opts.ngram_n} onChange={(e) => setOpts({ ...opts, ngram_n: Number(e.target.value) })}>
            {[1, 2, 3, 4].map((n) => <option key={n}>{n}</option>)}
          </select>
        </label>
        <Button loading={loading} disabled={!text.trim()} onClick={() => run(() => labApi.preprocessing({ text, ...opts }))}>Run preprocessing</Button>
      </div>
      <LabError error={error} />
      {data && (
        <div className="space-y-3">
          <div className="overflow-x-auto rounded-xl border border-line">
            <table className="w-full min-w-[40rem] text-left text-sm">
              <thead className="bg-paper text-xs text-muted"><tr><th className="px-3 py-2 font-semibold">Step</th><th className="px-3 py-2 font-semibold">Output</th></tr></thead>
              <tbody>
                <tr className="border-t border-line align-top"><td className="px-3 py-2 font-semibold">Original</td><td className="px-3 py-2">{data.original}</td></tr>
                {data.steps.map((s: any) => (
                  <tr key={s.name} className="border-t border-line align-top">
                    <td className="w-56 px-3 py-2"><p className="font-semibold">{s.name}</p><p className="text-xs text-muted">{s.description}</p></td>
                    <td className="px-3 py-2">{Array.isArray(s.output) ? <TokenList tokens={s.output} /> : s.output}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="grid gap-3 text-sm sm:grid-cols-2">
            <div className="rounded-lg border border-line p-3">
              <p className="font-semibold">Vocabulary</p>
              <p className="text-muted">{data.vocabulary.total_tokens} tokens, {data.vocabulary.unique_tokens} unique, type-token ratio {data.vocabulary.type_token_ratio}</p>
            </div>
            {data.oov && (
              <div className="rounded-lg border border-line p-3">
                <p className="font-semibold">Out of vocabulary ({data.oov_vocabulary_name})</p>
                <p className="text-muted">OOV rate {(data.oov.oov_rate * 100).toFixed(0)}%. Mapped to &lt;UNK&gt;: {data.oov.oov_tokens.join(", ") || "none"}</p>
              </div>
            )}
          </div>
          <p className="text-xs text-muted">Libraries used: tokenizer {data.backend.tokenizer}, stop words {data.backend.stopwords}, stemmer {data.backend.stemmer}, lemmatizer {data.backend.lemmatizer}. {data.backend.notes.join(" ")}</p>
        </div>
      )}
    </div>
  );
}
