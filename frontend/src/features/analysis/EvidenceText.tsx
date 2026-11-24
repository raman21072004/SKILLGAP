import { Fragment, useEffect, useMemo, useRef } from "react";
import type { Requirement } from "@/types/api";

/** Renders the original resume text with every evidence sentence highlighted in place. */
export function EvidenceText({ text, requirements, activeSkill }: { text: string; requirements: Requirement[]; activeSkill: string | null }) {
  const activeRef = useRef<HTMLElement | null>(null);
  const spans = useMemo(() => {
    const list = requirements
      .filter((r) => r.evidence && r.evidence.start !== null && r.evidence.end !== null)
      .map((r) => ({ start: r.evidence!.start!, end: r.evidence!.end!, skills: [r.canonical] }));
    list.sort((a, b) => a.start - b.start);
    const merged: typeof list = [];
    for (const s of list) {
      const last = merged[merged.length - 1];
      if (last && s.start < last.end) {
        last.end = Math.max(last.end, s.end);
        last.skills.push(...s.skills);
      } else merged.push({ ...s, skills: [...s.skills] });
    }
    return merged;
  }, [requirements]);

  useEffect(() => {
    activeRef.current?.scrollIntoView({ block: "center", behavior: "smooth" });
  }, [activeSkill]);

  const parts: JSX.Element[] = [];
  let pos = 0;
  spans.forEach((s, i) => {
    if (s.start > pos) parts.push(<Fragment key={`t${i}`}>{text.slice(pos, s.start)}</Fragment>);
    const active = activeSkill !== null && s.skills.includes(activeSkill);
    parts.push(
      <mark key={`m${i}`} ref={active ? (el) => { activeRef.current = el; } : undefined} className={active ? "evidence evidence-active" : "evidence"} title={`Evidence for: ${s.skills.join(", ")}`}>
        {text.slice(s.start, s.end)}
      </mark>,
    );
    pos = s.end;
  });
  if (pos < text.length) parts.push(<Fragment key="end">{text.slice(pos)}</Fragment>);

  return <pre className="max-h-[32rem] overflow-auto whitespace-pre-wrap font-sans text-sm leading-relaxed text-ink">{parts}</pre>;
}
