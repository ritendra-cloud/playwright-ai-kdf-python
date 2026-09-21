"""Object repository: logical element names -> locator strings, stored in CSV.

Tests refer to elements as ``@name`` (e.g. ``@google.search_box``). When the UI
changes, fix the locator once here and every test using the name is healed.
"""
from __future__ import annotations

import difflib
from pathlib import Path

from .csv_reader import read_object_repository_rows
from .errors import CsvFormatError, KeywordError


class ObjectRepository:
    def __init__(self, entries: dict[str, str] | None = None):
        self._entries: dict[str, str] = dict(entries or {})

    @classmethod
    def load(cls, directory: Path | str) -> "ObjectRepository":
        directory = Path(directory)
        entries: dict[str, str] = {}
        origin: dict[str, str] = {}
        if directory.is_dir():
            for path in sorted(directory.rglob("*.csv")):
                for line, name, locator, _desc in read_object_repository_rows(path):
                    if name in entries:
                        raise CsvFormatError(
                            f"{path}:{line}: duplicate element name '{name}' (first defined in {origin[name]})"
                        )
                    entries[name] = locator
                    origin[name] = f"{path.name}:{line}"
        return cls(entries)

    def __contains__(self, name: str) -> bool:
        return name in self._entries

    def names(self) -> list[str]:
        return sorted(self._entries)

    def get(self, name: str) -> str:
        try:
            return self._entries[name]
        except KeyError:
            hint = difflib.get_close_matches(name, self._entries, n=3)
            extra = f" Did you mean: {', '.join('@' + h for h in hint)}?" if hint else ""
            raise KeywordError(f"Unknown element '@{name}' (not in the object repository).{extra}") from None
