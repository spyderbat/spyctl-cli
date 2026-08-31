# pylint: disable=missing-function-docstring,redefined-outer-name
"""Unit tests for the agent-archives list/download feature.

Covers the pure logic (window resolution, source resolution, formatters), the
paginated list API client, and the `agent-archives list`/`download` command
wiring — all without touching the network.
"""

from types import SimpleNamespace
from unittest import mock

import pytest
from click.testing import CliRunner

import spyctl.api.archive as archive_api
import spyctl.commands.agent_archives as cmd
import spyctl.commands.archive_lib as archive_lib
import spyctl.resources.agent_archives as archive_res
from spyctl.spyctl import main

API_DATA = ("https://api.test", "key", "org123")


def _archive(name, src="mach:a", start=1000, end=2000, size=1024):
    return {
        "source_uid": src,
        "name": name,
        "start_time": start,
        "end_time": end,
        "size": size,
    }


def _source(uid, name):
    return {"uid": uid, "name": name}


# --------------------------------------------------------------------------- #
#                          Window resolution                                  #
# --------------------------------------------------------------------------- #


def test_window_single_instant_widens_to_one_second():
    # -e omitted: a point becomes [T, T+1] so the server's overlap match
    # returns the archive covering T. (ADR-0002)
    assert archive_lib.resolve_window(1500, None) == (1500, 1501)


def test_window_explicit_range():
    assert archive_lib.resolve_window(1000, 2000) == (1000, 2000)


def test_window_equal_bounds_widen():
    assert archive_lib.resolve_window(1500, 1500) == (1500, 1501)


def test_window_end_before_start_errors():
    with pytest.raises(SystemExit):
        archive_lib.resolve_window(2000, 1000)


def test_window_over_24h_errors():
    with pytest.raises(SystemExit):
        archive_lib.resolve_window(0, archive_lib.MAX_WINDOW_SECS + 1)


def test_window_exactly_24h_ok():
    assert archive_lib.resolve_window(0, archive_lib.MAX_WINDOW_SECS) == (
        0,
        archive_lib.MAX_WINDOW_SECS,
    )


def test_window_truncates_float_end():
    assert archive_lib.resolve_window(1000, 2000.9) == (1000, 2000)


# --------------------------------------------------------------------------- #
#                          Source resolution                                  #
# --------------------------------------------------------------------------- #


@pytest.fixture
def ctx():
    return SimpleNamespace(get_api_data=lambda: API_DATA)


def test_resolve_source_unique_match_returns_uid(ctx):
    sources = [_source("mach:abc", "db-backup-01"), _source("mach:xyz", "web-01")]
    with mock.patch.object(archive_lib.src_api, "get_sources", return_value=sources):
        assert archive_lib.resolve_single_source(ctx, "db-backup", False) == "mach:abc"


def test_resolve_source_by_uid(ctx):
    sources = [_source("mach:abc", "db-backup-01")]
    with mock.patch.object(archive_lib.src_api, "get_sources", return_value=sources):
        assert archive_lib.resolve_single_source(ctx, "mach:abc", True) == "mach:abc"


def test_resolve_source_no_match_errors(ctx):
    with mock.patch.object(archive_lib.src_api, "get_sources", return_value=[]):
        with pytest.raises(SystemExit):
            archive_lib.resolve_single_source(ctx, "nope", False)


def test_resolve_source_ambiguous_errors(ctx):
    sources = [_source("mach:a", "db-01"), _source("mach:b", "db-02")]
    with mock.patch.object(archive_lib.src_api, "get_sources", return_value=sources):
        with pytest.raises(SystemExit):
            archive_lib.resolve_single_source(ctx, "db", False)


# --------------------------------------------------------------------------- #
#                          Formatters                                         #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "num,expected",
    [
        (0, "0 B"),
        (512, "512 B"),
        (1024, "1.0 KiB"),
        (1536, "1.5 KiB"),
        (1048576, "1.0 MiB"),
    ],
)
def test_fmt_size(num, expected):
    assert archive_res.fmt_size(num) == expected


def test_fmt_time_zero_is_dash():
    assert archive_res.fmt_time(0) == "-"


def test_fmt_time_renders_utc():
    assert archive_res.fmt_time(1715002801) == "2024-05-06 13:40:01"


def test_summary_output_sorts_and_has_headers():
    out = archive_res.archive_summary_output(
        [_archive("z", start=3000), _archive("a", start=1000)]
    )
    lines = out.splitlines()
    assert "SOURCE_UID" in lines[0] and "SIZE" in lines[0]
    assert lines[1].split()[1] == "a"
    assert lines[2].split()[1] == "z"


# --------------------------------------------------------------------------- #
#                          List API pagination                                #
# --------------------------------------------------------------------------- #


def test_list_agent_archives_walks_all_pages():
    pages = [
        {"results": [_archive("p1")], "continuation_token": "tok"},
        {"results": [_archive("p2")], "continuation_token": ""},
    ]
    captured = []

    def fake_get(url, key, params=None):
        captured.append(params)
        return SimpleNamespace(json=lambda: pages[len(captured) - 1])

    with mock.patch.object(archive_api, "get", side_effect=fake_get):
        results = archive_api.list_agent_archives(*API_DATA, ["mach:a"], 1000, 2000)

    assert [r["name"] for r in results] == ["p1", "p2"]
    assert captured[0].get("continuation_token") is None
    assert captured[1]["continuation_token"] == "tok"
    assert captured[1]["source_uid"] == ["mach:a"]


def test_download_streams_chunks_to_dest():
    resp = SimpleNamespace(iter_content=lambda chunk_size: [b"ab", b"", b"cde"])
    sink = bytearray()

    class Dest:
        def write(self, b):
            sink.extend(b)

    with mock.patch.object(archive_api, "get", return_value=resp):
        written = archive_api.download_agent_archive(
            *API_DATA, "mach:a", "n.zip", Dest()
        )
    assert bytes(sink) == b"abcde"
    assert written == 5


# --------------------------------------------------------------------------- #
#                          CLI wiring                                          #
# --------------------------------------------------------------------------- #


@pytest.fixture
def wired():
    """Patch context + source resolution so commands reach the archive API."""
    ctx = SimpleNamespace(get_api_data=lambda: API_DATA)
    with (
        mock.patch.object(cmd.cfg, "get_current_context", return_value=ctx),
        mock.patch.object(
            cmd.archive_lib, "resolve_single_source", return_value="mach:a"
        ),
    ):
        yield ctx


def test_list_requires_start_time(wired):
    res = CliRunner().invoke(main, ["agent-archives", "list", "db-01"])
    assert res.exit_code != 0
    assert "start-time" in res.output or "-t" in res.output


def test_list_single_instant(wired):
    captured = {}

    def fake_list(api_url, api_key, org, source_uids, start, end):
        captured["window"] = (start, end)
        captured["uids"] = source_uids
        return [_archive("a1")]

    with mock.patch.object(archive_api, "list_agent_archives", side_effect=fake_list):
        res = CliRunner().invoke(
            main, ["agent-archives", "list", "db-01", "-t", "1500"]
        )
    assert res.exit_code == 0, res.output
    assert captured["window"] == (1500, 1501)  # -e omitted → covering instant
    assert captured["uids"] == ["mach:a"]


def _fake_dl(saved):
    def fake_dl(api_url, api_key, org, source_uid, name, dest):
        dest.write(b"zip")
        saved.append(name)
        return 3

    return mock.patch.object(archive_api, "download_agent_archive", side_effect=fake_dl)


def test_download_by_name_to_dir(wired, tmp_path):
    saved = []
    with _fake_dl(saved):
        res = CliRunner().invoke(
            main,
            ["agent-archives", "download", "db-01", "arch.zip", "-D", str(tmp_path)],
        )
    assert res.exit_code == 0, res.output
    assert saved == ["arch.zip"]
    assert (tmp_path / "arch.zip").read_bytes() == b"zip"


def test_download_by_name_defaults_to_cwd(wired, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    saved = []
    with _fake_dl(saved):
        res = CliRunner().invoke(
            main, ["agent-archives", "download", "db-01", "arch.zip"]
        )
    assert res.exit_code == 0, res.output
    assert (tmp_path / "arch.zip").read_bytes() == b"zip"


def test_download_by_time_instant(wired, tmp_path):
    saved = []
    window = {}

    def fake_list(api_url, api_key, org, source_uids, start, end):
        window["w"] = (start, end)
        return [_archive("covering.zip")]

    with (
        mock.patch.object(archive_api, "list_agent_archives", side_effect=fake_list),
        _fake_dl(saved),
    ):
        res = CliRunner().invoke(
            main,
            ["agent-archives", "download", "db-01", "-t", "1500", "-D", str(tmp_path)],
        )
    assert res.exit_code == 0, res.output
    assert window["w"] == (1500, 1501)  # -e omitted → covering instant
    assert saved == ["covering.zip"]


def test_download_by_range_fetches_all(wired, tmp_path):
    saved = []
    archives = [_archive("a1.zip"), _archive("a2.zip")]
    with (
        mock.patch.object(archive_api, "list_agent_archives", return_value=archives),
        _fake_dl(saved),
    ):
        res = CliRunner().invoke(
            main,
            [
                "agent-archives",
                "download",
                "db-01",
                "-t",
                "1000",
                "-e",
                "2000",
                "-D",
                str(tmp_path),
            ],
        )
    assert res.exit_code == 0, res.output
    assert set(saved) == {"a1.zip", "a2.zip"}
    assert {p.name for p in tmp_path.iterdir()} == {"a1.zip", "a2.zip"}


def test_download_name_and_time_are_mutually_exclusive(wired):
    res = CliRunner().invoke(
        main, ["agent-archives", "download", "db-01", "arch.zip", "-t", "1h"]
    )
    assert res.exit_code != 0
    assert "not both" in res.output


def test_download_requires_name_or_time(wired):
    res = CliRunner().invoke(main, ["agent-archives", "download", "db-01"])
    assert res.exit_code != 0
    assert "NAME" in res.output or "start-time" in res.output


def test_download_no_archives_in_window_is_clean(wired, tmp_path):
    with (
        mock.patch.object(archive_api, "list_agent_archives", return_value=[]),
        mock.patch.object(archive_api, "download_agent_archive") as dl,
    ):
        res = CliRunner().invoke(
            main,
            ["agent-archives", "download", "db-01", "-t", "1h", "-D", str(tmp_path)],
        )
    assert res.exit_code == 0, res.output
    dl.assert_not_called()
    assert list(tmp_path.iterdir()) == []


def test_download_failure_leaves_no_partial_file(wired, tmp_path):
    def boom(api_url, api_key, org, source_uid, name, d):
        d.write(b"partial")
        raise SystemExit("simulated 404 mid-stream")

    with mock.patch.object(archive_api, "download_agent_archive", side_effect=boom):
        res = CliRunner().invoke(
            main,
            ["agent-archives", "download", "db-01", "arch.zip", "-D", str(tmp_path)],
        )
    assert res.exit_code != 0
    assert list(tmp_path.iterdir()) == []  # no .part, no final file


def test_download_rejects_slashed_name(wired, tmp_path):
    # A name with a path separator can't steer the local write path; rejected
    # before any file open or network call.
    with mock.patch.object(archive_api, "download_agent_archive") as dl:
        res = CliRunner().invoke(
            main,
            [
                "agent-archives",
                "download",
                "db-01",
                "../../../etc/evil.zip",
                "-D",
                str(tmp_path),
            ],
        )
    assert res.exit_code != 0
    assert "invalid archive name" in res.output
    dl.assert_not_called()


def test_download_bad_output_dir_is_clean_error(wired, tmp_path):
    # -D under an existing file → clean error, not a raw traceback.
    afile = tmp_path / "f"
    afile.write_text("x")
    res = CliRunner().invoke(
        main,
        [
            "agent-archives",
            "download",
            "db-01",
            "arch.zip",
            "-D",
            str(afile / "sub"),
        ],
    )
    assert res.exit_code != 0
    assert "cannot create output directory" in res.output
    assert not isinstance(res.exception, NotADirectoryError)
