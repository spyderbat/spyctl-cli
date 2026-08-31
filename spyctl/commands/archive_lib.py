"""Shared helpers for the agent-archives list and download commands."""

from typing import Optional, Tuple

import spyctl.api.sources as src_api
import spyctl.filter_resource as filt
from spyctl import cli
from spyctl.commands.get import get_lib
from spyctl.config.configs import Context

MAX_WINDOW_SECS = 86400  # the archive API caps a listing window at 24 hours


def resolve_window(st: float, et: Optional[float]) -> Tuple[int, int]:
    """Normalize a ``-t``/``-e`` selection into a ``[start, end]`` query window.

    ``st`` (required) is epoch seconds; ``et`` is epoch seconds or ``None``.

    - ``et is None`` → a single instant: return ``[st, st + 1]``. The API
      requires ``end > start``, and the server's overlap match against that
      one-second window returns the archive whose own ``[start, end]`` covers
      the instant.
    - ``et`` given → an explicit range, validated as ``end > start`` and
      ``<= 24h``.
    """
    start = int(st)
    if et is None:
        return start, start + 1
    end = int(et)
    if end < start:
        cli.err_exit("end time must be after start time")
    if end == start:
        end = start + 1
    if end - start > MAX_WINDOW_SECS:
        cli.err_exit(
            "time window must not exceed 24 hours; "
            "narrow -t/--start-time and -e/--end-time"
        )
    return start, end


def resolve_single_source(ctx: Context, source: str, exact: bool) -> str:
    """Resolve a SOURCE selector to exactly one source UID.

    Matches the resolution `get sources` uses — `get_sources` + `filter_obj`
    over name and uid, with wildcard (substring) matching unless ``exact``.
    Expired sources are included so archives from an offline machine still
    resolve. Errors (and lists candidates) when the selector is ambiguous or
    matches nothing.
    """
    sources = src_api.get_sources(*ctx.get_api_data(), include_expired=True)
    term = get_lib.wildcard_name_or_id(source, exact)
    matches = filt.filter_obj(sources, ["name", "uid"], term)
    if not matches:
        cli.err_exit(f"No source matches '{source}'.")
    if len(matches) > 1:
        candidates = "\n".join(
            f"  {s.get('uid', '')}  {s.get('name', '') or ''}" for s in matches[:25]
        )
        cli.err_exit(
            f"'{source}' matches {len(matches)} sources — narrow it or use"
            f" -E/--exact:\n{candidates}"
        )
    return matches[0]["uid"]
