import { zodResolver } from "@hookform/resolvers/zod";
import { FileUp, X } from "lucide-react";
import { useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { FieldError, Hint, Input, Label, Textarea } from "@/components/ui/form";
import { Notice } from "@/components/ui/misc";
import { analysisSchema, splitSkills, validateFile, type AnalysisForm } from "@/features/analysis/schema";
import { analysisApi, errorMessage, type UploadResult } from "@/services/api";
import { useAuth } from "@/store/auth";
import { MODE_LABEL } from "@/utils/format";

const MODE_HELP = {
  semantic: "Keyword matching plus a sentence-transformer that recognises paraphrases. Falls back to TF-IDF, and says so, if the model is not installed.",
  tfidf: "Keyword matching plus lexical TF-IDF similarity. Fast and needs no model download.",
  keyword: "Only exact skill names and aliases. Highest precision, misses paraphrases.",
};

export default function NewAnalysisPage() {
  const navigate = useNavigate();
  const prefs = useAuth((s) => s.user?.preferences);
  const fileInput = useRef<HTMLInputElement>(null);
  const [upload, setUpload] = useState<UploadResult | null>(null);
  const [uploading, setUploading] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const { register, handleSubmit, setValue, watch, formState: { errors, isSubmitting } } = useForm<AnalysisForm>({
    resolver: zodResolver(analysisSchema),
    defaultValues: {
      resume_text: "", resume_id: null, job_description: "", job_title: "", mode: prefs?.default_mode ?? "semantic",
      must_have: "", nice_to_have: "", equal_weights: prefs?.equal_weights ?? false, count_strong_semantic: prefs?.count_strong_semantic ?? false,
    },
  });
  const mode = watch("mode");
  const resumeText = watch("resume_text");

  const onFile = async (file: File | undefined) => {
    if (!file) return;
    const problem = validateFile(file);
    if (problem) {
      toast.error(problem);
      return;
    }
    setUploading(true);
    try {
      const res = await analysisApi.upload(file);
      setUpload(res);
      setValue("resume_id", res.resume_id);
      setValue("resume_text", res.text, { shouldValidate: true });
      toast.success(`Extracted ${res.char_count.toLocaleString()} characters from ${res.filename}`);
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  };

  const clearUpload = () => {
    setUpload(null);
    setValue("resume_id", null);
    setValue("resume_text", "");
  };

  const onSubmit = handleSubmit(async (v) => {
    setServerError(null);
    try {
      const result = await analysisApi.create({
        resume_id: v.resume_id,
        resume_text: v.resume_text.trim() || null,
        job_description: v.job_description,
        job_title: v.job_title || null,
        target_role: v.job_title || null,
        mode: v.mode,
        must_have_skills: splitSkills(v.must_have),
        nice_to_have_skills: splitSkills(v.nice_to_have),
        equal_weights: v.equal_weights,
        count_strong_semantic: v.count_strong_semantic,
      });
      toast.success("Analysis ready");
      navigate(`/analyses/${result.id}`);
    } catch (e) {
      setServerError(errorMessage(e));
    }
  });

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">New analysis</h1>
        <p className="mt-1 text-muted">Add your resume and the job you are aiming for. Nothing is shared outside your account.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Your resume" description="Upload a PDF, DOCX or TXT (up to 5 MB), or paste the text. You can edit extracted text before analysing." />
          <CardBody className="space-y-3">
            <div className="flex flex-wrap items-center gap-3">
              <input ref={fileInput} type="file" accept=".pdf,.docx,.txt" className="sr-only" id="resume-file" onChange={(e) => onFile(e.target.files?.[0])} />
              <Button type="button" variant="secondary" loading={uploading} onClick={() => fileInput.current?.click()}>
                <FileUp className="h-4 w-4" aria-hidden /> Upload file
              </Button>
              {upload && (
                <span className="inline-flex items-center gap-2 rounded-lg bg-pine-soft px-3 py-1.5 text-sm">
                  {upload.filename}
                  <button type="button" onClick={clearUpload} aria-label="Remove uploaded file" className="rounded p-0.5 hover:bg-white"><X className="h-3.5 w-3.5" /></button>
                </span>
              )}
            </div>
            <div>
              <Label htmlFor="resume_text">Resume text</Label>
              <Textarea id="resume_text" rows={16} placeholder={"EXPERIENCE\n- Built REST APIs in Python with Flask…"} aria-invalid={!!errors.resume_text} {...register("resume_text")} />
              <div className="flex justify-between">
                <FieldError message={errors.resume_text?.message} />
                <span className="mt-1 text-xs text-muted tabular-nums">{resumeText.length.toLocaleString()} characters</span>
              </div>
            </div>
            <Hint>Scanned PDFs have no text layer. If extraction fails, run OCR first or paste the text.</Hint>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="The job" description="Paste the full job description, including requirement and nice-to-have lists." />
          <CardBody className="space-y-4">
            <div>
              <Label htmlFor="job_title">Job title (optional)</Label>
              <Input id="job_title" placeholder="Junior NLP Engineer" {...register("job_title")} />
            </div>
            <div>
              <Label htmlFor="job_description">Job description</Label>
              <Textarea id="job_description" rows={13} aria-invalid={!!errors.job_description} {...register("job_description")} />
              <FieldError message={errors.job_description?.message} />
            </div>
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader title="Analysis settings" description="Defaults work well. Adjust them to test how the result changes." />
        <CardBody className="grid gap-6 md:grid-cols-2">
          <fieldset>
            <legend className="mb-2 text-sm font-semibold">Matching method</legend>
            <div className="space-y-2">
              {(Object.keys(MODE_LABEL) as (keyof typeof MODE_LABEL)[]).map((m) => (
                <label key={m} className={`flex cursor-pointer gap-3 rounded-lg border p-3 text-sm ${mode === m ? "border-pine bg-pine-soft" : "border-line"}`}>
                  <input type="radio" value={m} className="mt-1 accent-[var(--color-pine)]" {...register("mode")} />
                  <span><span className="font-semibold">{MODE_LABEL[m]}</span><span className="block text-xs text-muted">{MODE_HELP[m]}</span></span>
                </label>
              ))}
            </div>
          </fieldset>
          <div className="space-y-4">
            <div>
              <Label htmlFor="must_have">Extra must-have skills</Label>
              <Input id="must_have" placeholder="e.g. Python, SQL" {...register("must_have")} />
              <Hint>Comma separated. Overrides what was detected in the job ad.</Hint>
            </div>
            <div>
              <Label htmlFor="nice_to_have">Extra nice-to-have skills</Label>
              <Input id="nice_to_have" placeholder="e.g. Docker, AWS" {...register("nice_to_have")} />
            </div>
            <label className="flex items-start gap-2 text-sm">
              <input type="checkbox" className="mt-0.5 h-4 w-4 accent-[var(--color-pine)]" {...register("equal_weights")} />
              <span>Weight all requirements equally <span className="block text-xs text-muted">By default must-haves count 2 and nice-to-haves count 1.</span></span>
            </label>
            <label className="flex items-start gap-2 text-sm">
              <input type="checkbox" className="mt-0.5 h-4 w-4 accent-[var(--color-pine)]" {...register("count_strong_semantic")} />
              <span>Count “verify” matches toward coverage <span className="block text-xs text-muted">Off by default, because similar wording does not prove a skill.</span></span>
            </label>
          </div>
        </CardBody>
      </Card>

      {serverError && <p role="alert" className="rounded-lg bg-missing-soft px-4 py-3 text-sm text-missing">{serverError}</p>}
      {isSubmitting && mode === "semantic" && (
        <Notice>The first semantic analysis loads the language model, which can take up to a minute. Later analyses are fast.</Notice>
      )}
      <div className="flex justify-end">
        <Button type="submit" size="lg" loading={isSubmitting}>{isSubmitting ? "Analysing…" : "Run analysis"}</Button>
      </div>
    </form>
  );
}
