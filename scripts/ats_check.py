#!/usr/bin/env python3
"""Internal ATS readability check for the generated resume PDFs.

The score is 0-10, one point per check. It reads the PDF the way a parser does
(text extraction, fonts, images) and never looks at the LaTeX source. The rules
come from outside this file: `evals/midlevel_resume_rubric.md` (target stack,
two-page limit) and common ATS parsing practice (clean Unicode text, standard
section headings, parseable contact and dates, embedded fonts with a Unicode
map, no images).

Usage:
    python3 scripts/ats_check.py portuguese.pdf english.pdf [--min 10]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

MAX_PAGES = 2

# Target stack from the rubric ("Primary stack"), then supporting keywords.
CORE_KEYWORDS = ("TypeScript", "Node.js", "Python", "AWS")
SUPPORT_KEYWORDS = (
    "Lambda",
    "SQS",
    "DynamoDB",
    "Terraform",
    "PostgreSQL",
    "Docker",
    "CI/CD",
    "REST",
    "NestJS",
    "Next.js",
    "React",
    "SaaS",
)
MIN_SUPPORT_KEYWORDS = 9
MIN_DATED_ENTRIES = 4

HEADINGS = {
    "pt": (
        "Resumo Profissional",
        "Experiência Profissional",
        "Projetos Pessoais",
        "Formação Acadêmica",
        "Habilidades Profissionais",
        "Idiomas",
    ),
    "en": (
        "Professional Summary",
        "Professional Experience",
        "Personal Projects",
        "Education",
        "Technologies",
        "Languages",
    ),
}

MONTH_YEAR = r"(\d{2}/\d{4})"
DATE_RANGE = re.compile(MONTH_YEAR + r"\s*[–-]+\s*(?:" + MONTH_YEAR + r"|Atual|Presente|Present)")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"\+?\d[\d\s().-]{8,}\d")
GOOD_BULLET = "•"
BAD_BULLETS = set("▪◦●■□◆◇➢➤▸‣∙·")


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


def detect_language(text: str) -> str:
    lower = text.lower()
    return "pt" if "resumo profissional" in lower or "experiência profissional" in lower else "en"


def check_pages(pages: int) -> Check:
    return Check("pages", pages <= MAX_PAGES, f"{pages} pages (limit {MAX_PAGES})")


def check_unicode_clean(text: str) -> Check:
    bad: list[str] = []
    for char in text:
        category = unicodedata.category(char)
        if category == "Mn" or char == "�" or category == "Co" or char == "ı":
            bad.append(f"U+{ord(char):04X}")
    if "(cid:" in text:
        bad.append("(cid:)")
    return Check("unicode_clean", not bad, f"{len(bad)} broken characters" if bad else "clean")


def check_headings(text: str) -> Check:
    language = detect_language(text)
    lines = [line.strip() for line in text.splitlines()]
    missing = [h for h in HEADINGS[language] if not any(l.lower() == h.lower() or l.lower().startswith(h.lower()) for l in lines)]
    return Check("headings", not missing, f"missing: {', '.join(missing)}" if missing else "all standard headings")


def check_section_order(text: str) -> Check:
    """Summary, then experience, then projects and education. Skills may sit anywhere."""
    language = detect_language(text)
    lines = [line.strip().lower() for line in text.splitlines()]
    summary, experience, projects, education = (
        next((i for i, l in enumerate(lines) if l.startswith(HEADINGS[language][n].lower())), -1)
        for n in (0, 1, 2, 3)
    )
    ordered = 0 <= summary < experience < projects and experience < education
    return Check("section_order", ordered, "single-column reading order" if ordered else f"positions summary={summary} experience={experience} projects={projects} education={education}")


def check_contact(text: str) -> Check:
    head = text[:900]
    found = {
        "email": bool(EMAIL.search(head)),
        "phone": bool(PHONE.search(head)),
        "linkedin": "linkedin.com/in/" in head,
        "github": "github.com/" in head,
    }
    missing = [k for k, ok in found.items() if not ok]
    return Check("contact", not missing, f"missing: {', '.join(missing)}" if missing else "email, phone, LinkedIn, GitHub")


def check_dates(text: str) -> Check:
    starts: list[tuple[int, int]] = []
    for line in text.splitlines():
        match = DATE_RANGE.search(line)
        if match and "/" in match.group(1):
            month, year = match.group(1).split("/")
            if 2000 <= int(year) <= 2100 and 1 <= int(month) <= 12:
                starts.append((int(year), int(month)))
    ordered = starts == sorted(starts, reverse=True)
    ok = len(starts) >= MIN_DATED_ENTRIES and ordered
    return Check("dates", ok, f"{len(starts)} dated entries, reverse chronological" if ok else f"{len(starts)} dated entries, ordered={ordered}")


def check_fonts(font_table: str) -> Check:
    rows = [line.split() for line in font_table.splitlines()[2:] if line.strip()]
    if not rows:
        return Check("fonts", False, "no fonts found")
    bad = [r[0] for r in rows if len(r) < 5 or r[-5] != "yes" or r[-3] != "yes"]
    # Columns end with: emb sub uni object ID -> emb is r[-5], uni is r[-3].
    return Check("fonts", not bad, f"{len(rows)} fonts embedded with Unicode map" if not bad else f"no Unicode map: {', '.join(bad)}")


def check_bullets(text: str) -> Check:
    """Only line-initial glyphs are bullets; "·" inside a line is a text separator."""
    starts = [line.strip()[:1] for line in text.splitlines() if line.strip()]
    bad = sorted({c for c in starts if c in BAD_BULLETS})
    good = sum(1 for c in starts if c == GOOD_BULLET)
    ok = not bad and good >= 10
    return Check("bullets", ok, f"{good} standard bullets" if ok else f"standard={good}, other glyphs={''.join(bad) or 'none'}")


def check_keywords(text: str) -> Check:
    lower = text.lower()
    core_missing = [k for k in CORE_KEYWORDS if k.lower() not in lower]
    support = [k for k in SUPPORT_KEYWORDS if k.lower() in lower]
    ok = not core_missing and len(support) >= MIN_SUPPORT_KEYWORDS
    detail = f"core {len(CORE_KEYWORDS) - len(core_missing)}/{len(CORE_KEYWORDS)}, support {len(support)}/{len(SUPPORT_KEYWORDS)}"
    if core_missing:
        detail += f", missing core: {', '.join(core_missing)}"
    return Check("keywords", ok, detail)


def check_no_images(image_table: str, words: int) -> Check:
    images = [l for l in image_table.splitlines()[2:] if l.strip()]
    ok = not images and words >= 400
    return Check("no_images", ok, f"{len(images)} images, {words} words" if not ok else f"0 images, {words} words of real text")


def run_tool(args: list[str]) -> str:
    result = subprocess.run(args, capture_output=True, text=True, check=True)
    return result.stdout


def score_pdf(path: Path) -> list[Check]:
    text = run_tool(["pdftotext", "-layout", str(path), "-"])
    info = run_tool(["pdfinfo", str(path)])
    pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))  # type: ignore[union-attr]
    return [
        check_pages(pages),
        check_unicode_clean(text),
        check_headings(text),
        check_section_order(text),
        check_contact(text),
        check_dates(text),
        check_fonts(run_tool(["pdffonts", str(path)])),
        check_bullets(text),
        check_keywords(text),
        check_no_images(run_tool(["pdfimages", "-list", str(path)]), len(text.split())),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pdfs", nargs="+", type=Path)
    parser.add_argument("--min", type=int, default=10, dest="minimum")
    args = parser.parse_args()

    failed = False
    for pdf in args.pdfs:
        checks = score_pdf(pdf)
        score = sum(c.passed for c in checks)
        print(f"{pdf.name}: ATS {score}/10")
        for check in checks:
            print(f"  {'PASS' if check.passed else 'FAIL'}  {check.name}: {check.detail}")
        failed = failed or score < args.minimum
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
