import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from skill_trigger_bench.cli import main


class CliTests(unittest.TestCase):
    def test_run_command_prints_json_and_returns_failure_code_for_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "SKILL.md"
            skill.write_text(
                "---\nname: pdf-helper\ndescription: Extract PDF tables.\n---\n",
                encoding="utf-8",
            )
            cases = root / "cases.json"
            cases.write_text(json.dumps({"cases": [
                {"id": "positive", "prompt": "Extract PDF tables", "should_trigger": True},
                {"id": "negative", "prompt": "Extract PDF tables", "should_trigger": False},
            ]}), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main(["run", str(skill), "--cases", str(cases), "--json"])
        self.assertEqual(exit_code, 1)
        self.assertEqual(json.loads(output.getvalue())["failed"], 1)

    def test_validate_command_requires_a_negative_example(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "SKILL.md"
            skill.write_text("---\nname: pdf-helper\ndescription: Extract PDF tables.\n---\n", encoding="utf-8")
            cases = root / "cases.json"
            cases.write_text(json.dumps({"cases": [
                {"prompt": "Extract PDF tables", "should_trigger": True}
            ]}), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main(["validate", str(skill), "--cases", str(cases)])
        self.assertEqual(exit_code, 2)
        self.assertIn("positive and one negative", output.getvalue())


if __name__ == "__main__":
    unittest.main()
