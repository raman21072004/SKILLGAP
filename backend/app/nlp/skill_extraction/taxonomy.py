"""Skill taxonomy: canonical names, aliases, categories, related skills, prerequisites.

The taxonomy is plain JSON (data/skill_taxonomy/taxonomy.json) so that it can be
edited without touching code. Related skills are stored but are NEVER treated as
equivalent: knowing Java is evidence of a *transferable* skill for a Python
requirement, not evidence of Python.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from app.nlp.config import data_dir


@dataclass(frozen=True)
class Skill:
    canonical: str
    category: str
    aliases: tuple[str, ...]
    case_sensitive_aliases: tuple[str, ...]
    related: tuple[str, ...]
    prerequisites: tuple[str, ...]
    level: str
    description: str

    @property
    def query_text(self) -> str:
        """Short natural-language phrase used as the semantic search query."""
        return f"{self.canonical}: {self.description}"


@dataclass
class AliasPattern:
    canonical: str
    alias: str
    regex: re.Pattern[str]
    length: int


@dataclass
class Taxonomy:
    skills: dict[str, Skill]
    categories: list[str]
    patterns: list[AliasPattern] = field(default_factory=list)

    def get(self, name: str) -> Skill | None:
        """Look up by canonical name or alias (case-insensitive)."""
        if name in self.skills:
            return self.skills[name]
        lowered = name.strip().lower()
        for skill in self.skills.values():
            if lowered == skill.canonical.lower() or lowered in skill.aliases or name.strip() in skill.case_sensitive_aliases:
                return skill
        return None

    def normalize(self, name: str) -> str | None:
        """Map an alias such as 'JS' or 'Postgres' to its canonical name."""
        skill = self.get(name)
        return skill.canonical if skill else None

    def related_to(self, canonical: str) -> set[str]:
        """Related skills in both directions (A lists B, or B lists A)."""
        out: set[str] = set()
        skill = self.skills.get(canonical)
        if skill:
            out.update(skill.related)
        for other in self.skills.values():
            if canonical in other.related:
                out.add(other.canonical)
        out.discard(canonical)
        return out


def _boundary_regex(alias: str, case_sensitive: bool) -> re.Pattern[str]:
    """Match an alias as a whole term.

    The left boundary forbids letters/digits; the right boundary also forbids
    '+', '#' and '&' so that 'C' does not match inside 'C++', 'C#' or 'R&D'.
    """
    escaped = re.escape(alias)
    escaped = escaped.replace(r"\ ", r"[\s\-]+")  # 'machine learning' == 'machine-learning'
    pattern = rf"(?<![A-Za-z0-9+#.]){escaped}(?![A-Za-z0-9+#&])"
    return re.compile(pattern, 0 if case_sensitive else re.IGNORECASE)


def build_taxonomy(raw: dict) -> Taxonomy:
    skills: dict[str, Skill] = {}
    patterns: list[AliasPattern] = []
    for entry in raw["skills"]:
        skill = Skill(
            canonical=entry["canonical"],
            category=entry["category"],
            aliases=tuple(a.lower() for a in entry.get("aliases", [])),
            case_sensitive_aliases=tuple(entry.get("case_sensitive_aliases", [])),
            related=tuple(entry.get("related", [])),
            prerequisites=tuple(entry.get("prerequisites", [])),
            level=entry.get("level", "intermediate"),
            description=entry.get("description", ""),
        )
        skills[skill.canonical] = skill
        insensitive = set(skill.aliases)
        if not skill.case_sensitive_aliases or skill.canonical.lower() in insensitive:
            insensitive.add(skill.canonical.lower())
        for alias in insensitive:
            if alias in {a.lower() for a in skill.case_sensitive_aliases}:
                continue
            patterns.append(AliasPattern(skill.canonical, alias, _boundary_regex(alias, False), len(alias)))
        for alias in skill.case_sensitive_aliases:
            patterns.append(AliasPattern(skill.canonical, alias, _boundary_regex(alias, True), len(alias)))
    # Longest aliases first so "machine learning" wins over "learning"-like overlaps
    patterns.sort(key=lambda p: p.length, reverse=True)
    return Taxonomy(skills=skills, categories=list(raw.get("categories", [])), patterns=patterns)


def load_taxonomy_file(path: Path) -> Taxonomy:
    with path.open(encoding="utf-8") as fh:
        return build_taxonomy(json.load(fh))


@lru_cache(maxsize=1)
def get_taxonomy() -> Taxonomy:
    return load_taxonomy_file(data_dir() / "skill_taxonomy" / "taxonomy.json")
