from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import date
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
    def test_flags_each_text_extraction_defect_and_accepts_normal_text(self) -> None:
        self.assertFalse(ATS.check_unicode_clean("L\u0131der").passed, "dotless i alone")
        self.assertFalse(ATS.check_unicode_clean("Li\u0301der").passed, "combining accent alone")
        self.assertFalse(ATS.check_unicode_clean("L\ufffdder").passed, "replacement character")
        self.assertFalse(ATS.check_unicode_clean("(cid:12)").passed, "unmapped glyph id")
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


class AtsCheckGapTests(unittest.TestCase):
    def test_dates_reject_impossible_values(self) -> None:
        base = "B 04/2026 – Atual\nC 10/2025 – 05/2026\nD 01/2025 – 10/2025\nE 06/2023 – 06/2025"
        for bad in ("A 13/2025 – Atual", "A 10/2025 – 05/2019", "A 10/2099 – Atual"):
            first = bad + "\n" + base
            self.assertFalse(ATS.check_dates(first, today=date(2026, 11, 19)).passed, bad)
        self.assertTrue(ATS.check_dates("A 10/2026 – Atual\n" + base, today=date(2026, 11, 19)).passed)

    def test_pages_reject_a_nearly_empty_page(self) -> None:
        self.assertFalse(ATS.check_pages(2, [955, 0]).passed)
        self.assertTrue(ATS.check_pages(2, [900, 400]).passed)

    def test_keywords_reject_stuffing(self) -> None:
        core = " ".join(ATS.CORE_KEYWORDS)
        support = " ".join(ATS.SUPPORT_KEYWORDS)
        self.assertFalse(ATS.check_keywords((core + " ") * 12 + support).passed)

    def test_contact_needs_all_four_channels(self) -> None:
        full = "a@b.com +55 (35) 99742-1900 linkedin.com/in/x github.com/x"
        self.assertTrue(ATS.check_contact(full).passed)
        self.assertFalse(ATS.check_contact(full.replace("a@b.com", "")).passed)

    def test_fonts_need_unicode_map_unless_encoding_is_standard(self) -> None:
        header = "name type encoding emb sub uni object ID\n---\n"
        standard = header + "Arial TrueType WinAnsi no no no 10 0\n"
        custom = header + "F45 Type 1 Custom yes yes no 12 0\n"
        mapped = header + "LMSans10 Type 1 Custom yes yes yes 12 0\n"
        self.assertTrue(ATS.check_fonts(standard).passed)
        self.assertFalse(ATS.check_fonts(custom).passed)
        self.assertTrue(ATS.check_fonts(mapped).passed)

    def test_images_fail_even_with_enough_text(self) -> None:
        header = "page num type\n---\n"
        self.assertFalse(ATS.check_no_images(header + "1 0 image\n", 900).passed)
        self.assertTrue(ATS.check_no_images(header, 900).passed)


if __name__ == "__main__":
    unittest.main()
