"""Turns a CSV ``target`` string into a Playwright Locator.

Supported forms
---------------
    @google.search_box                 element from the object repository
    role=button[name="Search"]         get_by_role  (quotes optional, add ,exact=true)
    label=Email  placeholder=Search    get_by_label / get_by_placeholder
    text=Sign in  alt=Logo  title=Help get_by_text / get_by_alt_text / get_by_title
    testid=submit                      get_by_test_id
    css=#search a h3   xpath=//h1      CSS / XPath
    #search                            anything else is passed to page.locator() as-is
Any form may end with ``>> first``, ``>> last`` or ``>> nth=2``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .errors import KeywordError

if TYPE_CHECKING:  # pragma: no cover
    from playwright.sync_api import Locator, Page

    from .object_repository import ObjectRepository

_PREFIX = re.compile(r"^(role|label|placeholder|text|testid|alt|title|css|xpath)\s*=\s*(.*)$", re.I | re.S)
_CHAIN = re.compile(r"^(?P<base>.*?)\s*>>\s*(?P<op>first|last|nth\s*=\s*-?\d+)\s*$", re.I | re.S)
_ROLE = re.compile(r"^(?P<role>[A-Za-z_-]+)\s*(?:\[(?P<attrs>.*)\])?\s*$", re.S)
_NAME = re.compile(r"""name\s*=\s*(?:"(?P<dq>[^"]*)"|'(?P<sq>[^']*)'|(?P<bare>[^,\]]+))""", re.I)
_EXACT = re.compile(r"exact\s*=\s*(true|false)", re.I)


@dataclass(frozen=True)
class LocatorSpec:
    kind: str                 # role|label|placeholder|text|testid|alt|title|css|xpath|raw
    value: str
    name: str | None = None   # accessible name (role only)
    exact: bool = False
    nth: str | None = None    # "first" | "last" | "nth=N"
    source: str = ""          # original text, for messages


def parse_locator(target: str, repo: "ObjectRepository | None" = None) -> LocatorSpec:
    """Parse a target string. Pure function (no browser needed) so it is unit-testable."""
    original = target.strip()
    if not original:
        raise KeywordError("This keyword needs a locator in the 'target' column")
    raw = original
    if raw.startswith("@"):
        if repo is None:
            raise KeywordError(f"Cannot resolve '{raw}': no object repository loaded")
        raw = repo.get(raw[1:].strip()).strip()

    nth = None
    chain = _CHAIN.match(raw)
    if chain:
        raw, nth = chain["base"].strip(), re.sub(r"\s+", "", chain["op"].lower())

    prefix = _PREFIX.match(raw)
    if not prefix:
        return LocatorSpec("raw", raw, nth=nth, source=original)

    kind, value = prefix.group(1).lower(), prefix.group(2).strip()
    if kind != "role":
        return LocatorSpec(kind, value, nth=nth, source=original)

    role = _ROLE.match(value)
    if not role:
        raise KeywordError(f"Bad role locator '{original}'. Use role=button[name=\"Save\"]")
    name, exact = None, False
    attrs = role["attrs"] or ""
    if attrs:
        m = _NAME.search(attrs)
        if m:
            name = (m["dq"] if m["dq"] is not None else m["sq"] if m["sq"] is not None else m["bare"]).strip()
        e = _EXACT.search(attrs)
        exact = bool(e and e.group(1).lower() == "true")
    return LocatorSpec("role", role["role"].lower(), name=name, exact=exact, nth=nth, source=original)


def build_locator(page: "Page", spec: LocatorSpec) -> "Locator":
    if spec.kind == "role":
        kwargs = {}
        if spec.name is not None:
            kwargs["name"] = spec.name
            kwargs["exact"] = spec.exact
        loc = page.get_by_role(spec.value, **kwargs)  # type: ignore[arg-type]
    elif spec.kind == "label":
        loc = page.get_by_label(spec.value)
    elif spec.kind == "placeholder":
        loc = page.get_by_placeholder(spec.value)
    elif spec.kind == "text":
        loc = page.get_by_text(spec.value)
    elif spec.kind == "testid":
        loc = page.get_by_test_id(spec.value)
    elif spec.kind == "alt":
        loc = page.get_by_alt_text(spec.value)
    elif spec.kind == "title":
        loc = page.get_by_title(spec.value)
    elif spec.kind in ("css", "xpath"):
        loc = page.locator(f"{spec.kind}={spec.value}")
    else:
        loc = page.locator(spec.value)

    if spec.nth == "first":
        loc = loc.first
    elif spec.nth == "last":
        loc = loc.last
    elif spec.nth:
        loc = loc.nth(int(spec.nth.split("=")[1]))
    return loc


def resolve_locator(page: "Page", target: str, repo: "ObjectRepository | None" = None) -> "Locator":
    return build_locator(page, parse_locator(target, repo))
