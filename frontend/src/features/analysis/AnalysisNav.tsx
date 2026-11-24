import { NavLink } from "react-router-dom";
import { cn } from "@/utils/cn";

export function AnalysisNav({ id, title }: { id: number | string; title: string }) {
  const tab = ({ isActive }: { isActive: boolean }) =>
    cn("rounded-md px-3 py-1.5 text-sm font-semibold", isActive ? "bg-pine text-white" : "text-muted hover:bg-paper hover:text-ink");
  return (
    <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
      <h1 className="text-2xl font-bold sm:text-3xl">{title}</h1>
      <nav aria-label="Analysis views" className="flex gap-1 rounded-lg border border-line bg-surface p-1">
        <NavLink end to={`/analyses/${id}`} className={tab}>Results</NavLink>
        <NavLink to={`/analyses/${id}/skills`} className={tab}>Skill explorer</NavLink>
        <NavLink to={`/analyses/${id}/roadmap`} className={tab}>Roadmap</NavLink>
      </nav>
    </div>
  );
}
