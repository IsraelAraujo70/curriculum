#!/usr/bin/env bash
set -euo pipefail

resume_path="${1:-english.tex}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
rubric_path="$repo_root/evals/midlevel_resume_rubric.md"

if [[ ! -f "$resume_path" ]]; then
  resume_path="$repo_root/$resume_path"
fi

if [[ ! -f "$resume_path" ]]; then
  echo "Resume not found: $resume_path" >&2
  exit 2
fi

prompt="$(printf '%s\n\nRESUME SOURCE:\n%s' "$(<"$rubric_path")" "$(<"$resume_path")")"
claude --model gpt-5.6-sol --print "$prompt"

