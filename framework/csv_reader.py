"""Reads keyword-driven test cases from CSV files.

Columns (header row required, order free, case-insensitive):

    test_id, test_name, tags, keyword, target, value, description

* ``keyword`` is the only mandatory column.
* ``test_id`` starts a new test; leave it blank to continue the previous test.
* ``test_name`` and ``tags`` are read from the first row of each test.
* Rows whose first non-empty cell starts with ``#`` are comments.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

from .errors import CsvFormatError

COLUMNS = ("test_id", "test_name", "tags", "keyword", "target", "value", "description")


@dataclass(frozen=True)
class Step:
    keyword: str
    target: str
    value: str
    description: str
    line: int          # physical line in the CSV file (for error messages)


@dataclass
class Scenario:
    id: str
    name: str
    tags: tuple[str, ...]
    source: Path
    steps: list[Step] = field(default_factory=list)


def _read_rows(path: Path, allowed: tuple[str, ...], required: tuple[str, ...]):
    """Yield (line_number, {column: stripped value}) for every non-blank data row."""
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise CsvFormatError(f"{path}: file is empty (a header row is required)")
        headers = [h.strip().lower() for h in reader.fieldnames]
        unknown = [h for h in headers if h not in allowed]
        if unknown:
            raise CsvFormatError(
                f"{path}: unknown column(s) {unknown}. Allowed columns: {list(allowed)}"
            )
        missing = [c for c in required if c not in headers]
        if missing:
            raise CsvFormatError(f"{path}: missing required column(s) {missing}")
        reader.fieldnames = headers
        for row in reader:
            line = reader.line_num
            if None in row:  # more cells than headers
                raise CsvFormatError(
                    f"{path}:{line}: too many columns. Wrap any cell that contains a comma in "
                    f'double quotes (and double any quote inside it, e.g. "role=button[name=""Save""]").'
                )
            cells = {k: (v or "").strip() for k, v in row.items()}
            if not any(cells.values()):
                continue
            yield line, cells


def read_scenarios(path: Path | str) -> list[Scenario]:
    """Parse one CSV file into scenarios (one per test_id), preserving order."""
    path = Path(path)
    scenarios: list[Scenario] = []
    seen: set[str] = set()
    current: Scenario | None = None

    for line, cells in _read_rows(path, COLUMNS, required=("keyword",)):
        first = next((v for v in cells.values() if v), "")
        if first.startswith("#"):
            continue
        test_id = cells.get("test_id", "")
        if test_id:
            if current is None or test_id != current.id:
                if test_id in seen:
                    raise CsvFormatError(
                        f"{path}:{line}: test_id '{test_id}' appears in non-adjacent rows; "
                        "keep all steps of a test together"
                    )
                seen.add(test_id)
                tags = tuple(t for t in re.split(r"[;\s]+", cells.get("tags", "")) if t)
                current = Scenario(test_id, cells.get("test_name") or test_id, tags, path)
                scenarios.append(current)
        elif current is None:
            raise CsvFormatError(f"{path}:{line}: the first row must have a test_id")

        keyword = cells.get("keyword", "")
        if not keyword:
            raise CsvFormatError(f"{path}:{line}: 'keyword' is empty")
        current.steps.append(
            Step(
                keyword=keyword,
                target=cells.get("target", ""),
                value=cells.get("value", ""),
                description=cells.get("description", ""),
                line=line,
            )
        )
    return scenarios


def read_object_repository_rows(path: Path):
    """Yield (line, name, locator, description) rows from an object-repository CSV."""
    for line, cells in _read_rows(path, ("name", "locator", "description"), ("name", "locator")):
        if cells["name"].startswith("#"):
            continue
        yield line, cells["name"], cells["locator"], cells.get("description", "")
