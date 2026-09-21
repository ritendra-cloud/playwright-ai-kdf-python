from __future__ import annotations

import re

from ..errors import KeywordError
from .registry import keyword


def _absolute(ctx, url: str) -> str:
    if re.match(r"^[a-z][a-z0-9+.-]*:", url, re.I):      # http:, https:, file:, about: ...
        return url
    if url.startswith("/"):
        if not ctx.settings.base_url:
            raise KeywordError(f"'{url}' is relative but KDF_BASE_URL is not set")
        return ctx.settings.base_url.rstrip("/") + url
    return "https://" + url                               # e.g. www.google.com


@keyword("open_browser", category="Browser", value="optional",
         doc="Launch the browser. Optional value: chrome, msedge, chromium, firefox or webkit "
             "(default comes from KDF_BROWSER / KDF_CHANNEL). Tests that skip this step get a browser automatically.",
         example=("", "chrome"))
def open_browser(ctx, target, value):
    ctx.open_browser(value or None)


@keyword("close_browser", category="Browser",
         doc="Close the browser. The framework also closes it automatically when a test ends or fails.")
def close_browser(ctx, target, value):
    ctx.close_browser()


@keyword("navigate", category="Browser", value="required", aliases=("open_url", "goto", "launch_url"),
         doc="Go to a URL (https:// optional; '/path' is joined with KDF_BASE_URL).",
         example=("", "https://www.google.com"))
def navigate(ctx, target, value):
    url = _absolute(ctx, value)
    response = ctx.page.goto(url, wait_until="domcontentloaded")
    if response is not None and response.status >= 400:      # file:// URLs have no response
        raise AssertionError(f"navigate to {url} returned HTTP {response.status} {response.status_text}")


@keyword("refresh", category="Browser", aliases=("reload",), doc="Reload the current page.")
def refresh(ctx, target, value):
    ctx.page.reload(wait_until="domcontentloaded")


@keyword("go_back", category="Browser", doc="Browser Back button.")
def go_back(ctx, target, value):
    ctx.page.go_back(wait_until="domcontentloaded")


@keyword("go_forward", category="Browser", doc="Browser Forward button.")
def go_forward(ctx, target, value):
    ctx.page.go_forward(wait_until="domcontentloaded")
