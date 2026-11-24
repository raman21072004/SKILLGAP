export type Classification = "direct_match" | "strong_semantic" | "related" | "missing";
export type Mode = "keyword" | "tfidf" | "semantic";
export type TaskStatus = "not_started" | "learning" | "practiced" | "completed";

export interface User {
  id: number;
  email: string;
  full_name: string;
  preferences: { default_mode?: Mode; count_strong_semantic?: boolean; equal_weights?: boolean; retention_days?: number };
  created_at: string;
}

export interface Evidence {
  text: string;
  section: string | null;
  start: number | null;
  end: number | null;
  match_start: number | null;
  match_end: number | null;
  matched_text: string | null;
  kind: "exact" | "semantic" | "related";
  strength: "demonstrated" | "mentioned" | "listed" | null;
}

export interface Requirement {
  match_id: number;
  canonical: string;
  category: string;
  importance: "must_have" | "nice_to_have";
  weight: number;
  requirement_text: string | null;
  requirement_source: string;
  exact_match: boolean;
  classification: Classification;
  user_classification: Classification | null;
  effective_classification: Classification;
  classification_label: string;
  similarity: number | null;
  tfidf_similarity: number | null;
  semantic_similarity: number | null;
  similarity_backend: string | null;
  related_skills_found: string[];
  method: string | null;
  explanation: string;
  next_action: string;
  uncertainty: string | null;
  evidence: Evidence | null;
}

export interface Coverage {
  coverage_score: number;
  must_have_coverage: number | null;
  nice_to_have_coverage: number | null;
  accepted_weight: number;
  total_weight: number;
  counts: Record<Classification, number>;
  contributions: { canonical: string; weight: number; accepted: boolean; points: number; classification: Classification }[];
  formula: string;
  accepted_classes: string[];
}

export interface MethodResult {
  method: Mode;
  label: string;
  available: boolean;
  matched: string[];
  related: string[];
  missing: string[];
  scores: Record<string, number>;
  time_ms: number | null;
  limitations: string;
}

export interface ModelInfo {
  mode: Mode;
  similarity_backend: string | null;
  semantic_available: boolean;
  semantic_model: string | null;
  fallback_used: boolean;
  fallback_reason: string | null;
  thresholds: Record<string, number>;
  processing_ms?: number;
}

export interface AnalysisDetail {
  id: number;
  created_at: string;
  job_title: string | null;
  target_role: string | null;
  mode: Mode;
  coverage: Coverage;
  document_similarity: { tfidf: number | null; semantic: number | null; note: string | null };
  model_info: ModelInfo;
  requirements: Requirement[];
  candidate_skills: { canonical: string; category: string; strength: string; mention_count: number }[];
  model_comparison: MethodResult[];
  resume_text: string | null;
  resume_sections: { name: string; heading: string | null; start: number; end: number }[];
  job_description: string | null;
  warnings: string[];
  unrecognized_job_terms: { term: string; score: number }[];
  roadmap_progress: Progress | null;
  disclaimer: string;
}

export interface AnalysisSummary {
  id: number;
  created_at: string;
  job_title: string | null;
  target_role: string | null;
  mode: Mode;
  coverage_score: number;
  must_have_coverage: number | null;
  nice_to_have_coverage: number | null;
  requirement_count: number;
  direct_count: number;
  missing_count: number;
  similarity_backend: string | null;
  fallback_used: boolean;
}

export interface Paginated<T> { items: T[]; total: number; page: number; page_size: number }

export interface Progress {
  total: number;
  by_status: Record<TaskStatus, number>;
  completed_percent: number;
  remaining_gaps: string[];
  note: string;
}

export interface Task {
  id: number;
  skill: string;
  category: string;
  importance: string;
  gap_type: Classification;
  priority: "high" | "medium" | "low";
  order: number;
  level: string;
  reason: string;
  prerequisites: { skill: string; status: string }[];
  project: string;
  estimated_effort: string;
  checklist: string[];
  checklist_done: number[];
  resources: { title: string; url: string; type: string }[];
  resources_note: string | null;
  status: TaskStatus;
}

export interface Roadmap {
  analysis_id: number;
  target_role: string | null;
  tasks: Task[];
  progress: Progress;
  verified_coverage: number;
  disclaimer: string;
}

export interface Dashboard {
  analysis_count: number;
  average_coverage: number | null;
  best_coverage: number | null;
  recent: AnalysisSummary[];
  frequently_missing: { skill: string; count: number }[];
  roadmap: { total_tasks: number; by_status: Record<TaskStatus, number>; completed_percent: number | null };
  coverage_trend: { id: number; date: string; coverage: number; label: string }[];
}

export interface ApiErrorBody { error: { code: string; message: string; details?: { field: string; message: string }[] | null } }
