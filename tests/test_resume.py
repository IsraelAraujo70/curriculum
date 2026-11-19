from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_resume", ROOT / "scripts" / "validate_resume.py"
)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ResumeValidatorTests(unittest.TestCase):
    def test_current_repository_passes(self) -> None:
        self.assertEqual([], VALIDATOR.validate_repository(ROOT))

    def test_rejects_vanity_metrics_and_proxy_evasion(self) -> None:
        text = "1,500+ commits; 500+ PRs; residential proxy to bypass bot detection"
        errors = VALIDATOR.validate_text("english.tex", text)
        combined = "\n".join(errors)
        self.assertIn("commit-volume vanity metric", combined)
        self.assertIn("PR-volume vanity metric", combined)
        self.assertIn("proxy-evasion wording", combined)
        self.assertIn("unsafe automation wording", combined)

    def test_rejects_missing_cross_language_dates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for filename, required in VALIDATOR.REQUIRED.items():
                text = "\n".join(required)
                text += "\n" + "\n".join(
                    (
                        "10/2026",
                        "04/2026",
                        "10/2025",
                        "05/2026",
                        "01/2025",
                        "06/2023",
                        "06/2025",
                        "israelaraujodeoliveira@gmail.com",
                        "linkedin.com/in/araisr",
                        "github.com/IsraelAraujo70",
                        "portfolio.israeldeveloper.com.br",
                    )
                )
                (root / filename).write_text(text, encoding="utf-8")

            portuguese = root / "portuguese.tex"
            portuguese.write_text(
                portuguese.read_text(encoding="utf-8").replace("04/2026", ""),
                encoding="utf-8",
            )
            (root / "evals").mkdir()
            (root / "evals" / "midlevel_resume_rubric.md").write_text("rubric")
            (root / "evals" / "run.sh").write_text("runner")

            errors = VALIDATOR.validate_repository(root)
            self.assertTrue(any("04/2026" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

