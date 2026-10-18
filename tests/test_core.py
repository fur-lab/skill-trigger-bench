import json
import tempfile
import unittest
from pathlib import Path

from skill_trigger_bench.core import load_skill, run_cases


class SkillLoadingTests(unittest.TestCase):
    def test_loads_skill_name_and_multiline_description(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text(
                "---\nname: pdf-helper\ndescription: >-\n  Extract PDF tables and merge PDF files.\n---\n# Instructions\n",
                encoding="utf-8",
            )
            skill = load_skill(path)
        self.assertEqual(skill.name, "pdf-helper")
        self.assertEqual(skill.description, "Extract PDF tables and merge PDF files.")

    def test_rejects_missing_description(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text("---\nname: pdf-helper\n---\nBody\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "description"):
                load_skill(path)


class TriggerCaseTests(unittest.TestCase):
    def test_passes_positive_and_negative_boundary_cases(self):
        cases = [
            {"id": "pdf-task", "prompt": "Extract tables from PDF files", "should_trigger": True},
            {"id": "web-task", "prompt": "Deploy my web application", "should_trigger": False},
        ]
        result = run_cases("Extract PDF tables and merge PDF files", cases, threshold=0.3)
        self.assertEqual(result.passed, 2)
        self.assertEqual(result.failed, 0)
        self.assertEqual([item.status for item in result.items], ["PASS", "PASS"])

    def test_flags_positive_case_with_no_description_overlap(self):
        cases = [
            {"id": "wrong-domain", "prompt": "Deploy my web application", "should_trigger": True},
            {"id": "near-miss", "prompt": "Write a sorting algorithm", "should_trigger": False},
        ]
        result = run_cases("Extract PDF tables and merge PDF files", cases, threshold=0.3)
        self.assertEqual(result.failed, 1)
        self.assertEqual(result.items[0].status, "FAIL")

    def test_requires_both_positive_and_negative_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cases.json"
            path.write_text(json.dumps({"cases": [{"prompt": "pdf", "should_trigger": True}]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "at least one positive and one negative"):
                run_cases("PDF skill", json.loads(path.read_text(encoding="utf-8"))["cases"], threshold=0.3, require_boundaries=True)


if __name__ == "__main__":
    unittest.main()
