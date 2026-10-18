"""Command-line interface for skill-trigger-bench."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .core import load_skill, run_cases


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skill-trigger-bench",
        description="Smoke-test Agent Skill trigger descriptions with positive and negative prompts.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "validate"):
        command = commands.add_parser(name, help=f"{name} trigger cases")
        command.add_argument("skill", type=Path, help="path to SKILL.md")
        command.add_argument("--cases", required=True, type=Path, help="path to trigger-cases.json")
        command.add_argument("--threshold", type=float, default=0.3, help="lexical overlap threshold (0-1; default: 0.3)")
        if name == "run":
            command.add_argument("--json", action="store_true", help="print machine-readable JSON")
    return parser


def _load_cases(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("cases"), list):
        raise ValueError("cases file must be a JSON object with a 'cases' array")
    return data["cases"]


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        skill = load_skill(args.skill)
        cases = _load_cases(args.cases)
        result = run_cases(skill.description, cases, threshold=args.threshold)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stdout)
        return 2

    if args.command == "validate":
        print(f"valid: {skill.name} · {len(cases)} cases · positive and negative boundaries present")
        return 0

    if args.json:
        print(json.dumps({"skill": skill.name, **result.to_dict()}, indent=2))
    else:
        print(f"{skill.name}: {result.passed}/{result.passed + result.failed} trigger checks passed (threshold={result.threshold:.2f})")
        for item in result.items:
            expected = "trigger" if item.expected else "do not trigger"
            predicted = "trigger" if item.predicted else "do not trigger"
            print(f"{item.status:4} {item.case_id:20} score={item.score:.2f} expected={expected}; proxy={predicted}")
        print("Note: lexical overlap is a wording proxy, not a prediction of a specific agent's runtime routing.")
    return 1 if result.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
