import numpy as np
import pytest

from app.nlp.recommendations.roadmap import build_roadmap, progress_summary
from app.nlp.tfidf.tfidf_matcher import bow_demo, document_similarity, skill_sentence_scores, top_terms_pair
from app.nlp.visualization.projection import pca_2d, tsne_2d


def test_tfidf_similarity_bounds():
    assert document_similarity("python sql docker", "python sql docker") == pytest.approx(1.0)
    assert document_similarity("python sql", "gardening cooking") == pytest.approx(0.0)
    assert document_similarity("", "python") == 0.0


def test_tfidf_keeps_multiword_and_tech_terms():
    pair = top_terms_pair("machine learning with c++", "deep learning with pytorch")
    terms = {t["term"] for t in pair["doc_a"]}
    assert "machine learning" in terms and "c++" in terms


def test_bow_sparse_characteristics():
    out = bow_demo(["python python sql", "java sql"])
    assert out["shape"] == [2, 3]
    assert 0 < out["sparsity"] < 1
    assert sum(out["matrix"][0]) == 3


def test_skill_sentence_scores_shape():
    m = skill_sentence_scores(["python", "docker"], ["built in python", "used docker", "nothing"])
    assert m.shape == (2, 3) and m[0, 0] > m[0, 2]


def _req(name, importance, cls, weight=2.0, category="X"):
    return {"canonical": name, "category": category, "importance": importance, "weight": weight, "classification": cls}


def test_roadmap_orders_prerequisites_first(taxonomy):
    reqs = [_req("AWS", "must_have", "missing", category="Cloud Computing"),
            _req("Cloud Computing", "nice_to_have", "missing", weight=1.0, category="Cloud Computing"),
            _req("Python", "must_have", "direct_match")]
    tasks = build_roadmap(reqs, {"Python"}, taxonomy, "Engineer")
    order = [t["skill"] for t in tasks]
    assert order.index("Cloud Computing") < order.index("AWS")
    assert "Python" not in order
    aws = next(t for t in tasks if t["skill"] == "AWS")
    assert aws["priority"] == "high"
    assert aws["resources"] and aws["resources"][0]["url"].startswith("https://")
    assert "indicative" in aws["estimated_effort"]


def test_progress_is_self_reported():
    p = progress_summary([{"skill": "A", "status": "completed"}, {"skill": "B", "status": "learning"}])
    assert p["completed_percent"] == 50.0 and p["remaining_gaps"] == ["B"]
    assert "self-reported" in p["note"]


def test_pca_and_tsne():
    rng = np.random.default_rng(0)
    v = rng.standard_normal((12, 20))
    labels = [f"w{i}" for i in range(12)]
    p = pca_2d(v, labels)
    assert len(p["points"]) == 12 and 0 < p["information_retained"] <= 1
    t1 = tsne_2d(v, labels, perplexity=3, seed=1)
    t2 = tsne_2d(v, labels, perplexity=3, seed=1)
    assert t1["points"] == t2["points"]             # fixed seed -> reproducible
    assert any("Only 12 points" in w for w in t1["warnings"])
    with pytest.raises(ValueError):
        pca_2d(v[:2], labels[:2])
