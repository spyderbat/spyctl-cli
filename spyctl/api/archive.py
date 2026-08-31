"""API calls for raw agent archive zips (list + download).

Wraps the ``source_data:Query``-gated endpoints added in backend #2114/#2116:

    GET /api/v1/org/{org}/archive/                    -> list zips for sources
    GET /api/v1/org/{org}/archive/{sourceUID}/{name}  -> stream one zip

The archiver keys these zips by *source UID* (a machine UID is only one kind of
source), so this module uses ``source_uid`` throughout to match the server.
"""

from typing import IO, Dict, List
from urllib.parse import quote

from spyctl.api.primitives import get

# Streaming chunk size for archive downloads. Archive zips can be large, so the
# download path streams to disk rather than buffering the whole body in memory
# (unlike the report download, whose payloads are small).
_DOWNLOAD_CHUNK = 1 << 20  # 1 MiB


def list_agent_archives(
    api_url: str,
    api_key: str,
    org_uid: str,
    source_uids: List[str],
    start_time: int,
    end_time: int,
    limit: int = 1000,
) -> List[Dict]:
    """List every archive zip for ``source_uids`` overlapping the time window.

    The server filters by overlap (an archive is returned when its own
    [start, end] intersects [start_time, end_time]) and pages large results via
    an opaque ``continuation_token``. This walks every page and returns the
    flattened list of archive objects, each shaped::

        {"source_uid": str, "name": str,
         "start_time": int, "end_time": int, "size": int}

    Args:
        api_url: Base URL of the Spyderbat API.
        api_key: Bearer token for authentication.
        org_uid: Organization that owns the archives.
        source_uids: One or more source UIDs (1-100) to list archives for.
        start_time: Inclusive lower bound of the window, in Unix seconds.
        end_time: Inclusive upper bound of the window, in Unix seconds.
        limit: Page size requested from the server (1-50000).

    Returns:
        The archive objects matching the query, across all pages.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/archive/"
    results: List[Dict] = []
    continuation_token = ""
    while True:
        params = {
            "source_uid": source_uids,
            "start_time": int(start_time),
            "end_time": int(end_time),
            "limit": limit,
        }
        if continuation_token:
            params["continuation_token"] = continuation_token
        body = get(url, api_key, params=params).json()
        results.extend(body.get("results", []))
        continuation_token = body.get("continuation_token") or ""
        if not continuation_token:
            break
    return results


def download_agent_archive(
    api_url: str,
    api_key: str,
    org_uid: str,
    source_uid: str,
    name: str,
    dest: IO[bytes],
) -> int:
    """Stream a single archive zip into ``dest``.

    The ``name`` is the opaque identifier returned by
    :func:`list_agent_archives`; the server reconstructs the storage key from
    ``(org, source_uid, name)`` and scopes it to the caller's org, so a name
    from another org 404s rather than leaking data.

    Args:
        api_url: Base URL of the Spyderbat API.
        api_key: Bearer token for authentication.
        org_uid: Organization that owns the archive.
        source_uid: Source UID the archive belongs to.
        name: Opaque archive identifier from the list endpoint.
        dest: Binary file-like object the zip is written to.

    Returns:
        The number of bytes written.
    """
    url = (
        f"{api_url}/api/v1/org/{org_uid}/archive/"
        f"{quote(source_uid, safe='')}/{quote(name, safe='')}"
    )
    resp = get(url, api_key)
    written = 0
    for chunk in resp.iter_content(chunk_size=_DOWNLOAD_CHUNK):
        if chunk:
            dest.write(chunk)
            written += len(chunk)
    return written
