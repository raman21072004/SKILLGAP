"""Skill-gap analysis: classify every job requirement against the resume.

Classification rules (applied in order, all deterministic):

1. DIRECT MATCH        the skill or one of its aliases appears in the resume.
2. STRONG SEMANTIC     not named, but the most similar resume sentence has
                       similarity >= strong threshold AND that sentence does not
                       name a *different* skill of the same category
                       (prevents "Built APIs in Java" from validating Python).
3. RELATED             a taxonomy-related skill is present (e.g. Java for Python),
                       or similarity >= related threshold.
4. MISSING/UNVERIFIED  otherwise.

Only DIRECT matches (plus user-confirmed corrections) count towards coverage.

Three comparison methods are also run on the same input:
    keyword  - taxonomy alias matching only
    tfidf    - lexical TF-IDF cosine between skill phrase and resume sentences
    semantic - dense sentence-transformer cosine (if the model is available)
"""

from __future__ import annotations

import time
from dataclasses import asdict

import numpy as np

from app.nlp.config import NLPConfig, get_nlp_config
from app.nlp.embeddings.sentence_encoder import Encoder, SentenceEncoder, get_encoder
from app.nlp.explanations.explainer import explain
from app.nlp.extraction.sections import SentenceSpan
from app.nlp.skill_extraction.extractor import ExtractedSkill, RequiredSkill, SkillMention
from app.nlp.skill_extraction.taxonomy import Taxonomy
from app.nlp.tfidf.tfidf_matcher import skill_sentence_scores

MODES = {"keyword", "tfidf", "semantic"}


def _semantic_scores(encoder: Encoder, queries: list[str], sentences: list[str]) -> np.ndarray:
    q = encoder.encode(queries)
    s = encoder.encode(sentences)
    qn = q / np.clip(np.linalg.norm(q, axis=1, keepdims=True), 1e-12, None)
    sn = s / np.clip(np.linalg.norm(s, axis=1, keepdims=True), 1e-12, None)
    return qn @ sn.T


def _encoder_ready(encoder: Encoder) -> bool:
    if isinstance(encoder, SentenceEncoder):
        return encoder.load()
    return bool(encoder.available)


def _lexical_phrase(taxonomy: Taxonomy, canonical: str) -> str:
    skill = taxonomy.skills[canonical]
    return " ".join([skill.canonical] + list(skill.aliases[:4]))


def _evidence_from_mention(m: SkillMention, strength: str, kind: str) -> dict:
    return {
        "text": m.sentence,
        "matched_text": m.matched_text,
        "section": m.section,
        "start": m.sentence_start,
        "end": m.sentence_end,
        "match_start": m.char_start,
        "match_end": m.char_end,
        "strength": strength,
        "kind": kind,
    }


def _evidence_from_sentence(s: SentenceSpan, kind: str) -> dict:
    return {"text": s.text, "matched_text": None, "section": s.section, "start": s.start, "end": s.end,
            "match_start": None, "match_end": None, "strength": None, "kind": kind}


def analyze_gaps(
    resume_sentences: list[SentenceSpan],
    candidate_skills: dict[str, ExtractedSkill],
    requirements: list[RequiredSkill],
    taxonomy: Taxonomy,
    mode: str = "semantic",
    encoder: Encoder | None = None,
    config: NLPConfig | None = None,
) -> dict:
    """Classify each requirement and run the three comparison methods."""
    if mode not in MODES:
        raise ValueError(f"mode must be one of {sorted(MODES)}")
    config = config or get_nlp_config()
    th = config.thresholds
    encoder = encoder or get_encoder()

    sentences = [s for s in resume_sentences if s.section != "header"]
    sent_texts = [s.text for s in sentences]
    canon_list = [r.canonical for r in requirements]

    # Mentions grouped by sentence start -> used for the conflict rule
    skills_in_sentence: dict[int, set[str]] = {}
    for sk in candidate_skills.values():
        for m in sk.mentions:
            skills_in_sentence.setdefault(m.sentence_start, set()).add(m.canonical)

    # ---- Method timings & score matrices ------------------------------------
    timings: dict[str, float] = {}

    t0 = time.perf_counter()
    keyword_hits = {c: c in candidate_skills for c in canon_list}
    timings["keyword"] = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    tfidf_m = skill_sentence_scores([_lexical_phrase(taxonomy, c) for c in canon_list], sent_texts)
    timings["tfidf"] = (time.perf_counter() - t0) * 1000

    semantic_ok = _encoder_ready(encoder) and bool(sent_texts) and bool(canon_list)
    semantic_error = None if semantic_ok else getattr(encoder, "error", None)
    sem_m = None
    if semantic_ok:
        t0 = time.perf_counter()
        try:
            sem_m = _semantic_scores(encoder, [taxonomy.skills[c].query_text for c in canon_list], sent_texts)
        except Exception as exc:  # pragma: no cover - runtime model failure
            semantic_ok, semantic_error = False, f"Semantic encoding failed: {type(exc).__name__}"
        timings["semantic"] = (time.perf_counter() - t0) * 1000

    # Which similarity backend drives the primary classification?
    fallback_used = False
    if mode == "semantic" and semantic_ok:
        primary_m, backend, strong_t, related_t = sem_m, f"sentence-transformer ({encoder.name})", th.semantic_strong, th.semantic_related
    elif mode in {"semantic", "tfidf"}:
        fallback_used = mode == "semantic"
        primary_m, backend, strong_t, related_t = tfidf_m, "tf-idf", th.tfidf_strong, th.tfidf_related
    else:
        primary_m, backend, strong_t, related_t = None, None, None, None

    results: list[dict] = []
    for i, req in enumerate(requirements):
        c = req.canonical
        related_present = sorted(r for r in taxonomy.related_to(c) if r in candidate_skills)
        tfidf_best = float(tfidf_m[i].max()) if sent_texts else 0.0
        sem_best = float(sem_m[i].max()) if sem_m is not None and sent_texts else None

        res = {
            "required_skill": c,
            "canonical": c,
            "category": req.category,
            "importance": req.importance,
            "weight": req.weight,
            "requirement_text": req.source_text,
            "requirement_source": req.source,
            "exact_match": c in candidate_skills,
            "tfidf_similarity": round(tfidf_best, 4),
            "semantic_similarity": round(sem_best, 4) if sem_best is not None else None,
            "similarity": None,
            "similarity_backend": backend,
            "related_skills_found": related_present,
            "evidence": None,
            "method": None,
            "user_classification": None,
        }

        if c in candidate_skills:
            sk = candidate_skills[c]
            res.update(classification="direct_match", method="taxonomy alias match",
                       evidence=_evidence_from_mention(sk.best_mention, sk.strength, "exact"), similarity=1.0)
        else:
            classification = "missing"
            evidence = None
            sim = None
            if primary_m is not None and sent_texts:
                j = int(np.argmax(primary_m[i]))
                sim = float(primary_m[i, j])
                best_sent = sentences[j]
                same_cat_conflict = any(
                    other != c and taxonomy.skills[other].category == req.category
                    for other in skills_in_sentence.get(best_sent.start, set())
                )
                if sim >= strong_t and not same_cat_conflict:
                    classification, evidence = "strong_semantic", _evidence_from_sentence(best_sent, "semantic")
                    res["method"] = f"{backend} similarity >= {strong_t}"
                elif sim >= related_t:
                    classification, evidence = "related", _evidence_from_sentence(best_sent, "semantic")
                    res["method"] = f"{backend} similarity >= {related_t}" + (" (capped: sentence names a different skill of the same category)" if same_cat_conflict and sim >= strong_t else "")
                res["similarity"] = round(sim, 4)
            if classification == "missing" and related_present:
                rel = candidate_skills[related_present[0]]
                classification = "related"
                evidence = _evidence_from_mention(rel.best_mention, rel.strength, "related")
                res["method"] = "taxonomy related-skill link"
            elif classification != "missing" and related_present and res["method"]:
                res["method"] += "; related skills present"
            if classification == "missing":
                res["method"] = "no alias match" + (f"; best {backend} similarity below {related_t}" if backend else "")
            res.update(classification=classification, evidence=evidence)

        explanation, next_action, uncertainty = explain(res)
        res.update(explanation=explanation, next_action=next_action, uncertainty=uncertainty)
        results.append(res)

    comparison = _model_comparison(canon_list, keyword_hits, tfidf_m, sem_m, sent_texts, config, timings, semantic_ok, semantic_error, encoder)

    return {
        "requirements": results,
        "mode": mode,
        "similarity_backend": backend,
        "semantic_available": semantic_ok,
        "semantic_error": semantic_error,
        "fallback_used": fallback_used,
        "fallback_reason": semantic_error if fallback_used else None,
        "thresholds": asdict(th),
        "model_comparison": comparison,
    }


def _model_comparison(canon_list, keyword_hits, tfidf_m, sem_m, sent_texts, config, timings, semantic_ok, semantic_error, encoder) -> list[dict]:
    th = config.thresholds

    def split(matrix, strong, related):
        matched, rel, missing, scores = [], [], [], {}
        for i, c in enumerate(canon_list):
            s = float(matrix[i].max()) if sent_texts else 0.0
            scores[c] = round(s, 4)
            (matched if s >= strong else rel if s >= related else missing).append(c)
        return matched, rel, missing, scores

    out = [{
        "method": "keyword",
        "label": "Keyword / taxonomy matching",
        "available": True,
        "matched": [c for c in canon_list if keyword_hits[c]],
        "related": [],
        "missing": [c for c in canon_list if not keyword_hits[c]],
        "scores": {c: 1.0 if keyword_hits[c] else 0.0 for c in canon_list},
        "time_ms": round(timings.get("keyword", 0.0), 2),
        "limitations": "Exact alias matching only: high precision, but misses paraphrases and unlisted synonyms.",
    }]
    m, r, miss, sc = split(tfidf_m, th.tfidf_strong, th.tfidf_related)
    out.append({
        "method": "tfidf", "label": "TF-IDF + cosine similarity", "available": True,
        "matched": m, "related": r, "missing": miss, "scores": sc,
        "time_ms": round(timings.get("tfidf", 0.0), 2),
        "limitations": "Lexical overlap only: no notion of meaning, sensitive to wording; thresholds "
                       f"{th.tfidf_strong}/{th.tfidf_related} are uncalibrated.",
    })
    if semantic_ok and sem_m is not None:
        m, r, miss, sc = split(sem_m, th.semantic_strong, th.semantic_related)
        out.append({
            "method": "semantic", "label": f"Dense embeddings ({encoder.name})", "available": True,
            "matched": m, "related": r, "missing": miss, "scores": sc,
            "time_ms": round(timings.get("semantic", 0.0), 2),
            "limitations": "Captures paraphrases but similarity is not proof of skill; may score related "
                           "technologies (e.g. Java vs Python) highly. Thresholds are uncalibrated.",
        })
    else:
        out.append({
            "method": "semantic", "label": "Dense embeddings", "available": False,
            "matched": [], "related": [], "missing": [], "scores": {}, "time_ms": None,
            "limitations": semantic_error or "Semantic model unavailable.",
        })
    return out
