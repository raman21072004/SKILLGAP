import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { buttonVariants } from "@/components/ui/button";
import { Logo } from "@/components/layout/Logo";
import { EvidenceBar, type BarItem } from "@/charts/EvidenceBar";
import { VerdictBadge } from "@/features/analysis/VerdictBadge";
import { useAuth } from "@/store/auth";

// Real output of SkillGap-NLP (TF-IDF mode) on data/sample_data: the bundled example
// resume against the bundled junior NLP engineer job description. Coverage 61.5%.
const m = (skill: string, verdict: BarItem["verdict"]): BarItem => ({ skill, verdict, weight: 2, importance: "must_have" });
const n = (skill: string, verdict: BarItem["verdict"]): BarItem => ({ skill, verdict, weight: 1, importance: "nice_to_have" });
const SAMPLE: BarItem[] = [
  m("Python", "direct_match"), m("Machine Learning", "direct_match"), m("Deep Learning", "direct_match"), m("PyTorch", "direct_match"),
  m("Natural Language Processing", "direct_match"), m("Word Embeddings", "direct_match"), m("REST APIs", "direct_match"), m("Flask", "direct_match"),
  m("SQL", "direct_match"), m("Docker", "direct_match"), m("Git", "direct_match"), m("Communication", "direct_match"),
  m("PostgreSQL", "related"), m("TensorFlow", "related"), m("Transformers", "related"), m("Text Classification", "related"), m("FastAPI", "related"),
  n("CI/CD", "related"), n("Kubernetes", "related"), n("MLOps", "related"), n("AWS", "missing"), n("Cloud Computing", "missing"),
];

const STEPS = [
  ["Read", "Text is extracted from your PDF, DOCX or pasted resume, split into sections and sentences, and never executed or shared."],
  ["Extract", "A taxonomy of 100 skills with aliases finds every requirement in the job ad and every skill your resume names, with its exact sentence."],
  ["Match", "Each requirement is checked by keyword, TF-IDF and a sentence-transformer. Similar wording is flagged for you to confirm, never counted as proof."],
  ["Plan", "Gaps become an ordered learning roadmap with prerequisites, a practice project and documentation links you can track."],
];

export default function LandingPage() {
  const status = useAuth((s) => s.status);
  const signedIn = status === "authenticated";
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5">
        <Logo />
        <nav className="flex items-center gap-2">
          {signedIn ? (
            <Link to="/dashboard" className={buttonVariants({ variant: "primary", size: "sm" })}>Open dashboard</Link>
          ) : (
            <>
              <Link to="/login" className={buttonVariants({ variant: "ghost", size: "sm" })}>Sign in</Link>
              <Link to="/register" className={buttonVariants({ variant: "primary", size: "sm" })}>Create account</Link>
            </>
          )}
        </nav>
      </header>

      <main>
        <section className="mx-auto grid max-w-6xl gap-12 px-5 pb-20 pt-10 lg:grid-cols-[1.05fr_1fr] lg:items-center lg:pt-16">
          <div>
            <h1 className="text-4xl font-bold leading-[1.05] sm:text-5xl lg:text-[3.6rem]">
              Which job requirements does your resume actually prove?
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-muted">
              SkillGap-NLP reads your resume and a job description, shows the sentence behind every match,
              separates real evidence from look-alike wording, and turns the gaps into a learning plan.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to={signedIn ? "/analyses/new" : "/register"} className={buttonVariants({ size: "lg" })}>Analyse my resume</Link>
              <a href="#how" className={buttonVariants({ variant: "secondary", size: "lg" })}>See how it works</a>
            </div>
          </div>

          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
            className="rounded-2xl border border-line bg-surface p-6 shadow-[0_24px_60px_-30px_rgba(19,98,79,0.35)]">
            <div className="flex items-baseline justify-between">
              <div>
                <p className="text-sm font-semibold">Sample analysis</p>
                <p className="text-xs text-muted">Bundled example resume vs. junior NLP engineer job ad</p>
              </div>
              <p className="font-display text-4xl font-bold text-pine">61.5%</p>
            </div>
            <div className="mt-5"><EvidenceBar items={SAMPLE} /></div>
            <ul className="mt-6 divide-y divide-line text-sm">
              <li className="flex items-center justify-between gap-3 py-2.5"><span><b>PyTorch</b><span className="block text-xs text-muted">“Trained an LSTM model in PyTorch to classify movie reviews…”</span></span><VerdictBadge verdict="direct_match" /></li>
              <li className="flex items-center justify-between gap-3 py-2.5"><span><b>PostgreSQL</b><span className="block text-xs text-muted">You show MySQL and SQL, which are related but not the same.</span></span><VerdictBadge verdict="related" /></li>
              <li className="flex items-center justify-between gap-3 py-2.5"><span><b>AWS</b><span className="block text-xs text-muted">No mention and no similar sentence. Added to the roadmap.</span></span><VerdictBadge verdict="missing" /></li>
            </ul>
          </motion.div>
        </section>

        <section className="border-y border-line bg-surface">
          <div className="mx-auto grid max-w-6xl gap-10 px-5 py-16 md:grid-cols-[1fr_1.4fr]">
            <h2 className="text-3xl font-bold">Keyword checkers say yes or no. Hiring managers read sentences.</h2>
            <div className="space-y-4 text-muted leading-relaxed">
              <p>Most resume checkers count keywords, so “Java” in a skills list looks the same as two years of Java in production, and a sentiment-analysis project scores zero against “text classification” because the words differ.</p>
              <p>SkillGap-NLP keeps those cases apart. A skill named in a project bullet counts as shown. A skill only listed gets a nudge to add evidence. A semantically similar sentence is marked “verify” so you decide. Related skills, like Java for a Python role, are called transferable, not equal.</p>
            </div>
          </div>
        </section>

        <section id="how" className="mx-auto max-w-6xl px-5 py-16">
          <h2 className="text-3xl font-bold">How an analysis runs</h2>
          <ol className="mt-10 grid gap-8 md:grid-cols-4">
            {STEPS.map(([title, body], i) => (
              <li key={title} className="border-t-2 border-pine pt-4">
                <span className="font-display text-sm font-bold text-pine">Step {i + 1}</span>
                <h3 className="mt-1 text-xl font-bold">{title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">{body}</p>
              </li>
            ))}
          </ol>
          <dl className="mt-16 grid gap-x-10 gap-y-6 border-t border-line pt-10 sm:grid-cols-2">
            {[
              ["Explainable coverage score", "The score is the weighted share of requirements with real evidence. Must-haves count double by default, and you can change the weights."],
              ["Evidence you can inspect", "Every verdict links to the exact sentence in your resume, highlighted in place, with the method and similarity that produced it."],
              ["Corrections that stick", "Disagree with a verdict? Change it. Your correction is stored next to the original and the score and roadmap update."],
              ["An NLP lab for your viva", "Tokenisation, stemming, Bag of Words, TF-IDF, Word2Vec, GloVe, cosine similarity, analogies, PCA and t-SNE on your own text."],
            ].map(([t, d]) => (
              <div key={t}><dt className="font-bold">{t}</dt><dd className="mt-1 text-sm text-muted">{d}</dd></div>
            ))}
          </dl>
        </section>

        <section className="bg-pine text-white">
          <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-6 px-5 py-14 md:flex-row md:items-center">
            <h2 className="max-w-xl text-3xl font-bold">Bring one resume and one job ad. Leave with a plan.</h2>
            <Link to={signedIn ? "/analyses/new" : "/register"} className="inline-flex h-12 items-center rounded-lg bg-white px-6 font-semibold text-pine hover:bg-paper">
              Start an analysis
            </Link>
          </div>
        </section>
      </main>

      <footer className="mx-auto max-w-6xl px-5 py-8 text-xs text-muted">
        SkillGap-NLP is a B.Tech AI &amp; ML academic project and a career-development aid. It does not make hiring decisions and never infers personal characteristics.
      </footer>
    </div>
  );
}
