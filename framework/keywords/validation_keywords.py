"""Validation keywords. Each one waits (auto-retry) up to KDF_TIMEOUT_MS before failing."""
from __future__ import annotations

import re
import time

from playwright.sync_api import expect

from ..errors import KeywordError
from .registry import keyword

V = "Validation"


def _to_int(value: str, keyword_name: str) -> int:
    try:
        return int(value)
    except ValueError:
        raise KeywordError(f"{keyword_name} expects a whole number in 'value', got '{value}'") from None


@keyword("validate", category=V, target="required", value="optional",
         doc="The element is visible. If value is given, its text must also contain it (case-sensitive).",
         example=("@google.results_container", ""))
def validate(ctx, target, value):
    loc = ctx.locator(target)
    expect(loc).to_be_visible(timeout=ctx.settings.timeout_ms)
    if value:
        expect(loc).to_contain_text(value, timeout=ctx.settings.timeout_ms)


@keyword("validate_visible", category=V, target="required", doc="The element is visible.",
         example=("@google.search_box", ""))
def validate_visible(ctx, target, value):
    expect(ctx.locator(target)).to_be_visible(timeout=ctx.settings.timeout_ms)


@keyword("validate_hidden", category=V, target="required",
         doc="The element is not visible (or not in the page at all).", example=("@login.error", ""))
def validate_hidden(ctx, target, value):
    expect(ctx.locator(target)).to_be_hidden(timeout=ctx.settings.timeout_ms)


@keyword("validate_text", category=V, target="required", value="required",
         doc="The element's text equals value (whitespace-normalised).", example=("role=heading", "Welcome"))
def validate_text(ctx, target, value):
    expect(ctx.locator(target)).to_have_text(value, timeout=ctx.settings.timeout_ms)


@keyword("validate_contains", category=V, target="required", value="required",
         doc="The element's text contains value (case-sensitive).", example=("@results", "Playwright"))
def validate_contains(ctx, target, value):
    expect(ctx.locator(target)).to_contain_text(value, timeout=ctx.settings.timeout_ms)


@keyword("validate_contains_ignore_case", category=V, target="required", value="required",
         doc="The element's text contains value, ignoring upper/lower case.",
         example=("@google.results_container", "playwright"))
def validate_contains_ignore_case(ctx, target, value):
    expect(ctx.locator(target)).to_contain_text(value, ignore_case=True, timeout=ctx.settings.timeout_ms)


@keyword("validate_page_contains", category=V, value="required",
         doc="The text is visible somewhere on the page (case-insensitive).", example=("", "Welcome back"))
def validate_page_contains(ctx, target, value):
    expect(ctx.page.get_by_text(value).first).to_be_visible(timeout=ctx.settings.timeout_ms)


@keyword("validate_value", category=V, target="required", value="required",
         doc="An input's current value equals value.", example=("label=Search", "playwright"))
def validate_value(ctx, target, value):
    expect(ctx.locator(target)).to_have_value(value, timeout=ctx.settings.timeout_ms)


@keyword("validate_attribute", category=V, target="required", value="required",
         doc="An attribute has a value. Write value as name=expected.", example=("role=link[name=Docs]", "href=/docs"))
def validate_attribute(ctx, target, value):
    name, sep, expected = value.partition("=")
    if not sep:
        raise KeywordError("validate_attribute expects value like  href=/docs")
    expect(ctx.locator(target)).to_have_attribute(name.strip(), expected, timeout=ctx.settings.timeout_ms)


@keyword("validate_enabled", category=V, target="required", doc="The element is enabled.",
         example=("role=button[name=Save]", ""))
def validate_enabled(ctx, target, value):
    expect(ctx.locator(target)).to_be_enabled(timeout=ctx.settings.timeout_ms)


@keyword("validate_disabled", category=V, target="required", doc="The element is disabled.",
         example=("role=button[name=Save]", ""))
def validate_disabled(ctx, target, value):
    expect(ctx.locator(target)).to_be_disabled(timeout=ctx.settings.timeout_ms)


@keyword("validate_checked", category=V, target="required", doc="A checkbox / radio is ticked.",
         example=("label=Remember me", ""))
def validate_checked(ctx, target, value):
    expect(ctx.locator(target)).to_be_checked(timeout=ctx.settings.timeout_ms)


@keyword("validate_count", category=V, target="required", value="required",
         doc="Exactly N elements match.", example=("css=table tbody tr", "5"))
def validate_count(ctx, target, value):
    expect(ctx.locator(target)).to_have_count(_to_int(value, "validate_count"), timeout=ctx.settings.timeout_ms)


@keyword("validate_count_at_least", category=V, target="required", value="required",
         doc="At least N elements match (waits until that many exist).",
         example=("@google.result_titles", "3"))
def validate_count_at_least(ctx, target, value):
    minimum = _to_int(value, "validate_count_at_least")
    loc = ctx.locator(target)
    deadline = time.monotonic() + ctx.settings.timeout_ms / 1000
    found = loc.count()
    while found < minimum and time.monotonic() < deadline:
        time.sleep(0.1)
        found = loc.count()
    if found < minimum:
        raise AssertionError(f"Expected at least {minimum} element(s) matching '{target}', found {found}")


@keyword("validate_title", category=V, value="required", doc="The page title equals value.",
         example=("", "Dashboard"))
def validate_title(ctx, target, value):
    expect(ctx.page).to_have_title(value, timeout=ctx.settings.timeout_ms)


@keyword("validate_title_contains", category=V, value="required",
         doc="The page title contains value (case-insensitive).", example=("", "Google Search"))
def validate_title_contains(ctx, target, value):
    expect(ctx.page).to_have_title(re.compile(re.escape(value), re.I), timeout=ctx.settings.timeout_ms)


@keyword("validate_url", category=V, value="required", doc="The full URL equals value.",
         example=("", "https://example.com/board"))
def validate_url(ctx, target, value):
    expect(ctx.page).to_have_url(value, timeout=ctx.settings.timeout_ms)


@keyword("validate_url_contains", category=V, value="required",
         doc="The URL contains value (case-insensitive).", example=("", "/search"))
def validate_url_contains(ctx, target, value):
    expect(ctx.page).to_have_url(re.compile(re.escape(value), re.I), timeout=ctx.settings.timeout_ms)
