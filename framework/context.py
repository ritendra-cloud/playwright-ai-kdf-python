"""ExecutionContext: everything a keyword needs while a scenario runs."""
from __future__ import annotations

import logging
import os
import random
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from .browser import BrowserSession
from .config import Settings
from .errors import KeywordError
from .locators import resolve_locator
from .object_repository import ObjectRepository

if TYPE_CHECKING:  # pragma: no cover
    from playwright.sync_api import Locator, Page

log = logging.getLogger("kdf")
_VAR = re.compile(r"\$\{([^}]*)\}")


def safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("_") or "unnamed"


class ExecutionContext:
    def __init__(
        self,
        settings: Settings,
        repo: ObjectRepository,
        *,
        scenario_id: str = "adhoc",
        variables: dict[str, str] | None = None,
    ):
        self.settings = settings
        self.repo = repo
        self.scenario_id = scenario_id
        self.variables: dict[str, str] = dict(variables or {})
        self.session: BrowserSession | None = None
        self.last_locator: str = ""
        self._closed_explicitly = False

    # ------------------------------------------------------------------ variables
    def resolve(self, text: str) -> str:
        """Replace ${name}, ${env.NAME}, ${config.attr}, ${timestamp} ... (optional ':-default')."""
        if not text or "${" not in text:
            return text

        def replace(match: re.Match) -> str:
            expr, default = match.group(1), None
            if ":-" in expr:
                expr, default = expr.split(":-", 1)
            expr = expr.strip()
            found = self._lookup(expr)
            if found is None or found == "":
                if default is not None:
                    return default
                raise KeywordError(
                    f"Undefined variable '${{{expr}}}'. Define it with set_variable, "
                    f"export it as an environment variable (${{env.NAME}}), or give a default "
                    f"(${{{expr}:-fallback}})."
                )
            return str(found)

        return _VAR.sub(replace, text)

    def _lookup(self, name: str):
        if name.startswith("env."):
            return os.environ.get(name[4:])
        if name.startswith("config."):
            return getattr(self.settings, name[7:], None)
        builtin = {
            "timestamp": lambda: int(time.time()),
            "date": lambda: datetime.now().strftime("%Y%m%d"),
            "uuid": lambda: uuid.uuid4().hex[:8],
            "random": lambda: random.randint(100000, 999999),
        }
        if name in builtin and name not in self.variables:
            return builtin[name]()
        return self.variables.get(name)

    # ------------------------------------------------------------------ browser
    def open_browser(self, choice: str | None = None) -> None:
        if self.session is not None:
            raise KeywordError("The browser is already open; call open_browser only once per test")
        self._closed_explicitly = False
        self.session = BrowserSession(self.settings, choice).start()

    def close_browser(self, trace_path: Path | None = None) -> None:
        if self.session is not None:
            log.info("    closing browser")
            self.session.stop(trace_path)
            self.session = None
            self._closed_explicitly = True

    @property
    def page(self) -> "Page":
        if self.session is None:
            if self._closed_explicitly:
                raise KeywordError("The browser was closed earlier in this test; add open_browser first")
            log.info("    (no open_browser step yet - launching the browser automatically)")
            self.open_browser()
        assert self.session is not None and self.session.page is not None
        return self.session.page

    @property
    def page_if_open(self) -> "Page | None":
        return self.session.page if self.session is not None else None

    def locator(self, target: str) -> "Locator":
        self.last_locator = target
        return resolve_locator(self.page, target, self.repo)

    # ------------------------------------------------------------------ files
    def artifact_dir(self, *parts: str) -> Path:
        path = self.settings.reports_dir.joinpath(*parts)
        path.mkdir(parents=True, exist_ok=True)
        return path
