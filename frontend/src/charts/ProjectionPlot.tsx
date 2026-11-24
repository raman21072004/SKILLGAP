import { CartesianGrid, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis, LabelList } from "recharts";

const PALETTE = ["#13624f", "#c98a1b", "#5d5f9e", "#b23a2e", "#2f7fa3", "#7a6a3a", "#8b4f8f", "#3f7d3a"];

export interface Point { label: string; x: number; y: number; group: string | null }

export function ProjectionPlot({ points }: { points: Point[] }) {
  const groups = [...new Set(points.map((p) => p.group ?? "Other"))];
  return (
    <div>
      <div className="h-96 w-full">
        <ResponsiveContainer>
          <ScatterChart margin={{ top: 16, right: 24, bottom: 8, left: 0 }}>
            <CartesianGrid stroke="var(--color-line)" />
            <XAxis type="number" dataKey="x" name="x" tick={{ fontSize: 11 }} />
            <YAxis type="number" dataKey="y" name="y" tick={{ fontSize: 11 }} />
            <ZAxis range={[70, 70]} />
            <Tooltip
              content={({ payload }) => {
                const p = payload?.[0]?.payload as Point | undefined;
                return p ? <div className="rounded-md border border-line bg-surface px-2 py-1 text-xs shadow-sm"><b>{p.label}</b><br />{p.group}</div> : null;
              }}
            />
            {groups.map((g, i) => (
              <Scatter key={g} name={g} data={points.filter((p) => (p.group ?? "Other") === g)} fill={PALETTE[i % PALETTE.length]}>
                <LabelList dataKey="label" position="top" style={{ fontSize: 10, fill: "var(--color-ink)" }} />
              </Scatter>
            ))}
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
        {groups.map((g, i) => (
          <li key={g} className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full" style={{ background: PALETTE[i % PALETTE.length] }} />{g}</li>
        ))}
      </ul>
    </div>
  );
}
