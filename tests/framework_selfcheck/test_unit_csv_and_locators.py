"""Fast unit tests (no browser) for the framework's parsing and validation logic."""
from __future__ import annotations

import pytest

from framework.cli import render_keywords_markdown
from framework.config import ROOT
from framework.context import ExecutionContext
from framework.csv_reader import read_scenarios
from framework.errors import CsvFormatError, KeywordError
from framework.keywords import get_keyword
from framework.locators import parse_locator
from framework.config import load_settings
from framework.object_repository import ObjectRepository

pytestmark = pytest.mark.selfcheck


def _write(tmp_path, text):
    path = tmp_path / "t.csv"
    path.write_text(text, encoding="utf-8")
    return path


# ------------------------------------------------------------------ CSV reader
def test_groups_rows_into_scenarios_and_reads_metadata(tmp_path):
    path = _write(tmp_path, (
        "test_id,test_name,tags,keyword,target,value,description\n"
        "A1,First,smoke;external,open_browser,,,\n"
        ",,,navigate,,example.com,blank test_id continues A1\n"
        "# a comment row\n"
        "\n"
        "B2,,,open_browser,,,\n"))
    a, b = read_scenarios(path)
    assert (a.id, a.name, a.tags, len(a.steps)) == ("A1", "First", ("smoke", "external"), 2)
    assert (b.id, b.name, len(b.steps)) == ("B2", "B2", 1)
    assert a.steps[1].line == 3


def test_excel_bom_and_case_insensitive_headers(tmp_path):
    path = tmp_path / "bom.csv"
    path.write_bytes("\ufeffTest_ID,KEYWORD,Target\nX,click,#a\n".encode("utf-8"))
    assert read_scenarios(path)[0].steps[0].target == "#a"


def test_too_many_columns_gives_actionable_message(tmp_path):
    path = _write(tmp_path, "test_id,keyword,target,value\nA,click,css=a,b,c\n")
    with pytest.raises(CsvFormatError, match="too many columns"):
        read_scenarios(path)


def test_non_adjacent_test_ids_and_unknown_columns_are_rejected(tmp_path):
    with pytest.raises(CsvFormatError, match="non-adjacent"):
        read_scenarios(_write(tmp_path, "test_id,keyword\nA,click\nB,click\nA,click\n"))
    with pytest.raises(CsvFormatError, match="unknown column"):
        read_scenarios(_write(tmp_path, "test_id,keyword,selector\nA,click,x\n"))


def test_quoted_cells_may_contain_commas(tmp_path):
    path = _write(tmp_path, 'test_id,keyword,target\nA,click,"css=textarea[name=q],input[name=q]"\n')
    assert read_scenarios(path)[0].steps[0].target == "css=textarea[name=q],input[name=q]"


# ------------------------------------------------------------------ locators
@pytest.mark.parametrize("text,kind,value,name,nth", [
    ('role=button[name="Search"]', "role", "button", "Search", None),
    ("role=button[name=Save, exact=true]", "role", "button", "Save", None),
    ("role=link", "role", "link", None, None),
    ("label=Email", "label", "Email", None, None),
    ("css=#search a h3 >> first", "css", "#search a h3", None, "first"),
    ("#search a h3 >> nth=2", "raw", "#search a h3", None, "nth=2"),
    ("text=Sign in >> last", "text", "Sign in", None, "last"),
])
def test_parse_locator_forms(text, kind, value, name, nth):
    spec = parse_locator(text)
    assert (spec.kind, spec.value, spec.name, spec.nth) == (kind, value, name, nth)


def test_object_repository_reference_and_helpful_typo_hint():
    repo = ObjectRepository({"app.save": "role=button[name=Save]"})
    assert parse_locator("@app.save", repo).name == "Save"
    with pytest.raises(KeywordError, match="Did you mean: @app.save"):
        parse_locator("@app.sav", repo)
    with pytest.raises(KeywordError, match="no object repository"):
        parse_locator("@app.save")


# ------------------------------------------------------------------ variables
def test_variable_resolution(monkeypatch):
    ctx = ExecutionContext(load_settings(), ObjectRepository(), variables={"NAME": "Ada"})
    monkeypatch.delenv("KDF_TEST_VAR", raising=False)
    assert ctx.resolve("Hi ${NAME}!") == "Hi Ada!"
    assert ctx.resolve("${env.KDF_TEST_VAR:-fallback}") == "fallback"
    monkeypatch.setenv("KDF_TEST_VAR", "from-env")
    assert ctx.resolve("${env.KDF_TEST_VAR:-fallback}") == "from-env"
    assert ctx.resolve("${timestamp}").isdigit()
    with pytest.raises(KeywordError, match="Undefined variable"):
        ctx.resolve("${MISSING}")


# ------------------------------------------------------------------ registry / docs
def test_verify_aliases_and_normalisation():
    assert get_keyword("Verify Visible").name == "validate_visible"
    assert get_keyword("type_text").name == "enter"
    assert get_keyword("nope") is None


def test_keyword_reference_in_specs_is_up_to_date():
    committed = (ROOT / "specs" / "keywords.md").read_text(encoding="utf-8")
    assert committed == render_keywords_markdown(), (
        "specs/keywords.md is stale. Run: python -m framework.cli keywords --markdown > specs/keywords.md")


def test_shipped_test_cases_are_valid():
    from framework.cli import discover_csv
    from framework.validator import validate_files
    settings = load_settings()
    files = discover_csv(settings, include_seed=True)
    assert files, "expected CSV files under test_cases/"
    _, issues = validate_files(files, ObjectRepository.load(settings.object_repo_dir))
    assert [str(i) for i in issues if i.level == "error"] == []
