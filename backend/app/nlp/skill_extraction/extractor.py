"""Hybrid skill extraction.

1. Phrase matching against the taxonomy (aliases, abbreviations, multi-word terms)
2. Normalised-text matching (hyphen/space variants, case rules for short names)
3. Statistical features (TF-IDF terms the taxonomy does not know -> surfaced for review)
4. Semantic matching is applied later, in the matching stage (skill_gap.analyzer)

Every mention keeps the exact source text and character offsets so the evidence
shown to the user is always a real passage from the document.

A mention is not proof of mastery. We record *how* a skill appears:
    demonstrated - used in an experience/project bullet or with an action verb
    listed       - only appears in a skills list
    mentioned    - appears elsewhere (summary, coursework, ...)
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from app.nlp.extraction.sections import SentenceSpan, detect_sections, mask_urls_and_emails, split_sentences
from app.nlp.skill_extraction.taxonomy import Taxonomy

ACTION_VERBS = {
    "built", "build", "developed", "develop", "implemented", "implement", "designed", "design", "created",
    "trained", "deployed", "engineered", "architected", "optimized", "optimised", "automated", "led", "wrote",
    "integrated", "migrated", "maintained", "launched", "delivered", "fine-tuned", "analyzed", "analysed",
    "programmed", "coded", "constructed", "improved", "reduced", "increased", "used", "using",
}

# Sections where an action verb ("built", "trained") counts as hands-on evidence.
# Summary/education/skills are excluded: "interested in machine learning" is not experience.
VERB_EVIDENCE_SECTIONS = {"body", "achievements", "publications"}

EXCLUDED_SECTIONS = {"header"}  # contact block: names/initials cause false positives ("R.")

NICE_TO_HAVE_CUES = re.compile(
    r"\b(nice[\s-]to[\s-]have|good[\s-]to[\s-]have|preferred|preferably|bonus|a plus|is a plus|desirable|optional|familiarity with)\b",
    re.IGNORECASE,
)
MUST_HAVE_CUES = re.compile(r"\b(must|required|requirement|mandatory|essential|need to|strong)\b", re.IGNORECASE)


@dataclass
class SkillMention:
    canonical: str
    category: str
    matched_text: str
    char_start: int
    char_end: int
    sentence: str
    sentence_start: int
    sentence_end: int
    section: str
    mention_type: str  # demonstrated | listed | mentioned


@dataclass
class ExtractedSkill:
    canonical: str
    category: str
    mentions: list[SkillMention] = field(default_factory=list)

    @property
    def strength(self) -> str:
        kinds = {m.mention_type for m in self.mentions}
        for k in ("demonstrated", "mentioned", "listed"):
            if k in kinds:
                return k
        return "mentioned"

    @property
    def best_mention(self) -> SkillMention:
        order = {"demonstrated": 0, "mentioned": 1, "listed": 2}
        return sorted(self.mentions, key=lambda m: (order.get(m.mention_type, 3), m.char_start))[0]

    def to_dict(self) -> dict:
        return {
            "canonical": self.canonical,
            "category": self.category,
            "strength": self.strength,
            "mention_count": len(self.mentions),
            "best_evidence": asdict(self.best_mention),
            "mentions": [asdict(m) for m in self.mentions],
        }


@dataclass
class RequiredSkill:
    canonical: str
    category: str
    importance: str  # must_have | nice_to_have
    weight: float
    source_text: str
    source: str = "extracted"  # extracted | user_added


def _mention_type(sentence: SentenceSpan) -> str:
    if sentence.section in {"experience", "projects"}:
        return "demonstrated"
    words = {w.lower() for w in re.findall(r"[A-Za-z\-]+", sentence.text)}
    if words & ACTION_VERBS and sentence.section in VERB_EVIDENCE_SECTIONS:
        return "demonstrated"
    if sentence.section == "skills":
        return "listed"
    return "mentioned"


HEADING_WORDS = re.compile(
    r"\b(requirements?|qualifications?|responsibilities|skills|nice[\s-]to[\s-]have|good[\s-]to[\s-]have|preferred|bonus|about|what you|you will|we offer|benefits)\b",
    re.IGNORECASE,
)


def _is_heading_line(line: str) -> bool:
    if line[:1] in "-•*–·▪●":
        return False
    words = line.split()
    return len(words) <= 6 and (line.endswith(":") or bool(HEADING_WORDS.search(line)))


def find_mentions(text: str, taxonomy: Taxonomy, skip_sections: set[str] | None = None) -> list[SkillMention]:
    """Find every taxonomy alias occurrence with sentence + section context."""
    skip_sections = EXCLUDED_SECTIONS if skip_sections is None else skip_sections
    sections = detect_sections(text)
    sentences = split_sentences(text, sections)
    masked = mask_urls_and_emails(text)
    mentions: list[SkillMention] = []

    for sent in sentences:
        if sent.section in skip_sections:
            continue
        segment = masked[sent.start : sent.end]
        occupied: list[tuple[int, int]] = []
        for pat in taxonomy.patterns:  # longest first
            for m in pat.regex.finditer(segment):
                s, e = m.start(), m.end()
                if any(s < oe and e > os_ for os_, oe in occupied):
                    continue  # overlaps a longer alias already matched (e.g. 'react native' vs 'react')
                occupied.append((s, e))
                skill = taxonomy.skills[pat.canonical]
                mentions.append(
                    SkillMention(
                        canonical=skill.canonical,
                        category=skill.category,
                        matched_text=text[sent.start + s : sent.start + e],
                        char_start=sent.start + s,
                        char_end=sent.start + e,
                        sentence=sent.text,
                        sentence_start=sent.start,
                        sentence_end=sent.end,
                        section=sent.section,
                        mention_type=_mention_type(sent),
                    )
                )
    mentions.sort(key=lambda m: m.char_start)
    return mentions


def extract_candidate_skills(resume_text: str, taxonomy: Taxonomy) -> dict[str, ExtractedSkill]:
    """Group resume mentions by canonical skill."""
    grouped: dict[str, ExtractedSkill] = {}
    for m in find_mentions(resume_text, taxonomy):
        grouped.setdefault(m.canonical, ExtractedSkill(m.canonical, m.category)).mentions.append(m)
    return grouped


def extract_required_skills(
    job_text: str,
    taxonomy: Taxonomy,
    must_have_weight: float = 2.0,
    nice_to_have_weight: float = 1.0,
    must_have_overrides: list[str] | None = None,
    nice_to_have_overrides: list[str] | None = None,
    custom_weights: dict[str, float] | None = None,
    equal_weights: bool = False,
) -> tuple[list[RequiredSkill], list[str]]:
    """Extract job requirements and decide must-have vs nice-to-have.

    Importance rules (deterministic and explainable):
      * a sentence or a section heading containing cues such as "nice to have",
        "preferred", "bonus", "a plus" -> nice_to_have
      * otherwise -> must_have (job ads usually list core requirements first)
      * if a skill appears as both, must_have wins
      * user overrides always win
    Returns (requirements, warnings).
    """
    warnings: list[str] = []
    # In job descriptions, text before the first heading is meaningful (not contact info)
    mentions = find_mentions(job_text, taxonomy, skip_sections=set())

    def in_nice_block(offset: int) -> bool:
        """True if the nearest heading line above `offset` is a nice-to-have heading."""
        preceding = job_text[:offset].split("\n")
        for line in reversed(preceding[:-1]):  # last item is the current line's prefix
            s = line.strip()
            if s and _is_heading_line(s):
                return bool(NICE_TO_HAVE_CUES.search(s))
        return False

    reqs: dict[str, RequiredSkill] = {}
    for m in mentions:
        nice = bool(NICE_TO_HAVE_CUES.search(m.sentence)) or in_nice_block(m.sentence_start)
        importance = "nice_to_have" if nice else "must_have"
        existing = reqs.get(m.canonical)
        if existing is None or (existing.importance == "nice_to_have" and importance == "must_have"):
            reqs[m.canonical] = RequiredSkill(
                canonical=m.canonical,
                category=m.category,
                importance=importance,
                weight=0.0,
                source_text=m.sentence,
            )

    def resolve(names: list[str] | None) -> list[str]:
        resolved = []
        for name in names or []:
            canon = taxonomy.normalize(name)
            if canon is None:
                warnings.append(f"'{name}' is not in the skill taxonomy and was ignored.")
            else:
                resolved.append(canon)
        return resolved

    for canon in resolve(must_have_overrides):
        skill = taxonomy.skills[canon]
        if canon in reqs:
            reqs[canon].importance = "must_have"
        else:
            reqs[canon] = RequiredSkill(canon, skill.category, "must_have", 0.0, "Added by user", source="user_added")
    for canon in resolve(nice_to_have_overrides):
        skill = taxonomy.skills[canon]
        if canon in reqs:
            reqs[canon].importance = "nice_to_have"
        else:
            reqs[canon] = RequiredSkill(canon, skill.category, "nice_to_have", 0.0, "Added by user", source="user_added")

    custom = {taxonomy.normalize(k) or k: float(v) for k, v in (custom_weights or {}).items()}
    for req in reqs.values():
        if equal_weights:
            req.weight = 1.0
        else:
            req.weight = must_have_weight if req.importance == "must_have" else nice_to_have_weight
        if req.canonical in custom:
            req.weight = max(0.0, custom[req.canonical])

    ordered = sorted(reqs.values(), key=lambda r: (r.importance != "must_have", r.category, r.canonical))
    return ordered, warnings


JD_BOILERPLATE = {
    "experience", "role", "requirements", "requirement", "nice", "knowledge", "good", "skills", "skill", "ability",
    "work", "working", "team", "strong", "looking", "junior", "senior", "engineer", "engineers", "about", "years",
    "year", "plus", "familiarity", "hands", "hands-on", "job", "candidate", "candidates", "company", "responsibilities",
    "qualifications", "preferred", "required", "must", "build", "building", "using", "use", "including", "like",
    "practices", "techniques", "platforms", "features", "product", "excellent", "understanding", "degree",
    "bachelor", "related", "field", "etc", "new", "great", "opportunity", "join", "help", "able", "well",
}


def unrecognized_terms(job_text: str, taxonomy: Taxonomy, top_k: int = 10) -> list[dict]:
    """Statistical feature extraction: high-TF-IDF JD terms that the taxonomy does not cover.

    These are shown to the user as "possible requirements to review" - never
    silently added as skills.
    """
    from app.nlp.tfidf.tfidf_matcher import top_terms_single_document

    known_tokens: set[str] = set()
    for skill in taxonomy.skills.values():
        for name in (skill.canonical.lower(), *skill.aliases):
            known_tokens.update(name.split())
    terms = top_terms_single_document(job_text, top_k=top_k * 6)
    out = []
    for term, score in terms:
        parts = term.split()
        if any(p in known_tokens or p in JD_BOILERPLATE or len(p) < 3 or p.isdigit() for p in parts):
            continue
        out.append({"term": term, "score": round(score, 4)})
        if len(out) >= top_k:
            break
    return out
