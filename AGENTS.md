# AGENTS.md - keyword-driven Playwright (Python) framework

Instructions for AI coding agents (OpenAI Codex, GitHub Copilot, Claude Code, Cursor...).

## What this project is
A Python + Playwright test framework where **tests are written in CSV files** as keyword rows
(`click`, `enter`, `validate_visible`, ...). A small engine (`framework/`) executes them; `pytest` is the runner.

## Layout
```
test_cases/*.csv           tests (one file per feature; several tests per file, keyed by test_id)
test_cases/seed/seed.csv   starting state used by the planner/generator (not run by default)
object_repository/*.csv    element name -> locator   (referenced in tests as @name)
specs/testing/*.md         test plans written by the planner agent
specs/keywords.md          the keyword vocabulary (generated - do not edit by hand)
framework/                 engine: csv_reader, executor, keywords/, locators, validator, reporting, cli
tests/test_keyword_suite.py   pytest entry point that runs the CSVs
tests/framework_selfcheck/    offline tests of the engine itself (opt-in: pytest -m selfcheck)
reports/                   results.json, screenshots/, failures/<file>_<test_id>/failure.md (+png, aria.yml, trace.zip)
.github/agents/*.agent.md  planner / generator / healer role definitions
```

## Commands
```bash
python -m framework.cli keywords          # list keywords
python -m framework.cli locators          # list object-repository elements
python -m framework.cli validate [files]  # static-check CSVs (no browser)
pytest                                    # run all CSV tests
pytest --csv test_cases/google_search.csv # one file
pytest -k TC001                           # one test id
pytest -m smoke                           # by tag
pytest -m selfcheck                       # framework self-tests (offline)
python -m framework.cli keywords --markdown > specs/keywords.md   # after adding a keyword
```

## CSV format
`test_id,test_name,tags,keyword,target,value,description` - see `specs/keywords.md` for the full reference.

## Agent roles
The role definitions are in `.github/agents/`. Copilot loads them as custom agents. In Codex (or any other tool),
when the user asks you to act as a role, **read that file, follow its body, and use the Playwright MCP tools
(`browser_*`) instead of the tool names listed in its front-matter**:

| Role | File | Produces |
|---|---|---|
| Planner | `.github/agents/playwright-test-planner.agent.md` | `specs/testing/<feature>.md` |
| Generator | `.github/agents/playwright-test-generator.agent.md` | `test_cases/<feature>.csv` + `object_repository/*.csv` |
| Healer | `.github/agents/playwright-test-healer.agent.md` | fixes to failing tests |

## Rules
- Never invent keywords; add one in `framework/keywords/` (decorated function) if genuinely missing, then regenerate `specs/keywords.md`.
- Read `reports/failures/.../failure.md` before fixing a failing test. Fix locators in `object_repository/`, not in individual rows.
- Do not weaken or remove validations to make a test pass. Do not use hard `wait` rows; use `wait_for` / `validate_*`.
- Do not bypass CAPTCHAs, bot detection or rate limits.
- Keep tests independent: each one opens its own browser and closes it.
