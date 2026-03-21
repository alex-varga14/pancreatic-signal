from __future__ import annotations

import re
from dataclasses import dataclass

_SECTION_HEADER_RE = re.compile(
    r"\b(clinical history|history|technique|findings|impression|conclusion)\s*:",
    flags=re.IGNORECASE,
)
_SECTION_NAME_MAP = {
    "clinical history": "history",
    "history": "history",
    "technique": "technique",
    "findings": "findings",
    "impression": "impression",
    "conclusion": "impression",
}
_SENTENCE_BREAK_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class TextSpan:
    text: str
    start: int
    end: int


@dataclass(frozen=True)
class SectionSpan(TextSpan):
    name: str


def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_sections(text: str) -> list[SectionSpan]:
    matches = list(_SECTION_HEADER_RE.finditer(text))
    if not matches:
        return [SectionSpan(name="unknown", text=text, start=0, end=len(text))] if text else []

    sections: list[SectionSpan] = []

    first_start = matches[0].start()
    leading_raw = text[:first_start]
    leading_text = leading_raw.strip()
    if leading_text:
        leading_trim = len(leading_raw) - len(leading_raw.lstrip())
        leading_start = leading_trim
        sections.append(
            SectionSpan(
                name="unknown",
                text=leading_text,
                start=leading_start,
                end=leading_start + len(leading_text),
            )
        )

    for index, match in enumerate(matches):
        content_start = match.end()
        content_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        raw_content = text[content_start:content_end]
        stripped = raw_content.strip()
        if not stripped:
            continue

        leading_trim = len(raw_content) - len(raw_content.lstrip())
        section_start = content_start + leading_trim
        section_end = section_start + len(stripped)
        section_name = _SECTION_NAME_MAP[match.group(1).lower()]
        sections.append(
            SectionSpan(
                name=section_name,
                text=stripped,
                start=section_start,
                end=section_end,
            )
        )

    return sections


def sentence_spans(text: str) -> list[TextSpan]:
    if not text:
        return []

    spans: list[TextSpan] = []
    cursor = 0

    for match in _SENTENCE_BREAK_RE.finditer(text):
        chunk = text[cursor:match.start()]
        stripped = chunk.strip()
        if stripped:
            leading_trim = len(chunk) - len(chunk.lstrip())
            start = cursor + leading_trim
            spans.append(TextSpan(text=stripped, start=start, end=start + len(stripped)))
        cursor = match.end()

    tail = text[cursor:]
    stripped_tail = tail.strip()
    if stripped_tail:
        leading_trim = len(tail) - len(tail.lstrip())
        start = cursor + leading_trim
        spans.append(TextSpan(text=stripped_tail, start=start, end=start + len(stripped_tail)))

    return spans


def sentence_split(text: str) -> list[str]:
    return [span.text for span in sentence_spans(text)]
