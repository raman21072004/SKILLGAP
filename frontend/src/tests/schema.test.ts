import { analysisSchema, loginSchema, registerSchema, splitSkills, validateFile } from "@/features/analysis/schema";

const base = { resume_text: "", resume_id: null, job_description: "x".repeat(40), mode: "semantic" as const, equal_weights: false, count_strong_semantic: false };

describe("analysis form validation", () => {
  it("requires a resume upload or pasted text", () => {
    const r = analysisSchema.safeParse(base);
    expect(r.success).toBe(false);
    if (!r.success) expect(r.error.issues[0].path).toEqual(["resume_text"]);
  });
  it("accepts an uploaded resume id without pasted text", () => {
    expect(analysisSchema.safeParse({ ...base, resume_id: 3 }).success).toBe(true);
  });
  it("rejects a short job description", () => {
    expect(analysisSchema.safeParse({ ...base, resume_text: "y".repeat(40), job_description: "short" }).success).toBe(false);
  });
  it("splits comma separated skills", () => {
    expect(splitSkills(" Python, ,SQL ,Docker")).toEqual(["Python", "SQL", "Docker"]);
  });
});

describe("auth validation", () => {
  it("validates email and password rules", () => {
    expect(loginSchema.safeParse({ email: "nope", password: "x" }).success).toBe(false);
    expect(registerSchema.safeParse({ full_name: "Ann", email: "a@b.co", password: "abcdefgh" }).success).toBe(false);
    expect(registerSchema.safeParse({ full_name: "Ann", email: "a@b.co", password: "abc12345" }).success).toBe(true);
  });
});

describe("file validation", () => {
  it("rejects unsupported and oversized files", () => {
    expect(validateFile(new File(["x"], "cv.exe"))).toMatch(/PDF, DOCX or TXT/);
    expect(validateFile(new File([], "cv.pdf"))).toMatch(/empty/);
    expect(validateFile(new File(["hello"], "cv.PDF"))).toBeNull();
  });
});
