"""Rule-based resume section detection and sentence segmentation with offsets.

Resumes are semi-structured: short heading lines ("EXPERIENCE", "Projects:")
separate blocks of bullet points. We detect headings with a small dictionary of
known section names. Every span keeps character offsets into the ORIGINAL text
so the UI can highlight evidence exactly where it appears.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

SECTION_HEADINGS: dict[str, list[str]] = {
    "summary": ["summary", "professional summary", "profile", "objective", "career objective", "about me", "about"],
    "education": ["education", "academic background", "academics", "qualifications", "academic qualifications"],
    "experience": [
        "experience", "work experience", "professional experience", "employment", "employment history",
        "internship", "internships", "work history", "industrial training",
    ],
    "projects": ["projects", "academic projects", "personal projects", "key projects", "project work"],
    "skills": ["skills", "technical skills", "key skills", "core competencies", "technologies", "tech stack", "tools"],
    "certifications": ["certifications", "certificates", "licenses", "courses", "certifications and courses"],
    "achievements": ["achievements", "awards", "honors", "honours", "accomplishments", "extracurricular activities"],
    "publications": ["publications", "research", "papers"],
}

_HEADING_LOOKUP = {alias: name for name, aliases in SECTION_HEADINGS.items() for alias in aliases}

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{8,}\d)")
URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)


@dataclass
class Section:
    name: str
    start: int
    end: int
    heading: str | None = None
    heading_start: int | None = None  # offset of the heading line itself


@dataclass
class SentenceSpan:
    text: str
    start: int
    end: int
    section: str


def _normalise_heading(line: str) -> str:
    line = line.strip().strip(":-–—|•*#").strip().lower()
    line = re.sub(r"\s+", " ", line)
    return line


def detect_sections(text: str) -> list[Section]:
    """Split text into sections. Text before the first heading is 'contact/header'."""
    headings: list[tuple[int, int, str, str]] = []  # (line_start, line_end, section_name, raw)
    offset = 0
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        norm = _normalise_heading(stripped)
        if stripped and len(norm.split()) <= 5 and norm in _HEADING_LOOKUP:
            headings.append((offset, offset + len(line), _HEADING_LOOKUP[norm], stripped))
        offset += len(line)

    sections: list[Section] = []
    first_start = headings[0][0] if headings else len(text)
    if first_start > 0:
        sections.append(Section(name="header", start=0, end=first_start, heading=None))
    for i, (line_start, line_end, name, raw) in enumerate(headings):
        end = headings[i + 1][0] if i + 1 < len(headings) else len(text)
        sections.append(Section(name=name, start=line_end, end=end, heading=raw, heading_start=line_start))
    if not sections:
        sections.append(Section(name="body", start=0, end=len(text)))
    return sections


def section_at(sections: list[Section], offset: int) -> str:
    for sec in sections:
        if sec.start <= offset < sec.end:
            return sec.name
    return "body"


_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9•\-*])|\n+")
_BULLET_PREFIX = re.compile(r"^[\s•\-*–·▪◦●]+")


def split_sentences(text: str, sections: list[Section] | None = None) -> list[SentenceSpan]:
    """Split on newlines (resume bullets) and sentence punctuation, keeping offsets."""
    sections = sections if sections is not None else detect_sections(text)
    heading_ranges = [(s.heading_start, s.start) for s in sections if s.heading_start is not None]
    spans: list[SentenceSpan] = []
    pos = 0
    for match in list(_SENTENCE_BOUNDARY.finditer(text)) + [None]:
        end = match.start() if match else len(text)
        chunk = text[pos:end]
        lead = len(chunk) - len(chunk.lstrip())
        bullet = _BULLET_PREFIX.match(chunk[lead:])
        if bullet:
            lead += bullet.end()
        stripped = chunk[lead:].rstrip()
        start = pos + lead
        is_heading = any(hs <= start < he for hs, he in heading_ranges)
        if len(stripped) >= 2 and not is_heading:
            spans.append(SentenceSpan(text=stripped, start=start, end=start + len(stripped), section=section_at(sections, start)))
        pos = match.end() if match else len(text)
    return spans


def mask_urls_and_emails(text: str) -> str:
    """Replace URLs/emails with spaces of equal length so offsets stay valid.

    Prevents false skill matches such as 'http' inside a URL or 'github' in a
    profile link being counted as demonstrated experience.
    """

    def blank(m: re.Match[str]) -> str:
        return " " * (m.end() - m.start())

    return EMAIL_RE.sub(blank, URL_RE.sub(blank, text))


def extract_contact_presence(text: str) -> dict[str, bool]:
    """Report which contact fields exist WITHOUT returning their values.

    Contact details are personal data and are not needed for skill analysis.
    """
    return {
        "email": bool(EMAIL_RE.search(text)),
        "phone": bool(PHONE_RE.search(text)),
        "links": bool(URL_RE.search(text)),
    }


def summarise_sections(text: str) -> list[dict]:
    sections = detect_sections(text)
    return [
        {"name": s.name, "heading": s.heading, "start": s.start, "end": s.end, "char_count": s.end - s.start}
        for s in sections
    ]
