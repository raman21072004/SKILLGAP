import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Classification, Requirement } from "@/types/api";
import { VERDICT } from "@/utils/format";

export function CategoryChart({ requirements }: { requirements: Requirement[] }) {
  const byCat = new Map<string, Record<Classification, number>>();
  for (const r of requirements) {
    const row = byCat.get(r.category) ?? { direct_match: 0, strong_semantic: 0, related: 0, missing: 0 };
    row[r.effective_classification] += 1;
    byCat.set(r.category, row);
  }
  const data = [...byCat.entries()].map(([category, v]) => ({ category, ...v }));
  if (!data.length) return null;
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer>
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
          <CartesianGrid horizontal={false} stroke="var(--color-line)" />
          <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12, fill: "var(--color-muted)" }} />
          <YAxis type="category" dataKey="category" width={150} tick={{ fontSize: 12, fill: "var(--color-ink)" }} />
          <Tooltip cursor={{ fill: "var(--color-paper)" }} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {(Object.keys(VERDICT) as Classification[]).map((k) => (
            <Bar key={k} dataKey={k} name={VERDICT[k].short} stackId="a" fill={VERDICT[k].color} radius={2} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
