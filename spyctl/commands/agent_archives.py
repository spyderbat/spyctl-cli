"""The 'agent-archives' command group: list and download raw agent archive zips.

Modeled on the `report` group: a list+download artifact surface that owns its
own commands rather than living under `get` (which can't host a binary
download). `list` and `download` share the same SOURCE + time selectors.
"""

import os
from typing import Optional

import click

import spyctl.api.archive as archive_api
import spyctl.commands.archive_lib as archive_lib
import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources.agent_archives as archive_res
import spyctl.spyctl_lib as lib
from spyctl import cli

# Time options local to `list`. Unlike the shared `time_options`, `-t` is
# required and `-e` defaults to None: `-t` alone selects the archive covering
# that instant; `-e` extends it to a range. This "covering" sense is specific
# to archives (discrete, sequential zips) and differs from the usual "since T"
# meaning of `-t` elsewhere in the CLI.
start_time_option = click.option(
    "-t",
    "--start-time",
    "st",
    required=True,
    type=lib.time_inp,
    help="Time to cover. Alone, returns the archive covering this instant;"
    " with -e, the start of a range. Accepts 3pm, 2h, ISO 8601, or epoch.",
)
end_time_option = click.option(
    "-e",
    "--end-time",
    "et",
    default=None,
    type=lib.time_inp,
    help="End of the range (at most 24h after -t). Omit to fetch the single"
    " archive covering -t.",
)
# Same as `start_time_option` but optional — on `download`, a positional NAME is
# the alternative to a time selector.
start_time_option_optional = click.option(
    "-t",
    "--start-time",
    "st",
    default=None,
    type=lib.time_inp,
    help="Time to cover (instead of a NAME). Alone, the archive covering this"
    " instant; with -e, the start of a range. Accepts 3pm, 2h, ISO, epoch.",
)
source_arg = click.argument("source", required=True)


@click.group("agent-archives", cls=lib.CustomSubGroup, epilog=lib.SUB_EPILOG)
@_so.help_option
def agent_archives() -> None:
    """List and download raw agent archive zips."""


# ----------------------------------------------------------------- #
#                              list                                 #
# ----------------------------------------------------------------- #


@agent_archives.command("list", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.help_option
@source_arg
@start_time_option
@end_time_option
@_so.exact_match_option
@_so.output_option
def list_archives(
    source: str,
    st: float,
    et: Optional[float],
    exact: bool,
    output: str,
) -> None:
    """List archive zips for a SOURCE (name, hostname, or mach: id).

    \b
      agent-archives list db-01 -t 3:15pm        # the archive covering 3:15
      agent-archives list db-01 -t 3pm -e 5pm    # a range (max 24h)
    """
    handle_list(source, st, et, exact, output)


def handle_list(
    source: str,
    st: float,
    et: Optional[float],
    exact: bool,
    output: str,
) -> None:
    """Resolve the SOURCE, then list its archives over the time window."""
    ctx = cfg.get_current_context()
    source_uid = archive_lib.resolve_single_source(ctx, source, exact)
    start, end = archive_lib.resolve_window(st, et)
    archives = archive_api.list_agent_archives(
        *ctx.get_api_data(), [source_uid], start, end
    )
    if output in (lib.OUTPUT_DEFAULT, lib.OUTPUT_WIDE):
        cli.show(archive_res.archive_summary_output(archives), lib.OUTPUT_RAW)
    else:
        for archive in archives:
            cli.show(archive, output)


# ----------------------------------------------------------------- #
#                            download                              #
# ----------------------------------------------------------------- #


@agent_archives.command("download", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.help_option
@source_arg
@click.argument("name", required=False)
@start_time_option_optional
@end_time_option
@_so.exact_match_option
@click.option(
    "-D",
    "--output-dir",
    "output_dir",
    default=".",
    show_default=True,
    type=click.Path(file_okay=False, dir_okay=True),
    help="Directory to save the zips into (one file per archive, named by the"
    " archive). Created if it doesn't exist.",
)
def download_archive(
    source: str,
    name: Optional[str],
    st: Optional[float],
    et: Optional[float],
    exact: bool,
    output_dir: str,
) -> None:
    """Download archive zips for a SOURCE -- by time/range, or by exact NAME.

    Give a time selector (same as 'list', no names to copy) OR a specific NAME
    from 'list'. `-t` alone fetches the archive covering that instant;
    `-t`/`-e` fetches every archive in the range (max 24h).

    \b
      agent-archives download db-01 -t 3:15pm            # the archive at 3:15
      agent-archives download db-01 -t 3pm -e 5pm         # every archive 3-5pm
      agent-archives download db-01 -t 2h -D ./evidence   # into a directory
      agent-archives download db-01 mach:...-....zip      # one exact archive
    """
    handle_download(source, name, st, et, exact, output_dir)


def handle_download(
    source: str,
    name: Optional[str],
    st: Optional[float],
    et: Optional[float],
    exact: bool,
    output_dir: str,
) -> None:
    """Download archive(s) for a SOURCE, selected by NAME or by time/range.

    Streams each archive to ``output_dir`` (one file per archive, named by the
    archive). Symmetric with `list`: the time selectors choose the same
    archives, but here they're written to disk.
    """
    if name and (st is not None or et is not None):
        cli.err_exit("give either a NAME or -t/--start-time, not both")
    if not name and st is None:
        cli.err_exit("specify an archive NAME, or -t/--start-time to download by time")
    ctx = cfg.get_current_context()
    source_uid = archive_lib.resolve_single_source(ctx, source, exact)

    if name:
        # A real archive name has no path separator (server contract); reject
        # one early so it can't steer the local write path.
        if "/" in name or "\\" in name or name in (".", ".."):
            cli.err_exit(f"invalid archive name: {name!r}")
        names = [name]
    else:
        start, end = archive_lib.resolve_window(st, et)
        archives = archive_api.list_agent_archives(
            *ctx.get_api_data(), [source_uid], start, end
        )
        if not archives:
            cli.try_log("No archives found for that source and time.")
            return
        total = sum(a.get("size", 0) for a in archives)
        cli.try_log(
            f"Downloading {len(archives)} archive(s)"
            f" ({archive_res.fmt_size(total)}) to {output_dir} ..."
        )
        names = [a["name"] for a in archives]

    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        cli.err_exit(f"cannot create output directory {output_dir}: {e.strerror or e}")
    for archive_name in names:
        _download_one(ctx, source_uid, archive_name, output_dir)


def _download_one(
    ctx: cfg.Context, source_uid: str, name: str, output_dir: str
) -> None:
    """Stream one archive zip to ``output_dir/<name>``.

    Streams to a ``.part`` temp file and atomically renames on success, so a
    failure mid-stream (e.g. the API layer exiting on a non-200) never leaves a
    partial or zero-byte file behind. The archive name is API-supplied and
    separator-free by contract; ``basename`` is a belt-and-suspenders guard so
    it can never steer the write outside ``output_dir``.
    """
    safe = os.path.basename(name)
    dest_path = os.path.join(output_dir, safe)
    tmp_path = dest_path + ".part"
    try:
        dest = open(tmp_path, "wb")
    except OSError as e:
        cli.err_exit(f"cannot write to {dest_path}: {e.strerror or e}")
    try:
        with dest:
            written = archive_api.download_agent_archive(
                *ctx.get_api_data(), source_uid, name, dest
            )
        os.replace(tmp_path, dest_path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
    click.echo(f"Saved {safe} ({archive_res.fmt_size(written)}) to {dest_path}")
