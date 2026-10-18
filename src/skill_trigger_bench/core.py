"""A deterministic lexical smoke test for Agent Skill trigger descriptions.

This is a proxy for wording overlap, not an agent-runtime activation simulator.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Skill:
    name: str
    description: str


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    prompt: str
    expected: bool
    score: float
    predicted: bool
    status: str


@dataclass(frozen=True)
class RunResult:
    passed: int
    failed: int
    threshold: float
    items: list[CaseResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "failed": self.failed,
            "threshold": self.threshold,
            "items": [asdict(item) for item in self.items],
        }


_WORD = re.compile(r"[a-z0-9]+", re.IGNORECASE)
_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "do", "does", "for",
    "from", "help", "i", "in", "is", "it", "me", "my", "of", "on", "or",
    "please", "the", "this", "to", "use", "when", "with", "you", "your",
}


def load_skill(path: str | Path) -> Skill:
    """Read a SKILL.md file and validate its required frontmatter fields."""
    content = Path(path).read_text(encoding="utf-8")
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter delimited by ---")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("SKILL.md frontmatter is missing its closing ---") from exc
    try:
        metadata = yaml.safe_load("\n".join(lines[1:end])) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML frontmatter: {exc}") from exc
    if not isinstance(metadata, dict):
        raise ValueError("frontmatter must be a YAML mapping")
    name = metadata.get("name")
    description = metadata.get("description")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("frontmatter requires a non-empty name")
    if not isinstance(description, str) or not description.strip():
        raise ValueError("frontmatter requires a non-empty description")
    return Skill(name=name.strip(), description=" ".join(description.split()))


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in _WORD.findall(text) if len(token) > 1 and token.lower() not in _STOP_WORDS}


def score_prompt(description: str, prompt: str) -> float:
    """Return the fraction of meaningful prompt terms present in the description."""
    terms = _tokens(prompt)
    if not terms:
        return 0.0
    return len(terms & _tokens(description)) / len(terms)


def run_cases(
    description: str,
    cases: list[dict[str, Any]],
    threshold: float = 0.3,
    require_boundaries: bool = True,
) -> RunResult:
    """Compare annotated positive/negative prompts against a lexical threshold."""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0 and 1")
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a non-empty list")
    validated: list[tuple[str, str, bool]] = []
    for index, case in enumerate(cases, 1):
        if not isinstance(case, dict):
            raise ValueError(f"case {index} must be an object")
        prompt = case.get("prompt")
        expected = case.get("should_trigger")
        case_id = case.get("id", f"case-{index}")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"case {case_id} requires a non-empty prompt")
        if not isinstance(expected, bool):
            raise ValueError(f"case {case_id} requires boolean should_trigger")
        validated.append((str(case_id), prompt.strip(), expected))
    if require_boundaries and (not any(row[2] for row in validated) or all(row[2] for row in validated)):
        raise ValueError("include at least one positive and one negative trigger case")

    items = []
    for case_id, prompt, expected in validated:
        score = score_prompt(description, prompt)
        predicted = score >= threshold
        items.append(CaseResult(
            case_id=case_id,
            prompt=prompt,
            expected=expected,
            score=round(score, 4),
            predicted=predicted,
            status="PASS" if predicted == expected else "FAIL",
        ))
    failed = sum(item.status == "FAIL" for item in items)
    return RunResult(passed=len(items) - failed, failed=failed, threshold=threshold, items=items)
