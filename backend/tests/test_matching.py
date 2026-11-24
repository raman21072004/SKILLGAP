import numpy as np
import pytest

from app.nlp.config import NLPConfig
from app.nlp.extraction.sections import split_sentences
from app.nlp.pipeline import AnalysisInputError, AnalysisOptions, run_analysis
from app.nlp.similarity.cosine import cosine_breakdown, cosine_similarity
from app.nlp.skill_extraction.extractor import RequiredSkill, extract_candidate_skills
from app.nlp.skill_gap.analyzer import analyze_gaps
from app.nlp.skill_gap.scoring import compute_coverage
from tests.conftest import SAMPLE_JOB, SAMPLE_RESUME


class FixedEncoder:
    """Encoder returning a fixed similarity for every (query, sentence) pair."""

    def __init__(self, sim: float):
        self.name, self.available, self.error = "fixed", True, None
        self.sim = sim

    def encode(self, texts):
        # queries contain ':' (skill query_text); sentences do not
        a = np.array([1.0, 0.0])
        b = np.array([self.sim, np.sqrt(1 - self.sim**2)])
        return np.stack([a if ":" in t else b for t in texts])


class Unavailable:
    name, available, error = "missing-model", False, "model not installed"

    def encode(self, texts):
        raise RuntimeError("unavailable")


def _req(taxonomy, name, importance="must_have", weight=2.0):
    s = taxonomy.skills[name]
    return RequiredSkill(name, s.category, importance, weight, name)


def _run(taxonomy, resume, reqs, encoder, mode="semantic"):
    sents = split_sentences(resume)
    cand = extract_candidate_skills(resume, taxonomy)
    return analyze_gaps(sents, cand, reqs, taxonomy, mode=mode, encoder=encoder, config=NLPConfig())


def test_cosine_similarity_basics():
    assert cosine_similarity([1, 0], [1, 0]) == pytest.approx(1.0)
    assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)
    assert cosine_similarity([1, 1], [2, 2]) == pytest.approx(1.0)   # magnitude does not matter
    assert cosine_similarity([0, 0], [1, 1]) == 0.0
    assert cosine_breakdown([1, 0], [0, 1])["angle_degrees"] == 90.0
    with pytest.raises(ValueError):
        cosine_similarity([1, 2], [1, 2, 3])


def test_direct_match_and_missing(taxonomy):
    out = _run(taxonomy, "PROJECTS\nBuilt APIs in Python.", [_req(taxonomy, "Python"), _req(taxonomy, "Kubernetes")], Unavailable(), mode="keyword")
    cls = {r["canonical"]: r["classification"] for r in out["requirements"]}
    assert cls == {"Python": "direct_match", "Kubernetes": "missing"}


def test_java_does_not_prove_python(taxonomy):
    # Even with a very high semantic score, a sentence that names Java is not evidence of Python.
    out = _run(taxonomy, "EXPERIENCE\nBuilt backend services in Java.", [_req(taxonomy, "Python")], FixedEncoder(0.95))
    r = out["requirements"][0]
    assert r["classification"] == "related"
    assert r["exact_match"] is False
    assert "capped" in r["method"]


def test_strong_semantic_requires_verification(taxonomy):
    resume = "PROJECTS\nTrained a classifier that labels reviews as positive or negative."
    out = _run(taxonomy, resume, [_req(taxonomy, "Text Classification")], FixedEncoder(0.9))
    r = out["requirements"][0]
    assert r["classification"] == "strong_semantic"
    assert r["evidence"]["text"] in resume          # evidence is real resume text
    assert "verif" in (r["uncertainty"] or "").lower()


def test_fallback_is_reported_not_hidden(taxonomy):
    out = _run(taxonomy, "PROJECTS\nBuilt APIs in Python.", [_req(taxonomy, "Docker")], Unavailable())
    assert out["fallback_used"] is True
    assert out["similarity_backend"] == "tf-idf"
    sem = next(m for m in out["model_comparison"] if m["method"] == "semantic")
    assert sem["available"] is False and "not installed" in sem["limitations"]


def test_semantic_path_with_test_encoder(taxonomy, test_encoder):
    result = run_analysis(SAMPLE_RESUME, SAMPLE_JOB, AnalysisOptions(mode="semantic"), encoder=test_encoder)
    assert result["model_info"]["semantic_available"] is True
    assert result["document_similarity"]["semantic"] is not None
    assert {m["method"] for m in result["model_comparison"]} == {"keyword", "tfidf", "semantic"}


def test_coverage_formula():
    reqs = [
        {"canonical": "A", "weight": 2.0, "importance": "must_have", "classification": "direct_match"},
        {"canonical": "B", "weight": 2.0, "importance": "must_have", "classification": "missing"},
        {"canonical": "C", "weight": 1.0, "importance": "nice_to_have", "classification": "strong_semantic"},
    ]
    cov = compute_coverage(reqs)
    assert cov["coverage_score"] == pytest.approx(40.0)          # 2 / 5
    assert cov["must_have_coverage"] == pytest.approx(50.0)
    assert cov["nice_to_have_coverage"] == pytest.approx(0.0)
    assert compute_coverage(reqs, count_strong_semantic=True)["coverage_score"] == pytest.approx(60.0)
    reqs[1]["user_classification"] = "direct_match"              # user confirms B
    assert compute_coverage(reqs)["coverage_score"] == pytest.approx(80.0)
    assert compute_coverage([])["coverage_score"] == 0.0


def test_full_pipeline_on_sample(taxonomy):
    result = run_analysis(SAMPLE_RESUME, SAMPLE_JOB, AnalysisOptions(mode="tfidf", target_role="NLP Engineer"))
    by = {r["canonical"]: r for r in result["requirements"]}
    assert by["Python"]["classification"] == "direct_match"
    assert by["PostgreSQL"]["classification"] == "related"       # MySQL/SQL are related, not equal
    assert by["AWS"]["classification"] == "missing"
    for r in result["requirements"]:
        if r["evidence"]:
            assert r["evidence"]["text"] in SAMPLE_RESUME
    assert 0 <= result["coverage"]["coverage_score"] <= 100
    assert result["roadmap"] and all(t["skill"] != "Python" for t in result["roadmap"])
    assert "not a hiring decision" in result["disclaimer"]


def test_input_validation():
    with pytest.raises(AnalysisInputError):
        run_analysis("", SAMPLE_JOB)
    with pytest.raises(AnalysisInputError):
        run_analysis(SAMPLE_RESUME, "short")
