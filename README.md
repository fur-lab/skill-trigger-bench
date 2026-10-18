# skill-trigger-bench

**Catch vague Agent Skill triggers before they cause confusing routing.** Add positive and negative example prompts for each `SKILL.md`, then run a fast, offline wording-overlap smoke test locally or in CI.

> This is a deterministic lexical proxy, not a simulator of Claude Code, Codex, Cursor, or any other agent's private runtime routing. Use it to spot wording gaps and accidental overlaps; verify actual activation in the agent you ship to.

## Why this exists

Most skill checks validate frontmatter and file structure. `skill-trigger-bench` focuses on the boundary: *what should activate this skill, and what similar request should not?* The same idea as regression tests, applied to skill descriptions.

## Quick start

```bash
python -m pip install git+https://github.com/fur-lab/skill-trigger-bench.git
skill-trigger-bench validate examples/csv-summary/SKILL.md --cases examples/csv-summary/trigger-cases.json
skill-trigger-bench run examples/csv-summary/SKILL.md --cases examples/csv-summary/trigger-cases.json
```

Run straight from a checkout:

```bash
python -m pip install -e .
python -m skill_trigger_bench run examples/csv-summary/SKILL.md --cases examples/csv-summary/trigger-cases.json
```

Example output:

```text
csv-summary: 4/4 trigger checks passed (threshold=0.30)
PASS csv-summary-request   score=1.00 expected=trigger; proxy=trigger
PASS tabular-analysis     score=0.80 expected=trigger; proxy=trigger
PASS pdf-extraction       score=0.00 expected=do not trigger; proxy=do not trigger
PASS web-deployment       score=0.00 expected=do not trigger; proxy=do not trigger
Note: lexical overlap is a wording proxy, not a prediction of a specific agent's runtime routing.
```

## Add cases to your skill repo

`trigger-cases.json` contains realistic prompts and the expected boundary:

```json
{
  "cases": [
    {"id": "csv-summary", "prompt": "Summarize a CSV dataset", "should_trigger": true},
    {"id": "pdf-near-miss", "prompt": "Extract text from a PDF", "should_trigger": false}
  ]
}
```

Keep both positive and negative examples. A good negative example is a plausible near-miss, not an unrelated prompt. See [`examples/csv-summary/`](examples/csv-summary/) for a complete sample.

## Commands

- `validate SKILL.md --cases trigger-cases.json` — check that the skill metadata and case file are valid and include both boundaries.
- `run SKILL.md --cases trigger-cases.json` — score all cases and return exit code `1` when an expected boundary is missed.
- `--threshold 0.3` — change the minimum prompt-term overlap required for a predicted trigger (range `0`–`1`).
- `--json` — emit machine-readable results for `run`.

The score is the proportion of meaningful prompt words that also occur in the skill description. It deliberately needs no API key, model download, or network request. It does **not** assess semantic equivalence, model behavior, or runtime skill loading.

## GitHub Actions

Copy [`.github/workflows/skill-trigger-bench.yml`](.github/workflows/skill-trigger-bench.yml) into your repository. Change the `skill` and `cases` paths for your own skills. The workflow installs this CLI directly from GitHub and runs the annotated boundary cases on every push and pull request.

## Development

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

## Roadmap

- Per-skill threshold overrides
- Compare trigger-case results across multiple skills to highlight overlaps
- Optional adapters for running cases against real agent runtimes

## Contributing

Issues and pull requests are welcome. Keep the default checks offline and deterministic. Please include tests for behavior changes.

## License

MIT. See [`LICENSE`](LICENSE).
