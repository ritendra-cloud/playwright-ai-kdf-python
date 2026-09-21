"""Owns the Playwright browser lifecycle for one scenario."""
from __future__ import annotations

import logging
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from .config import Settings
from .errors import KeywordError

log = logging.getLogger("kdf")

_ENGINES = {"chromium", "firefox", "webkit"}
_CHANNELS = {"chrome", "chrome-beta", "chrome-dev", "chrome-canary", "msedge", "msedge-beta", "msedge-dev"}


class BrowserSession:
    """Launch -> context -> page, with tracing so failures can be inspected afterwards."""

    def __init__(self, settings: Settings, choice: str | None = None):
        self.settings = settings
        self.engine, self.channel = self._resolve(choice)
        self._pw = None
        self._browser = None
        self._context = None
        self.page = None

    def _resolve(self, choice: str | None) -> tuple[str, str | None]:
        if not choice:
            return self.settings.browser, self.settings.channel
        choice = choice.strip().lower()
        if choice in _CHANNELS:
            return "chromium", choice
        if choice in _ENGINES:
            return choice, None
        raise KeywordError(
            f"Unknown browser '{choice}'. Use one of: {sorted(_ENGINES | _CHANNELS)}"
        )

    def start(self) -> "BrowserSession":
        s = self.settings
        self._pw = sync_playwright().start()
        try:
            options: dict = {"headless": s.headless, "slow_mo": s.slow_mo_ms}
            if self.channel:
                options["channel"] = self.channel
            label = f"{self.channel or self.engine} ({'headless' if s.headless else 'headed'})"
            log.info("    launching %s", label)
            try:
                self._browser = getattr(self._pw, self.engine).launch(**options)
            except PlaywrightError as exc:
                hint = (
                    f"Could not launch '{self.channel or self.engine}'. "
                    + (f"Install it with:  playwright install {self.channel}   "
                       f"or run with KDF_CHANNEL= (empty) to use Playwright's bundled Chromium."
                       if self.channel else f"Install it with:  playwright install {self.engine}")
                )
                raise KeywordError(f"{hint}\nOriginal error: {str(exc).splitlines()[0]}") from exc
            width, height = s.viewport
            self._context = self._browser.new_context(
                viewport={"width": width, "height": height},
                locale=s.locale,
                base_url=s.base_url or None,
            )
            self._context.set_default_timeout(s.timeout_ms)
            self._context.set_default_navigation_timeout(s.navigation_timeout_ms)
            self._context.tracing.start(screenshots=True, snapshots=True)
            self.page = self._context.new_page()
            return self
        except Exception:
            self.stop()
            raise

    def stop(self, trace_path: Path | None = None) -> None:
        """Close everything. Saves a Playwright trace only when trace_path is given (failures)."""
        if self._context is not None:
            try:
                if trace_path is not None:
                    trace_path.parent.mkdir(parents=True, exist_ok=True)
                    self._context.tracing.stop(path=str(trace_path))
                else:
                    self._context.tracing.stop()
            except Exception:  # noqa: BLE001 - never mask the real result
                pass
            try:
                self._context.close()
            except Exception:  # noqa: BLE001
                pass
        if self._browser is not None:
            try:
                self._browser.close()
            except Exception:  # noqa: BLE001
                pass
        if self._pw is not None:
            try:
                self._pw.stop()
            except Exception:  # noqa: BLE001
                pass
        self._pw = self._browser = self._context = self.page = None
