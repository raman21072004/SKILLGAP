import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { MethodResult } from "@/types/api";

export function ModelComparison({ methods }: { methods: MethodResult[] }) {
  const data = methods.filter((m) => m.available).map((m) => ({
    name: m.method === "semantic" ? "Dense embeddings" : m.method === "tfidf" ? "TF-IDF" : "Keyword",
    Matched: m.matched.length,
    Related: m.related.length,
    Missing: m.missing.length,
  }));
  return (
    <div className="space-y-5">
      <div className="h-56 w-full">
        <ResponsiveContainer>
          <BarChart data={data} margin={{ left: -16 }}>
            <CartesianGrid vertical={false} stroke="var(--color-line)" />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
            <Tooltip cursor={{ fill: "var(--color-paper)" }} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar dataKey="Matched" fill="var(--color-shown)" radius={[3, 3, 0, 0]} />
            <Bar dataKey="Related" fill="var(--color-related)" radius={[3, 3, 0, 0]} />
            <Bar dataKey="Missing" fill="var(--color-missing)" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[36rem] text-left text-sm">
          <thead className="border-b border-line text-xs text-muted">
            <tr><th className="py-2 pr-3 font-semibold">Method</th><th className="py-2 pr-3 font-semibold">Matched</th><th className="py-2 pr-3 font-semibold">Time</th><th className="py-2 font-semibold">Limitations</th></tr>
          </thead>
          <tbody>
            {methods.map((m) => (
              <tr key={m.method} className="border-b border-line align-top last:border-0">
                <td className="py-2 pr-3 font-semibold">{m.label}</td>
                <td className="py-2 pr-3">{m.available ? `${m.matched.length} of ${m.matched.length + m.related.length + m.missing.length}` : "Unavailable"}</td>
                <td className="py-2 pr-3 tabular-nums">{m.time_ms !== null ? `${m.time_ms.toFixed(1)} ms` : "n/a"}</td>
                <td className="py-2 text-muted">{m.limitations}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-muted">These are three different methods run on the same input. Only the dense-embedding method uses a deep learning model. Matched counts use each method's own uncalibrated threshold.</p>
    </div>
  );
}
