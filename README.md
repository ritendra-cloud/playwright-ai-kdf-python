# Playwright AI keyword-driven framework (Python)

A **keyword-driven** test framework in Python. Tests are written as rows in **CSV files**
(`click`, `enter`, `validate_visible`, ...), executed by Playwright, and maintained with the help of three
AI agents - **planner**, **generator** and **healer** - that drive a real browser through the
**Playwright MCP server** from **GitHub Copilot** or **OpenAI Codex**.

It follows the structure of the TypeScript reference project (agents in `.github/agents`, MCP config, context files, `specs/`,
seed test, page-object idea) and adapts it to Python and to CSV.

## What a test looks like

`test_cases/google_search.csv` - launch Chrome, search Google, verify the results, close Chrome:

| test_id | test_name | tags | keyword | target | value | description |
|---|---|---|---|---|---|---|
| TC001 | Google search returns relevant results | smoke;external | set_variable | SEARCH_TEXT | `${env.SEARCH_TEXT:-Playwright Python}` | Text to search for |
| TC001 | | | open_browser | | | Launch Chrome |
| TC001 | | | navigate | | https://www.google.com | Open Google |
| TC001 | | | click_if_visible | `@google.consent_accept_all` | | Dismiss cookie pop-up if shown |
| TC001 | | | validate_visible | `@google.search_box` | | Search box is displayed |
| TC001 | | | enter | `@google.search_box` | `${SEARCH_TEXT}` | Type the search text |
| TC001 | | | press_key | `@google.search_box` | Enter | Submit |
| TC001 | | | wait_for | `@google.results_container` | | Results loaded |
| TC001 | | | validate_url_contains | | /search | On the results page |
| TC001 | | | validate_title_contains | | `${SEARCH_TEXT}` | Title contains the search text |
| TC001 | | | validate_count_at_least | `@google.result_titles` | 3 | At least 3 results |
| TC001 | | | validate_contains_ignore_case | `@google.results_container` | `${SEARCH_TEXT}` | Results mention the text |
| TC001 | | | screenshot | | google-results.png | Evidence |
| TC001 | | | close_browser | | | Close Chrome |

`@google.search_box` etc. are element names defined once in `object_repository/google.csv`. When Google changes its
markup you fix one line there and every test is healed.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chrome            # the installed-Chrome channel (the default here)
# alternatively: playwright install chromium   and set KDF_CHANNEL= (empty) to use bundled Chromium

pytest                                # runs test_cases/google_search.csv in a visible Chrome window
SEARCH_TEXT="model context protocol" pytest      # search for something else (Windows: set SEARCH_TEXT=...)
```

Settings live in environment variables or a `.env` file (copy `.env.example`): browser/channel, headless, timeouts, slow-motion, base URL.

## Project layout

| Path | Reference TS project equivalent | Purpose |
|---|---|---|
| `test_cases/*.csv` | `tests/**/*.spec.ts` | The tests (keyword rows) |
| `test_cases/seed/seed.csv` | `tests/seed.spec.ts` | Starting state for planner/generator |
| `object_repository/*.csv` | `tests/pages/*.ts` (Page Objects) | Named locators |
| `framework/` | Playwright Test runner + fixtures | The engine (CSV reader, keywords, executor, reports) |
| `tests/test_keyword_suite.py` | `playwright.config.ts` `testDir` | pytest runs every CSV scenario as a test |
| `.github/agents/*.agent.md` | same | Planner / generator / healer |
| `.vscode/mcp.json`, `.codex/config.toml` | `.vscode/mcp.json` | MCP server for Copilot / Codex |
| `.github/copilot-instructions.md`, `AGENTS.md`, `CLAUDE.md` | same | Context for the AI tools |
| `specs/testing/*.md`, `specs/keywords.md` | `specs/testing/*.md` | Plans, keyword reference |
| `reports/` | `test-results/` | `results.json`, screenshots, failure bundles |

## Keywords

46 keywords in four groups - full table with examples in **[specs/keywords.md](specs/keywords.md)** (or `python -m framework.cli keywords`).

- **Browser:** `open_browser`, `close_browser`, `navigate`, `refresh`, `go_back`, `go_forward`
- **Interaction:** `click`, `double_click`, `right_click`, `hover`, `click_if_visible`, `enter`, `enter_secret` (masked in logs), `type_slowly`, `clear`, `press_key`, `select`, `check`, `uncheck`, `scroll_to`, `upload_file`, `wait_for`, `wait_for_url`, `wait`
- **Validation:** `validate` (+ `_visible`, `_hidden`, `_text`, `_contains`, `_contains_ignore_case`, `_page_contains`, `_value`, `_attribute`, `_enabled`, `_disabled`, `_checked`, `_count`, `_count_at_least`, `_title`, `_title_contains`, `_url`, `_url_contains`). Each also works as `verify_*`.
- **Data & utility:** `set_variable`, `store_text`, `screenshot`, `log`

Validations retry automatically until `KDF_TIMEOUT_MS`, so you rarely need waits. Keyword names are forgiving (`Validate Visible`, `validate-visible` and `verify_visible` are the same).

**Targets** can be `@repository.name`, `role=button[name="Save"]`, `label=`, `placeholder=`, `text=`, `testid=`, `css=`, `xpath=` or a plain CSS selector, optionally ending in `>> first`, `>> last` or `>> nth=2`.
**Variables:** `${NAME}`, `${env.NAME:-default}`, `${config.base_url}`, `${timestamp}`, `${uuid}`, `${random}`, `${date}`.
**Tags** become pytest markers (`pytest -m smoke`); `skip` or `fixme` disables a test.

**Adding a keyword** is one decorated function in `framework/keywords/`:

```python
@keyword("double_click", category="Interaction", target="required", doc="Double-click an element.",
         example=("text=Row 1", ""))
def double_click(ctx, target, value):
    ctx.locator(target).dblclick()
```
then `python -m framework.cli keywords --markdown > specs/keywords.md` (a self-test fails if you forget).

## Running

```bash
pytest                                     # all CSV tests
pytest --csv test_cases/google_search.csv  # one file (or folder)
pytest -k TC001                            # one test id
pytest -m "smoke and not external"         # by tag
pytest --include-seed                      # also run the seed tests
python -m framework.cli validate           # check all CSVs without opening a browser
pytest -m selfcheck                        # tests of the framework itself (offline, needs bundled Chromium)
```

Live step log while running, then `reports/results.json`. **When a step fails**, `reports/failures/<file>_<test_id>/` contains
`failure.md` (step, CSV line, resolved locator, error, URL, accessibility snapshot), `failure.png`, `aria.yml` and `trace.zip`
(`python -m playwright show-trace trace.zip`). The browser is closed even when a test fails.

## Using the AI agents

The agents are prompt files, so they run *inside* Copilot or Codex - they are not Python programs. All three drive a
real browser through the Playwright MCP server and hand work to each other through files:

```
Planner  ->  specs/testing/<feature>.md  ->  Generator  ->  test_cases/<feature>.csv + object_repository/*.csv  ->  Healer (fixes failures)
```

**GitHub Copilot (VS Code)** - the recommended path, matching the reference project
1. Open this folder in VS Code with Copilot Chat. Start the `playwright` server from `.vscode/mcp.json` (the *Start* lens above the server entry).
2. In the Chat agent picker choose `playwright-test-planner`, and ask e.g.:
   *"Explore https://www.google.com and plan tests for searching. Save the plan to specs/testing/google-search.md"*
3. Switch to `playwright-test-generator`: *"Generate the CSV test for scenario 1 of specs/testing/google-search.md"*
4. When something fails, pick `playwright-test-healer`: *"Run the tests and fix any failures"*

**OpenAI Codex (CLI / IDE)**
1. Make sure the MCP server is registered: `.codex/config.toml` is included; if Codex doesn't pick it up run `codex mcp add playwright -- npx @playwright/mcp@latest`.
2. `AGENTS.md` is read automatically. Ask by role: *"Act as the playwright-test-planner (see .github/agents/) and plan Google search tests"*, then *"...as the generator..."*, *"...as the healer..."*.

Requires Node.js (for `npx @playwright/mcp@latest`). Tool names in the agent front-matter (`read`, `edit`, `execute`, `playwright/*`) can differ slightly between
VS Code versions - if a tool is reported missing, adjust the list via the *Configure Tools* picker.

## CI

`.github/workflows/run-tests.yml` validates the CSVs, runs the offline self-checks and every test not tagged `external`.
Google is tagged `external` because CAPTCHAs are common from datacenter IPs.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Could not launch 'chrome'` | `playwright install chrome`, or set `KDF_CHANNEL=` (empty) to use bundled Chromium |
| Google shows a CAPTCHA / URL has `/sorry/` | Too many automated requests or a flagged IP. Run headed (`KDF_HEADLESS=false`), slow down, wait, or test your own application instead. The framework deliberately does not try to evade bot detection |
| `navigate ... returned HTTP 4xx/5xx` | The site rejected the request (rate limit, block, outage) - see above |
| `too many columns` in a CSV | A cell with a comma needs double quotes, and quotes inside it must be doubled |
| `Unknown element '@x'` | Add it to `object_repository/*.csv` (the message suggests close matches) |
| `strict mode violation ... resolved to N elements` | Make the locator unique or append `>> first` / `>> nth=N` |

## Verification status

Verified in a sandbox with Playwright 1.56 and Chromium: 20 offline self-checks (CSV parsing, locators, variables, all main keywords, failure bundles,
guaranteed browser close), and the real `google_search.csv` + `google.csv` run end to end (14/14 steps) against a local page that
imitates Google's structure. **Not verified against live google.com** (no internet access in the sandbox): Google changes its markup and bot checks without notice, so run
`pytest` once on your machine and, if a locator needs adjusting, edit `object_repository/google.csv` (or let the healer agent do it).
The Copilot/Codex agent files follow the reference project's format but have not been executed inside those tools.
