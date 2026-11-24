import axios, { AxiosError } from "axios";
import type {
  AnalysisDetail, AnalysisSummary, ApiErrorBody, Classification, Dashboard, Mode, Paginated, Roadmap, Task, TaskStatus, User,
} from "@/types/api";

// Same-origin requests (Vite proxies /api to the backend). The session lives in an
// httpOnly cookie, so no token is ever stored in localStorage.
export const http = axios.create({ baseURL: "", withCredentials: true, timeout: 180_000 });

export function errorMessage(err: unknown, fallback = "Something went wrong. Try again."): string {
  if (err instanceof AxiosError) {
    const body = err.response?.data as ApiErrorBody | undefined;
    if (body?.error) {
      const details = body.error.details?.map((d) => d.message).filter(Boolean);
      return details?.length ? `${body.error.message} ${details.join(" ")}` : body.error.message;
    }
    if (err.code === "ECONNABORTED") return "The server took too long to respond.";
    if (!err.response) return "Cannot reach the backend. Check that it is running on port 8000.";
  }
  return fallback;
}

export const authApi = {
  me: () => http.get<User>("/api/auth/me").then((r) => r.data),
  login: (email: string, password: string) => http.post<{ user: User }>("/api/auth/login", { email, password }).then((r) => r.data.user),
  register: (full_name: string, email: string, password: string) =>
    http.post<{ user: User }>("/api/auth/register", { full_name, email, password }).then((r) => r.data.user),
  logout: () => http.post("/api/auth/logout"),
};

export interface CreateAnalysisInput {
  resume_id?: number | null;
  resume_text?: string | null;
  job_description: string;
  job_title?: string | null;
  target_role?: string | null;
  mode: Mode;
  must_have_skills: string[];
  nice_to_have_skills: string[];
  equal_weights: boolean;
  count_strong_semantic: boolean;
}

export interface UploadResult { resume_id: number; filename: string | null; file_type: string; char_count: number; page_count: number | null; text: string }

export const analysisApi = {
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return http.post<UploadResult>("/api/resumes/upload", form).then((r) => r.data);
  },
  create: (input: CreateAnalysisInput) => http.post<AnalysisDetail>("/api/analyses", input).then((r) => r.data),
  list: (page = 1, pageSize = 10) =>
    http.get<Paginated<AnalysisSummary>>("/api/analyses", { params: { page, page_size: pageSize } }).then((r) => r.data),
  get: (id: number | string) => http.get<AnalysisDetail>(`/api/analyses/${id}`).then((r) => r.data),
  remove: (id: number) => http.delete(`/api/analyses/${id}`),
  correct: (id: number, matchId: number, corrected: Classification | null, comment?: string) =>
    http.patch<AnalysisDetail>(`/api/analyses/${id}/matches/${matchId}`, { corrected_classification: corrected, comment }).then((r) => r.data),
  roadmap: (id: number | string) => http.get<Roadmap>(`/api/analyses/${id}/roadmap`).then((r) => r.data),
  updateTask: (taskId: number, body: { status?: TaskStatus; checklist_done?: number[] }) =>
    http.patch<{ task: Task; progress: Roadmap["progress"] }>(`/api/roadmap/tasks/${taskId}`, body).then((r) => r.data),
  dashboard: () => http.get<Dashboard>("/api/dashboard").then((r) => r.data),
  exportOne: (id: number | string) => http.get(`/api/analyses/${id}/export`).then((r) => r.data),
};

export const userApi = {
  update: (body: { full_name?: string; preferences?: User["preferences"] }) => http.patch<User>("/api/users/me", body).then((r) => r.data),
  exportAll: () => http.get("/api/users/me/export").then((r) => r.data),
  privacy: () => http.get<{ retention_days: number; stores_original_files: boolean; statement: string }>("/api/users/me/privacy").then((r) => r.data),
  deleteAccount: (password: string) => http.post("/api/users/me/delete", { password }),
};

/* eslint-disable @typescript-eslint/no-explicit-any */
export const labApi = {
  preprocessing: (params: { text: string; lowercase: boolean; remove_stopwords: boolean; lemmatize: boolean; ngram_n: number }) =>
    http.get<any>("/api/nlp/preprocessing", { params }).then((r) => r.data),
  bow: (doc_a: string, doc_b: string) => http.post<any>("/api/nlp/bow", { doc_a, doc_b }).then((r) => r.data),
  tfidf: (doc_a: string, doc_b: string) => http.post<any>("/api/nlp/tfidf", { doc_a, doc_b }).then((r) => r.data),
  vectors: (text: string, corpus: string[]) => http.post<any>("/api/nlp/vectors", { text, corpus }).then((r) => r.data),
  word2vec: (words: string[], architecture: "cbow" | "skipgram") => http.post<any>("/api/nlp/word2vec", { words, architecture }).then((r) => r.data),
  compareW2v: (words: string[], window: number, vector_size: number) =>
    http.post<any>("/api/nlp/word2vec/compare", { words, window, vector_size }).then((r) => r.data),
  glove: (words: string[]) => http.post<any>("/api/nlp/glove", { words }).then((r) => r.data),
  analogy: (model: string, positive: string[], negative: string[]) => http.post<any>("/api/nlp/analogy", { model, positive, negative }).then((r) => r.data),
  similarity: (text_a: string, text_b: string) => http.post<any>("/api/nlp/similarity", { text_a, text_b }).then((r) => r.data),
  visualize: (body: { source: string; method: string; items: string[]; perplexity: number; seed: number }) =>
    http.post<any>("/api/nlp/visualize", body).then((r) => r.data),
  compareModels: (resume_text: string, job_description: string) =>
    http.post<any>("/api/nlp/compare-models", { resume_text, job_description }).then((r) => r.data),
  status: () => http.get<any>("/api/nlp/models/status").then((r) => r.data),
  taxonomy: () => http.get<{ skills: { canonical: string; category: string }[] }>("/api/nlp/taxonomy").then((r) => r.data),
};

export function downloadJson(data: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
