#!/usr/bin/env python3
"""Fast, deterministic quality gate for the resume sources."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED = {
    "english.tex": (
        "Mid-Level Full-Stack \\& AI Software Engineer",
        "3+ years",
        "Python",
        "TypeScript",
        "AWS",
        "Moneria",
        "ComicConnect",
        "(Contract)",
        "Professional working proficiency",
        "\\usepackage[T1]{fontenc}",
        "\\pdfgentounicode=1",
    ),
    "portuguese.tex": (
        "Engenheiro de Software Full Stack e IA Pleno",
        "3+ anos",
        "Python",
        "TypeScript",
        "AWS",
        "Moneria",
        "ComicConnect",
        "(Contrato)",
        "Proficiência profissional",
        "\\usepackage[T1]{fontenc}",
        "\\pdfgentounicode=1",
    ),
}

BANNED_PATTERNS = {
    r"1[.,]500\+ commits": "commit-volume vanity metric",
    r"500\+ PRs": "PR-volume vanity metric",
    r"\d+k\+ stars": "repository-star borrowing",
    r"\d[\d.,]*\s*\+?\s*(PRs?|pull requests?|commits?)\b": "volume metric (PRs or commits)",
    r"\\color\{white\}|\\pdfliteral|\\tiny": "hidden-text wording",
    r"bypass .*bot detection": "unsafe automation wording",
    r"residential proxy": "proxy-evasion wording",
    r"Full Stack Software Engineer with 2\+ years": "stale experience claim",
    r"Engenheiro de Software Full Stack com 2\+ anos": "stale experience claim",
}


MONERIA_ENTRY = re.compile(r"Moneria[^\n]*\\hfill 10/2026 --")


def strip_comments(text: str) -> str:
    """Remove LaTeX comments so a phrase or date inside `%` cannot satisfy a check."""
    return re.sub(r"(?<!\\)%.*", "", text)


def validate_text(filename: str, text: str) -> list[str]:
    text = strip_comments(text)
    errors: list[str] = []
    if filename in REQUIRED and not MONERIA_ENTRY.search(text):
        errors.append(f"{filename}: Moneria entry must start 10/2026 on its heading line")
    for phrase in REQUIRED[filename]:
        if phrase not in text:
            errors.append(f"{filename}: missing required phrase: {phrase}")

    for pattern, reason in BANNED_PATTERNS.items():
        if re.search(pattern, text, flags=re.IGNORECASE):
            errors.append(f"{filename}: contains {reason}: /{pattern}/")

    bullet_count = text.count("\\item ")
    if bullet_count > 30:
        errors.append(f"{filename}: {bullet_count} bullets exceeds the 30-bullet limit")

    return errors


def validate_repository(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    documents: dict[str, str] = {}

    for filename in REQUIRED:
        path = root / filename
        if not path.exists():
            errors.append(f"missing resume source: {filename}")
            continue
        documents[filename] = strip_comments(path.read_text(encoding="utf-8"))
        errors.extend(validate_text(filename, documents[filename]))

    if len(documents) == 2:
        for date in ("10/2026", "04/2026", "10/2025", "05/2026", "01/2025", "06/2023", "06/2025"):
            if any(date not in text for text in documents.values()):
                errors.append(f"experience date is inconsistent across languages: {date}")

        shared_links = (
            "israelaraujodeoliveira@gmail.com",
            "linkedin.com/in/araisr",
            "+55 (35) 99742-1900",
            "github.com/IsraelAraujo70",
            "portfolio.israeldeveloper.com.br",
        )
        for link in shared_links:
            if any(link not in text for text in documents.values()):
                errors.append(f"contact link is inconsistent across languages: {link}")

    rubric = root / "evals" / "midlevel_resume_rubric.md"
    runner = root / "evals" / "run.sh"
    if not rubric.exists():
        errors.append("missing periodic eval rubric")
    if not runner.exists():
        errors.append("missing periodic eval runner")

    return errors


def main() -> int:
    errors = validate_repository()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("PASS: resume sources are focused, consistent, and eval-ready")
    return 0


if __name__ == "__main__":
    sys.exit(main())
