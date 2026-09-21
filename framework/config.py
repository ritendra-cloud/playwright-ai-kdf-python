"""Framework settings, read from environment variables (optionally via a .env file)."""
from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


def _as_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_viewport(value: str) -> tuple[int, int]:
    try:
        width, height = str(value).lower().split("x")
        return int(width), int(height)
    except ValueError as exc:
        raise ValueError(f"KDF_VIEWPORT must look like 1440x900, got {value!r}") from exc


@dataclass(frozen=True)
class Settings:
    base_url: str = ""
    browser: str = "chromium"            # chromium | firefox | webkit
    channel: str | None = "chrome"       # chrome | msedge | None (bundled Chromium)
    headless: bool = False
    slow_mo_ms: int = 0
    timeout_ms: int = 10_000
    navigation_timeout_ms: int = 30_000
    viewport: tuple[int, int] = (1440, 900)
    locale: str = "en-US"
    reports_dir: Path = ROOT / "reports"
    test_cases_dir: Path = ROOT / "test_cases"
    object_repo_dir: Path = ROOT / "object_repository"


def load_settings(**overrides) -> Settings:
    """Build Settings from KDF_* environment variables, then apply keyword overrides."""
    load_dotenv(ROOT / ".env", override=False)
    env = os.environ
    d = Settings()

    def get(name: str, default):
        return env[name] if name in env else default

    channel = get("KDF_CHANNEL", d.channel)
    settings = Settings(
        base_url=str(get("KDF_BASE_URL", d.base_url)).strip(),
        browser=str(get("KDF_BROWSER", d.browser)).strip().lower(),
        channel=(str(channel).strip() or None) if channel is not None else None,
        headless=_as_bool(get("KDF_HEADLESS", d.headless)),
        slow_mo_ms=int(get("KDF_SLOW_MO_MS", d.slow_mo_ms)),
        timeout_ms=int(get("KDF_TIMEOUT_MS", d.timeout_ms)),
        navigation_timeout_ms=int(get("KDF_NAVIGATION_TIMEOUT_MS", d.navigation_timeout_ms)),
        viewport=_parse_viewport(get("KDF_VIEWPORT", "%dx%d" % d.viewport)),
        locale=str(get("KDF_LOCALE", d.locale)),
        reports_dir=Path(get("KDF_REPORTS_DIR", d.reports_dir)),
        test_cases_dir=Path(get("KDF_TEST_CASES_DIR", d.test_cases_dir)),
        object_repo_dir=Path(get("KDF_OBJECT_REPO_DIR", d.object_repo_dir)),
    )
    return replace(settings, **overrides) if overrides else settings
