import { useState, type ReactNode } from "react";
import { toast } from "sonner";
import { errorMessage } from "@/services/api";

/** "Explain to your examiner" panel: the theory behind each demonstration. */
export function Explain({ children }: { children: ReactNode }) {
  return (
    <details className="group rounded-lg border border-line bg-paper px-4 py-3 text-sm" open>
      <summary className="cursor-pointer font-semibold text-pine">What this demonstrates</summary>
      <div className="mt-2 space-y-2 leading-relaxed text-muted">{children}</div>
    </details>
  );
}

export function useLabCall<T>() {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const run = async (fn: () => Promise<T>) => {
    setLoading(true);
    setError(null);
    try {
      setData(await fn());
    } catch (e) {
      const msg = errorMessage(e);
      setError(msg);
      setData(null);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };
  return { data, error, loading, run };
}

export function LabError({ error }: { error: string | null }) {
  if (!error) return null;
  return <p role="alert" className="rounded-lg border border-verify/40 bg-verify-soft px-3 py-2 text-sm text-[#6b4708]">{error}</p>;
}

export function TokenList({ tokens, highlight }: { tokens: string[]; highlight?: Set<string> }) {
  if (!tokens.length) return <span className="text-xs text-muted">(empty)</span>;
  return (
    <div className="flex flex-wrap gap-1">
      {tokens.map((t, i) => (
        <span key={`${t}-${i}`} className={`rounded px-1.5 py-0.5 font-mono text-xs ${highlight?.has(t) ? "bg-missing-soft text-missing line-through" : "bg-pine-soft text-ink"}`}>{t}</span>
      ))}
    </div>
  );
}

export function splitWords(s: string): string[] {
  return s.split(/[,\s]+/).map((w) => w.trim()).filter(Boolean);
}

export const SAMPLE_RESUME_SNIPPET = "Built a customer churn prediction model with scikit-learn and pandas. Developed REST APIs in Flask to serve predictions. Trained an LSTM model in PyTorch to classify movie reviews.";
export const SAMPLE_JOB_SNIPPET = "We need experience with machine learning, deep learning in PyTorch or TensorFlow, text classification and building REST APIs with FastAPI or Flask.";
