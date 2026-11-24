import type { Classification, TaskStatus } from "@/types/api";

export const VERDICT: Record<Classification, { label: string; short: string; color: string; soft: string; text: string }> = {
  direct_match: { label: "Shown in resume", short: "Shown", color: "var(--color-shown)", soft: "var(--color-pine-soft)", text: "text-[var(--color-shown)]" },
  strong_semantic: { label: "Likely, needs your confirmation", short: "Verify", color: "var(--color-verify)", soft: "var(--color-verify-soft)", text: "text-[#8a5c0a]" },
  related: { label: "Related skill only", short: "Related", color: "var(--color-related)", soft: "var(--color-related-soft)", text: "text-[var(--color-related)]" },
  missing: { label: "Not shown in resume", short: "Not shown", color: "var(--color-missing)", soft: "var(--color-missing-soft)", text: "text-[var(--color-missing)]" },
};

export const STATUS_LABEL: Record<TaskStatus, string> = {
  not_started: "Not started",
  learning: "Learning",
  practiced: "Practiced",
  completed: "Completed",
};

export const MODE_LABEL = {
  semantic: "Deep semantic (recommended)",
  tfidf: "TF-IDF similarity",
  keyword: "Keyword only",
} as const;

export function pct(v: number | null | undefined, digits = 0): string {
  return v === null || v === undefined ? "n/a" : `${v.toFixed(digits)}%`;
}

export function num(v: number | null | undefined, digits = 2): string {
  return v === null || v === undefined ? "n/a" : v.toFixed(digits);
}

export function date(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

export const SECTION_LABEL: Record<string, string> = {
  experience: "Experience", projects: "Projects", skills: "Skills", education: "Education", summary: "Summary",
  certifications: "Certifications", achievements: "Achievements", publications: "Publications", body: "Resume", header: "Header",
};
