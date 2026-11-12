"""Research-neutral scene extraction for ANY original FR/EN narration.

This compiler extracts short visible labels *only from authored script text*.
It never guesses numeric facts, downloads assets, or claims factual review.
Each result feeds the same universal visual grammar as authored JSON briefs.
"""
from __future__ import annotations

import re

from .universal_kinetic import read_story

VERSION = "source-text-universal-beat-compiler-v1"
_STOP = frozenset((
    "about", "after", "again", "also", "avec", "avoir", "been", "before",
    "being", "between", "dans", "does", "dont", "elle", "elles", "encore",
    "entre", "est", "from", "have", "here", "into", "just", "leur", "mais",
    "more", "nous", "notre", "pour", "quand", "quel", "quelle", "quoi",
    "sont", "then", "there", "these", "this", "those", "tout", "tous",
    "une", "vers", "votre", "were", "what", "when", "where", "which",
    "while", "will", "with", "would", "vous", "your", "they", "them",
    "their", "that", "the", "and", "are", "was", "for", "how", "can",
    "les", "des", "une", "sur", "aux", "qui", "que", "par", "pas", "dans",
    "dont", "plus", "comme", "nous", "ils", "ses", "ces", "cette",
))
_SEQ = re.compile(r"\b(?:first|second|third|next|then|finally|afterwards|"
                  r"d'abord|ensuite|puis|enfin|premièrement|deuxièmement)\b",
                  re.IGNORECASE)
_WORDS = re.compile(r"[^\W_]+(?:['’][^\W_]+)?", re.UNICODE)


def _chunks(script: str) -> list[str]:
    if type(script) is not str or not 12 <= len(script.strip()) <= 8200:
        raise ValueError("Provide a substantive original script (12–8200 chars)")
    if any(ord(c) < 32 and c not in "\r\n\t" for c in script):
        raise ValueError("Script contains unsafe controls")
    paragraphs = [re.sub(r"\s+", " ", x).strip()
                  for x in re.split(r"\n\s*\n", script.strip()) if x.strip()]
    if len(paragraphs) == 1:
        # A one-paragraph mobile submission can still be divided by sentences.
        paragraphs = [x.strip() for x in re.split(
            r"(?<=[.!?…])\s+(?=[\wÀ-ÿ«\"'])", paragraphs[0]) if x.strip()]
    if len(paragraphs) > 12:
        # Coalesce without dropping or inventing any authored text.
        total = len(paragraphs)
        paragraphs = [" ".join(paragraphs[i*total//12:(i+1)*total//12])
                      for i in range(12)]
    if not 2 <= len(paragraphs) <= 12:
        raise ValueError("At least two sentences or paragraphs required")
    if any(len(x) > 650 for x in paragraphs):
        raise ValueError("Each narrated beat must fit 650 characters")
    if any(len(x.split()) < 3 for x in paragraphs):
        raise ValueError("Each narrated beat needs at least three words")
    return paragraphs


def _concepts(paragraph: str, topic: str) -> list[str]:
    # Source-spanned lexical extraction: only original words, never made-up
    # comparison targets or scientific values. Longer original nouns/verbs
    # get a preference but no fake linguistic POS classification is claimed.
    words = _WORDS.findall(paragraph)
    tokens = []
    for value in words:
        core = value.casefold().strip("'’")
        if len(core) >= 3 and core not in _STOP and not core.isnumeric():
            if core not in {x.casefold() for x in tokens}:
                tokens.append(value[:35])
    if len(tokens) < 2:
        for value in _WORDS.findall(topic):
            core = value.casefold()
            if len(core) >= 3 and core not in _STOP and core not in {
                    x.casefold() for x in tokens}:
                tokens.append(value[:35])
    if len(tokens) < 2:
        raise ValueError("No two meaningful visual concepts in the script")
    return tokens[:5]


def compile_original_script(*, topic: str, script: str,
                            language: str = "en") -> dict:
    if type(topic) is not str or not 3 <= len(topic.strip()) <= 150:
        raise ValueError("Topic must be 3–150 characters")
    if language not in ("en", "fr"):
        raise ValueError("Language must be en or fr")
    parts = _chunks(script)
    beats = []
    for index, narration in enumerate(parts, 1):
        clauses = [x.strip() for x in re.split(
            r"(?<=[.!?…])\s+|[;:]\s+|,\s+(?=(?:then|puis|ensuite)\b)",
            narration) if x.strip()]
        sequential = bool(_SEQ.search(narration) and len(clauses) >= 2)
        if sequential:
            steps = []
            for clause in clauses[:5]:
                # Real original text, shortened only for display.
                steps.append(" ".join(clause.split()[:4])[:35])
            graphic = {"kind": "sequence", "steps": steps}
        else:
            graphic = {"kind": "concept",
                       "nodes": _concepts(narration, topic)}
        raw_title = re.split(r"[.!?…]", narration, maxsplit=1)[0]
        title = " ".join(raw_title.split()[:10])[:90].strip()
        beats.append({"title": title or f"Part {index}",
                      "narration": narration, "sources": [], **graphic})
    return {"schemaVersion": 1, "topic": topic.strip(),
            "language": language, "beats": beats,
            "originalTextOnly": True,
            "factualResearchPerformed": False}


__all__ = ("compile_original_script", "VERSION")
