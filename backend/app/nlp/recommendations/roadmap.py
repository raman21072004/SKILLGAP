"""Personalised learning roadmap from identified gaps.

* Priority: must-have gaps first; truly missing skills before related/verify ones.
* Order: prerequisites first (topological sort), then priority.
* Resources come from a curated catalog (data/learning_resources/catalog.json);
  we never generate arbitrary URLs. Missing catalog entries are reported honestly.
* Effort estimates are indicative only and do not guarantee proficiency.
"""

from __future__ import annotations

import heapq
import json
from functools import lru_cache

from app.nlp.config import data_dir
from app.nlp.skill_extraction.taxonomy import Taxonomy
from app.nlp.skill_gap.scoring import effective_classification

PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


@lru_cache(maxsize=1)
def load_catalog() -> dict:
    with (data_dir() / "learning_resources" / "catalog.json").open(encoding="utf-8") as fh:
        return json.load(fh)


def _priority(importance: str, classification: str) -> str:
    if importance == "must_have":
        return "high" if classification == "missing" else "medium"
    return "medium" if classification == "missing" else "low"


def build_roadmap(requirements: list[dict], candidate_skills: set[str], taxonomy: Taxonomy, target_role: str | None = None) -> list[dict]:
    catalog = load_catalog()
    role = target_role or "the target role"
    gaps = [r for r in requirements if effective_classification(r) != "direct_match"]
    gap_names = {r["canonical"] for r in gaps}
    by_name = {r["canonical"]: r for r in gaps}

    tasks: dict[str, dict] = {}
    for r in gaps:
        cls = effective_classification(r)
        skill = taxonomy.skills.get(r["canonical"])
        level = skill.level if skill else "intermediate"
        category = r["category"]
        prereqs = []
        for p in (skill.prerequisites if skill else ()):
            status = "demonstrated" if p in candidate_skills else ("in roadmap" if p in gap_names else "learn first")
            prereqs.append({"skill": p, "status": status})
        resources = catalog["resources"].get(r["canonical"], [])
        project = catalog["projects"].get(r["canonical"]) or catalog["category_projects"].get(
            category, f"Build a small project that uses {r['canonical']} and document what you learned."
        )
        importance_txt = "a must-have" if r["importance"] == "must_have" else "a nice-to-have"
        if cls == "missing":
            reason = f"{r['canonical']} is {importance_txt} requirement for {role} and the resume shows no evidence of it."
        elif cls == "related":
            reason = f"{r['canonical']} is {importance_txt} requirement for {role}; you have related skills but no direct evidence."
        else:
            reason = f"{r['canonical']} is {importance_txt} requirement for {role}; your resume suggests related work that should be verified and stated explicitly."
        checklist = [
            f"Study the core concepts of {r['canonical']} using the suggested resources",
            f"Complete the practice project: {project}",
            "Publish the project (e.g. on GitHub) with a clear README",
            f"Add a resume bullet describing what you built with {r['canonical']} and its outcome",
            "Re-run the analysis to check that the new evidence is detected",
        ]
        if cls == "strong_semantic":
            checklist.insert(0, f"Confirm whether your existing work actually used {r['canonical']}")
        tasks[r["canonical"]] = {
            "skill": r["canonical"],
            "category": category,
            "importance": r["importance"],
            "gap_type": cls,
            "priority": _priority(r["importance"], cls),
            "reason": reason,
            "level": level,
            "prerequisites": prereqs,
            "project": project,
            "estimated_effort": catalog["effort_by_level"].get(level, "varies"),
            "checklist": checklist,
            "resources": resources,
            "resources_note": None if resources else "No curated resource in the catalog yet; consult the official documentation.",
            "status": "not_started",
        }

    # Topological order: a task waits for prerequisite tasks that are also in the roadmap
    deps = {name: {p["skill"] for p in t["prerequisites"] if p["skill"] in tasks} for name, t in tasks.items()}
    indegree = {n: len(d) for n, d in deps.items()}
    dependents: dict[str, list[str]] = {n: [] for n in tasks}
    for n, d in deps.items():
        for p in d:
            dependents[p].append(n)
    heap = [(PRIORITY_RANK[tasks[n]["priority"]], -by_name[n]["weight"], n) for n, k in indegree.items() if k == 0]
    heapq.heapify(heap)
    ordered: list[str] = []
    while heap:
        _, _, n = heapq.heappop(heap)
        ordered.append(n)
        for child in dependents[n]:
            indegree[child] -= 1
            if indegree[child] == 0:
                heapq.heappush(heap, (PRIORITY_RANK[tasks[child]["priority"]], -by_name[child]["weight"], child))
    ordered += [n for n in tasks if n not in ordered]  # safety net for cycles

    out = []
    for i, n in enumerate(ordered, start=1):
        t = tasks[n]
        t["order"] = i
        out.append(t)
    return out


def progress_summary(tasks: list[dict]) -> dict:
    """Self-reported learning progress. Kept separate from verified resume evidence."""
    total = len(tasks)
    by_status = {s: 0 for s in ("not_started", "learning", "practiced", "completed")}
    for t in tasks:
        by_status[t["status"]] = by_status.get(t["status"], 0) + 1
    remaining = [t["skill"] for t in tasks if t["status"] != "completed"]
    return {
        "total": total,
        "by_status": by_status,
        "completed_percent": round(100 * by_status["completed"] / total, 1) if total else 0.0,
        "remaining_gaps": remaining,
        "note": "Progress is self-reported and does not change the verified coverage score. Update your resume and re-run the analysis to verify new skills.",
    }
