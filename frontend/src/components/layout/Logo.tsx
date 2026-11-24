import { Link } from "react-router-dom";

/** The mark is a miniature evidence bar: shown / verify / not shown. */
export function Logo({ to = "/" }: { to?: string }) {
  return (
    <Link to={to} className="flex items-center gap-2.5 font-display text-lg font-bold tracking-tight">
      <span className="flex h-7 items-center gap-[3px] rounded-md bg-pine px-1.5" aria-hidden>
        <span className="h-3 w-3.5 rounded-sm bg-paper" />
        <span className="h-3 w-1.5 rounded-sm bg-verify" />
        <span className="h-3 w-1.5 rounded-sm bg-paper/35" />
      </span>
      SkillGap<span className="text-muted font-medium">NLP</span>
    </Link>
  );
}
