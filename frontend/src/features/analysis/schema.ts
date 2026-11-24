import { z } from "zod";

export const analysisSchema = z
  .object({
    resume_text: z.string().max(60000, "Resume text is too long (60,000 characters max)."),
    resume_id: z.number().nullable(),
    job_description: z.string().trim().min(30, "Paste the job description (at least 30 characters).").max(60000, "Job description is too long."),
    job_title: z.string().max(200).optional(),
    mode: z.enum(["keyword", "tfidf", "semantic"]),
    must_have: z.string().max(2000).optional(),
    nice_to_have: z.string().max(2000).optional(),
    equal_weights: z.boolean(),
    count_strong_semantic: z.boolean(),
  })
  .refine((v) => v.resume_id !== null || v.resume_text.trim().length >= 30, {
    message: "Upload a resume or paste at least 30 characters of resume text.",
    path: ["resume_text"],
  });

export type AnalysisForm = z.infer<typeof analysisSchema>;

export function splitSkills(raw?: string): string[] {
  return (raw ?? "").split(",").map((s) => s.trim()).filter(Boolean);
}

export const loginSchema = z.object({
  email: z.string().trim().email("Enter a valid email address."),
  password: z.string().min(1, "Enter your password."),
});

export const registerSchema = z.object({
  full_name: z.string().trim().min(2, "Enter your name."),
  email: z.string().trim().email("Enter a valid email address."),
  password: z
    .string()
    .min(8, "Use at least 8 characters.")
    .regex(/[A-Za-z]/, "Include at least one letter.")
    .regex(/\d/, "Include at least one number."),
});

export const ALLOWED_UPLOADS = [".pdf", ".docx", ".txt"];
export const MAX_UPLOAD_MB = 5;

export function validateFile(file: File): string | null {
  const ext = file.name.toLowerCase().slice(file.name.lastIndexOf("."));
  if (!ALLOWED_UPLOADS.includes(ext)) return "Upload a PDF, DOCX or TXT file.";
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) return `The file is larger than ${MAX_UPLOAD_MB} MB.`;
  if (file.size === 0) return "The file is empty.";
  return null;
}
