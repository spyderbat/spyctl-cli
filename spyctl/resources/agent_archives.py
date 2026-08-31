"""Output formatting for raw agent archive zips."""

from datetime import datetime, timezone
from typing import Dict, List

from tabulate import tabulate

ARCHIVE_HEADERS = ["SOURCE_UID", "NAME", "START", "END", "SIZE"]


def archive_summary_output(archives: List[Dict]) -> str:
    """Render a plain table of archive zips, oldest first."""
    data = [archive_summary_data(a) for a in archives]
    data.sort(key=lambda line: (line[2], line[0]))
    rows = [
        [src, name, fmt_time(start), fmt_time(end), fmt_size(size)]
        for src, name, start, end, size in data
    ]
    return tabulate(rows, ARCHIVE_HEADERS, tablefmt="plain")


def archive_summary_data(archive: Dict) -> List:
    """Extract the sortable summary row for a single archive."""
    return [
        archive.get("source_uid", ""),
        archive.get("name", ""),
        archive.get("start_time", 0),
        archive.get("end_time", 0),
        archive.get("size", 0),
    ]


def fmt_time(epoch: int) -> str:
    """Render an epoch-seconds value as a UTC timestamp."""
    if not epoch:
        return "-"
    return datetime.fromtimestamp(int(epoch), tz=timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def fmt_size(num: int) -> str:
    """Human-readable byte size (1.5 MiB, 920 KiB, ...)."""
    size = float(num or 0)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024 or unit == "TiB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TiB"
