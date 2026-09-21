"""Keyword registry.

Adding a keyword = writing one decorated function:

    @keyword("click", category="Interaction", target="required",
             doc="Click an element.", example=("@login.submit", ""))
    def click(ctx, target, value):
        ctx.locator(target).click()

Every ``validate*`` keyword automatically gets a ``verify*`` alias.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Literal

Req = Literal["none", "optional", "required"]

CATEGORY_ORDER = ("Browser", "Interaction", "Validation", "Data & Utility")


@dataclass(frozen=True)
class KeywordSpec:
    name: str
    func: Callable
    category: str
    target: Req
    value: Req
    doc: str
    example: tuple[str, str]
    aliases: tuple[str, ...]
    sensitive: bool = False     # mask the value in logs and reports


_REGISTRY: dict[str, KeywordSpec] = {}
_ALIASES: dict[str, str] = {}


def normalize(name: str) -> str:
    """'Validate Visible', 'validate-visible' and 'VALIDATE_VISIBLE' are all the same keyword."""
    return re.sub(r"[\s\-]+", "_", name.strip().lower())


def keyword(
    name: str,
    *,
    category: str,
    doc: str,
    target: Req = "none",
    value: Req = "none",
    example: tuple[str, str] = ("", ""),
    aliases: tuple[str, ...] = (),
    sensitive: bool = False,
):
    def decorator(func: Callable) -> Callable:
        canonical = normalize(name)
        all_aliases = [normalize(a) for a in aliases]
        if canonical.startswith("validate"):
            all_aliases.append("verify" + canonical[len("validate"):])
        if canonical in _REGISTRY or canonical in _ALIASES:
            raise ValueError(f"Keyword '{canonical}' is registered twice")
        _REGISTRY[canonical] = KeywordSpec(
            canonical, func, category, target, value, doc, example, tuple(all_aliases), sensitive
        )
        for alias in all_aliases:
            if alias in _REGISTRY or alias in _ALIASES:
                raise ValueError(f"Alias '{alias}' clashes with an existing keyword")
            _ALIASES[alias] = canonical
        return func

    return decorator


def get_keyword(name: str) -> KeywordSpec | None:
    key = normalize(name)
    return _REGISTRY.get(_ALIASES.get(key, key))


def all_keywords() -> list[KeywordSpec]:
    order = {c: i for i, c in enumerate(CATEGORY_ORDER)}
    return sorted(_REGISTRY.values(), key=lambda k: (order.get(k.category, 99), k.name))


def check_arguments(spec: KeywordSpec, target: str, value: str) -> str | None:
    """Return a problem description, or None when the row supplies what the keyword needs."""
    if spec.target == "required" and not target:
        return f"'{spec.name}' needs a value in the 'target' column"
    if spec.value == "required" and not value:
        return f"'{spec.name}' needs a value in the 'value' column"
    if spec.target == "none" and target:
        return f"'{spec.name}' does not use the 'target' column (got '{target}')"
    if spec.value == "none" and value:
        return f"'{spec.name}' does not use the 'value' column (got '{value}')"
    return None
