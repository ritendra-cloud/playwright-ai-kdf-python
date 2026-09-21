from __future__ import annotations

import logging
import re

from ..context import safe_name
from .registry import keyword

D = "Data & Utility"
log = logging.getLogger("kdf")


@keyword("set_variable", category=D, target="required", value="required",
         doc="Store a value. The 'target' column holds the variable NAME. Read it later as ${NAME}. "
             "Use ${env.NAME:-default} to allow overriding from the environment.",
         example=("SEARCH_TEXT", "${env.SEARCH_TEXT:-Playwright Python}"))
def set_variable(ctx, target, value):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", target):
        raise ValueError(f"'{target}' is not a valid variable name (letters, digits, underscore)")
    ctx.variables[target] = value


@keyword("store_text", category=D, target="required", value="required",
         doc="Save an element's text into the variable named in value.", example=("@order.number", "ORDER_ID"))
def store_text(ctx, target, value):
    ctx.variables[value] = ctx.locator(target).inner_text().strip()


@keyword("screenshot", category=D, value="optional",
         doc="Save a screenshot to reports/screenshots/<test_id>/ (value = file name, optional).",
         example=("", "google-results.png"))
def screenshot(ctx, target, value):
    folder = ctx.artifact_dir("screenshots", safe_name(ctx.scenario_id))
    name = safe_name(value) if value else f"step_{len(list(folder.iterdir())) + 1}"
    if not name.lower().endswith(".png"):
        name += ".png"
    ctx.page.screenshot(path=str(folder / name))
    log.info("    screenshot -> %s", folder / name)


@keyword("log", category=D, value="required", doc="Write a message to the test log.", example=("", "Checkpoint reached"))
def log_message(ctx, target, value):
    log.info("    LOG: %s", value)
