from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ats_check", ROOT / "scripts" / "ats_check.py")
assert SPEC and SPEC.loader
ATS = importlib.util.module_from_spec(SPEC)
sys.modules["ats_check"] = ATS
SPEC.loader.exec_module(ATS)

PT_SECTIONS = "\n".join(
    ("Resumo Profissional", "x", "Experiência Profissional", "x", "Projetos Pessoais", "x", "Formação Acadêmica", "x", "Habilidades Profissionais", "Idiomas")
)


class AtsCheckTests(unittest.TestCase):
    def test_flags_loose_accents_but_accepts_normal_text(self) -> None:
        self.assertFalse(ATS.check_unicode_clean("L\u0131\u0301der T\u00e9cnico").passed)
        self.assertTrue(ATS.check_unicode_clean("Líder Técnico, recebíveis").passed)

    def test_bullet_glyph_only_matters_at_line_start(self) -> None:
        good = "\n".join(["• item"] * 10 + ["Next.js · PostgreSQL · Rust"])
        self.assertTrue(ATS.check_bullets(good).passed)
        self.assertFalse(ATS.check_bullets("\n".join(["▪ item"] * 10)).passed)
        self.assertFalse(ATS.check_bullets("• só um").passed)

    def test_dates_must_parse_and_run_newest_first(self) -> None:
        newest_first = "A 10/2026 – Atual\nB 04/2026 – Atual\nC 10/2025 – 05/2026\nD 01/2025 – 10/2025"
        self.assertTrue(ATS.check_dates(newest_first).passed)
        self.assertFalse(ATS.check_dates("\n".join(reversed(newest_first.splitlines()))).passed)
        self.assertFalse(ATS.check_dates("A 2026 – hoje\nB 2025 – 2026").passed)

    def test_section_order_allows_skills_first_but_not_experience_first(self) -> None:
        self.assertTrue(ATS.check_section_order(PT_SECTIONS).passed)
        swapped = PT_SECTIONS.replace("Resumo Profissional", "TMP").replace("Experiência Profissional", "Resumo Profissional").replace("TMP", "Experiência Profissional")
        self.assertFalse(ATS.check_section_order(swapped).passed)

    def test_headings_found_even_in_uppercase(self) -> None:
        self.assertTrue(ATS.check_headings(PT_SECTIONS.upper()).passed)
        self.assertFalse(ATS.check_headings(PT_SECTIONS.replace("Idiomas", "")).passed)

    def test_keywords_need_the_rubric_core_stack(self) -> None:
        core = " ".join(ATS.CORE_KEYWORDS)
        support = " ".join(ATS.SUPPORT_KEYWORDS)
        self.assertTrue(ATS.check_keywords(core + " " + support).passed)
        self.assertFalse(ATS.check_keywords(core.replace("AWS", "") + " " + support).passed)

    def test_page_limit_is_two(self) -> None:
        self.assertTrue(ATS.check_pages(2).passed)
        self.assertFalse(ATS.check_pages(3).passed)


if __name__ == "__main__":
    unittest.main()
