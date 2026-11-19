# Curriculum

ATS-friendly resumes positioned for mid-level full-stack, backend, and applied AI roles using TypeScript, Node.js, Python, and AWS.

## Build

```bash
tectonic english.tex
tectonic portuguese.tex
```

Generated PDFs are intentionally ignored by Git.

## Gate tests

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_resume.py
```

The validator checks role positioning, experience consistency, required evidence, risky wording, and the presence of the periodic quality eval.

## ATS readability check

```bash
tectonic portuguese.tex && tectonic english.tex   # or pdflatex
python3 scripts/ats_check.py portuguese.pdf english.pdf
```

Scores each PDF from 0 to 10, one point per check: page limit, clean Unicode text, standard section headings, reading order, parseable contact, parseable dates, fonts with a Unicode map, standard bullets, rubric keywords, and no images. It reads the PDF text the way a parser does, so it catches problems the LaTeX source hides (for example, accents that extract as loose marks without T1 fonts and glyph-to-Unicode mapping).

## Periodic quality eval

Run before publishing a new resume version:

```bash
./evals/run.sh english.tex
```

The eval uses local Claude Code and must score at least 85/100 with no disqualifier from `evals/midlevel_resume_rubric.md`.
