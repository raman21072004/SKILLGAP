"""Deterministic, template-based explanations.

No language model is used: every sentence is built from the actual matching
result, so the explanation can never invent evidence.
"""

from __future__ import annotations

CLASS_LABELS = {
    "direct_match": "Direct match",
    "strong_semantic": "Strong semantic match - needs verification",
    "related": "Related / transferable skill",
    "missing": "Missing or unverified",
}

SECTION_LABELS = {
    "experience": "Experience", "projects": "Projects", "skills": "Skills", "education": "Education",
    "summary": "Summary", "certifications": "Certifications", "achievements": "Achievements",
    "publications": "Publications", "body": "Resume", "header": "Header",
}


def _section(name: str | None) -> str:
    return SECTION_LABELS.get(name or "body", (name or "resume").title())


def explain(req: dict) -> tuple[str, str, str | None]:
    """Return (explanation, next_action, uncertainty) for one requirement result."""
    skill = req["canonical"]
    cls = req["classification"]
    ev = req.get("evidence")
    backend = req.get("similarity_backend")
    sim = req.get("similarity")
    sim_txt = f"{sim:.2f}" if isinstance(sim, (int, float)) else "n/a"

    if cls == "direct_match":
        strength = ev.get("strength") if ev else None
        where = _section(ev.get("section")) if ev else "resume"
        if strength == "demonstrated":
            return (
                f"'{ev['matched_text']}' appears in your {where} section in a sentence describing work you did, "
                f"which directly matches the requirement '{skill}'.",
                "Keep this evidence. Quantify the impact (numbers, scale) to strengthen it.",
                None,
            )
        if strength == "listed":
            return (
                f"'{ev['matched_text']}' is listed in your {where} section, which matches '{skill}' by name. "
                "It is only listed - no project or experience sentence shows how you used it.",
                f"Add a project or experience bullet that shows what you built with {skill}.",
                "Listed without supporting experience; proficiency cannot be verified from the resume.",
            )
        return (
            f"'{ev['matched_text']}' is mentioned in your {where} section, matching '{skill}' by name.",
            f"Make the evidence stronger by describing a concrete task where you used {skill}.",
            "Mentioned, but not clearly tied to hands-on work.",
        )

    if cls == "strong_semantic":
        return (
            f"'{skill}' is not named in your resume, but a sentence in your {_section(ev.get('section') if ev else None)} "
            f"section is semantically similar (cosine {sim_txt}, {backend}). Similarity suggests relevant work, "
            "but it is not proof of the skill.",
            f"If you have genuinely used {skill}, name it explicitly in that bullet. Otherwise treat it as a gap.",
            "Inferred from semantic similarity only - requires your verification.",
        )

    if cls == "related":
        related = req.get("related_skills_found") or []
        if related:
            rel_txt = ", ".join(related)
            return (
                f"'{skill}' was not found, but you show related skills ({rel_txt}). Related skills are transferable "
                f"and can make {skill} faster to learn, but they do not demonstrate {skill} itself.",
                f"Use your {related[0]} background to learn {skill}, then build a small project that uses it.",
                "Transferable skill only; not counted as coverage.",
            )
        return (
            f"'{skill}' was not found. The closest resume sentence has moderate similarity (cosine {sim_txt}, {backend}), "
            "which suggests partially related work.",
            f"Review whether your experience really involves {skill}; if so, name it explicitly.",
            "Weak semantic signal; not counted as coverage.",
        )

    return (
        f"No mention of '{skill}' or its aliases was found, and no resume sentence was sufficiently similar "
        f"(best cosine {sim_txt}{', ' + backend if backend else ''}).",
        f"Add {skill} to your learning roadmap and add resume evidence after you have practised it.",
        "Absence from the resume does not prove you lack the skill - it means the resume does not show it.",
    )
