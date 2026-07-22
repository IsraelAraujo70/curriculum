# Curriculum

ATS-friendly resumes positioned for mid-level international backend and full-stack roles using Python, TypeScript, and AWS.

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

## Periodic quality eval

Run before publishing a new resume version:

```bash
./evals/run.sh english.tex
```

The eval uses local Claude Code and must score at least 85/100 with no disqualifier from `evals/midlevel_resume_rubric.md`.

