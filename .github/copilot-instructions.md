# Keyword-driven Playwright (Python) framework - working agreement

Read `AGENTS.md` first: it describes the layout, the CSV format and the commands. Then:

1. Tests are **CSV rows**, not code. Keywords available: `specs/keywords.md` (never invent one - add it in `framework/keywords/` if truly needed).
2. Locators live in `object_repository/*.csv` and are referenced as `@name`. Prefer role > label > placeholder > text > testid > css.
3. Every test starts from the seed state in `test_cases/seed/seed.csv`, is independent, and follows Arrange-Act-Assert:
   open/navigate, act, then `validate_*` the outcome. Every test ends with at least one validation.
4. Explore or debug the live app with the Playwright MCP server (`.vscode/mcp.json`); use `browser_snapshot` before guessing locators.
5. After editing any CSV run `python -m framework.cli validate`, then `pytest --csv <file>`.
6. Failures produce `reports/failures/<file>_<test_id>/failure.md` - read it before changing anything.
7. Never weaken assertions to get a green run. Never bypass CAPTCHAs or bot protection.
8. Use the agents: `playwright-test-planner` -> `specs/testing/*.md`; `playwright-test-generator` -> `test_cases/*.csv`;
   `playwright-test-healer` -> fixes failing tests.
