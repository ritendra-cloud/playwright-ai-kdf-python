from __future__ import annotations

import time

from playwright.sync_api import TimeoutError as PlaywrightTimeout

from ..errors import KeywordError
from .registry import keyword

C = "Interaction"


@keyword("click", category=C, target="required", aliases=("tap",),
         doc="Click an element.", example=("role=button[name=Login]", ""))
def click(ctx, target, value):
    ctx.locator(target).click()


@keyword("double_click", category=C, target="required", doc="Double-click an element.",
         example=("text=Row 1", ""))
def double_click(ctx, target, value):
    ctx.locator(target).dblclick()


@keyword("right_click", category=C, target="required", doc="Right-click an element.",
         example=("text=Row 1", ""))
def right_click(ctx, target, value):
    ctx.locator(target).click(button="right")


@keyword("hover", category=C, target="required", doc="Move the mouse over an element.",
         example=("text=Menu", ""))
def hover(ctx, target, value):
    ctx.locator(target).hover()


@keyword("click_if_visible", category=C, target="required", value="optional",
         doc="Click only if the element shows up (default wait 3 s, or the number of seconds in value). "
             "Never fails - use it for cookie banners and consent pop-ups.",
         example=("@google.consent_accept_all", "3"))
def click_if_visible(ctx, target, value):
    seconds = float(value) if value else 3.0
    element = ctx.locator(target).first
    try:
        element.wait_for(state="visible", timeout=seconds * 1000)
        element.click(timeout=seconds * 1000)
    except PlaywrightTimeout:
        return


@keyword("enter", category=C, target="required", value="optional",
         aliases=("fill", "input_text", "type_text"),
         doc="Put text into an input (replaces existing text; empty value clears the field).",
         example=("label=Username", "alice"))
def enter(ctx, target, value):
    ctx.locator(target).fill(value)


@keyword("enter_secret", category=C, target="required", value="required", sensitive=True,
         doc="Like enter, but the value is masked in logs and reports. Prefer ${env.PASSWORD}.",
         example=("label=Password", "${env.APP_PASSWORD}"))
def enter_secret(ctx, target, value):
    ctx.locator(target).fill(value)


@keyword("type_slowly", category=C, target="required", value="required",
         doc="Type key by key (50 ms apart) - for widgets that react to individual key presses.",
         example=("@search.box", "playwright"))
def type_slowly(ctx, target, value):
    ctx.locator(target).press_sequentially(value, delay=50)


@keyword("clear", category=C, target="required", doc="Empty an input field.", example=("label=Search", ""))
def clear(ctx, target, value):
    ctx.locator(target).clear()


@keyword("press_key", category=C, target="optional", value="required",
         doc="Press a key or chord (Enter, Tab, Escape, Control+A ...). With a target the element is focused "
             "first; without one the key goes to the page.",
         example=("@google.search_box", "Enter"))
def press_key(ctx, target, value):
    if target:
        ctx.locator(target).press(value)
    else:
        ctx.page.keyboard.press(value)


@keyword("select", category=C, target="required", value="required", aliases=("select_option",),
         doc="Choose an option of a <select> by its label or value.", example=("label=Country", "India"))
def select(ctx, target, value):
    ctx.locator(target).select_option(value)


@keyword("check", category=C, target="required", doc="Tick a checkbox / radio button.",
         example=("label=Remember me", ""))
def check(ctx, target, value):
    ctx.locator(target).check()


@keyword("uncheck", category=C, target="required", doc="Untick a checkbox.", example=("label=Remember me", ""))
def uncheck(ctx, target, value):
    ctx.locator(target).uncheck()


@keyword("scroll_to", category=C, target="required", doc="Scroll an element into view.",
         example=("text=Footer", ""))
def scroll_to(ctx, target, value):
    ctx.locator(target).scroll_into_view_if_needed()


@keyword("upload_file", category=C, target="required", value="required",
         doc="Attach a file to an <input type=file>.", example=("label=Resume", "data/cv.pdf"))
def upload_file(ctx, target, value):
    ctx.locator(target).set_input_files(value)


@keyword("wait_for", category=C, target="required", aliases=("wait_for_visible",),
         doc="Wait until an element is visible (prefer this over wait).", example=("@google.results_container", ""))
def wait_for(ctx, target, value):
    ctx.locator(target).first.wait_for(state="visible")


@keyword("wait_for_url", category=C, value="required",
         doc="Wait until the URL matches a glob (e.g. **/board).", example=("", "**/board"))
def wait_for_url(ctx, target, value):
    ctx.page.wait_for_url(value)


@keyword("wait", category=C, value="required",
         doc="Hard pause for N seconds. Last resort - flaky and slow; use wait_for or validate instead.",
         example=("", "2"))
def wait(ctx, target, value):
    try:
        time.sleep(float(value))
    except ValueError:
        raise KeywordError(f"wait expects a number of seconds, got '{value}'") from None
