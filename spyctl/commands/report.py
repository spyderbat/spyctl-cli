"""Handles the report subcommand for spyctl."""

import json
from typing import IO, Any, Callable, Dict, List, Optional, Type

import click
from tabulate import tabulate

import spyctl.api.reports as api
import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.primitives import response_err_msg

# ----------------------------------------------------------------- #
#                       Report Subcommand                           #
# ----------------------------------------------------------------- #


@click.group("report", cls=lib.CustomSubGroup, epilog=lib.SUB_EPILOG, hidden=True)
@click.help_option("-h", "--help", hidden=True)
def report():
    """Generate and manage reports"""


@report.command("inventory", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
def get_inventory():
    """Get the list of available report types to generate"""
    handle_get_report_inventory(lib.OUTPUT_YAML)


@report.command("generate", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
@click.option(
    "-f",
    "--from-file",
    type=click.File("r"),
    help="Read report input from a json file",
    required=False,
)
@click.option(
    "--save-input",
    type=click.Path(),
    help="Save report input to a file for future use",
)
def generate(from_file: IO[str], save_input: str):
    """Generate a new report based on available report types"""
    handle_generate_report(from_file, save_input)


@report.command("status", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
@click.option(
    "-o",
    "--output",
    default=lib.OUTPUT_DEFAULT,
    type=click.Choice(lib.OUTPUT_CHOICES + [lib.OUTPUT_WIDE], case_sensitive=False),
)
@click.argument("report_id", required=True)
def status(report_id: str, output: str):
    """Get status and metadata for a report"""
    handle_get_report_status(report_id, output)


@report.command("download", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
@click.argument("report_id", required=True)
@click.option(
    "-o",
    "--output_format",
    help="report format",
    type=click.Choice(
        ["json", "yaml", "md", "mdx", "html", "pdf"], case_sensitive=False
    ),
    default="md",
)
@click.option("-f", "--file", help="save to file", type=click.File("wb"))
def download(report_id: str, output_format: str, file: Optional[IO]):
    """Get the generated content for a report"""

    handle_get_report_download(report_id, output_format, file)


@report.command("delete", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
@click.argument("report_id", required=True)
def delete(report_id: str):
    """Deletes a report"""
    handle_delete_report(report_id)


@report.command("list", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
@click.option(
    "-o",
    "--output",
    default=lib.OUTPUT_DEFAULT,
    type=click.Choice(lib.OUTPUT_CHOICES + [lib.OUTPUT_WIDE], case_sensitive=False),
)
def report_list(output: str):
    """Get the list of generated reports with status and metadata"""
    handle_get_report_list(output)


# ----------------------------------------------------------------- #
#               Handler functions for report commands               #
# ----------------------------------------------------------------- #


def handle_get_report_inventory(output: str):
    ctx = cfg.get_current_context()
    inventory = api.get_report_inventory(*ctx.get_api_data())
    if inventory and "context_uid" in inventory:
        del inventory["context_uid"]
    cli.show(inventory, output)


def handle_generate_report(from_file: Optional[IO[str]], save_input: str):
    ctx = cfg.get_current_context()
    if from_file:
        with from_file:
            li = json.load(from_file)
        report_input = li
    else:
        click.echo("Getting available report types...\n")
        inv = api.get_report_inventory(*ctx.get_api_data())
        if not inv:
            cli.err_exit("Could not get inventory of available report types")
            return
        inventory = inv["inventory"]

        click.secho("Available Report Types", fg="green")
        for nr, report_type in enumerate(inventory):
            click.echo(
                f"{nr + 1: 2}. {report_type['short'] + ':':<30} {report_type['description']}"
            )
        report_nr = -1
        while report_nr < 0 or report_nr >= len(inventory):
            report_nr = click.prompt("Select nr of report type to generate")
            try:
                report_nr = int(report_nr) - 1
            except ValueError:
                report_nr = -1
        report_type = inventory[report_nr]
        click.secho(f"\nCollecting arguments for {report_type['short']}...", fg="green")

        report_args = {}
        for nr, arg in enumerate(report_type["args"]):
            report_args[arg["name"]] = __collect_report_arg(nr, arg)

        report_input = {
            "report_id": report_type["id"],
            "report_args": report_args,
            "report_format": "md",
            "report_tags": {"User-Agent": "spyctl"},
        }
        if save_input:
            with open(save_input, "w", encoding="utf-8") as f:
                json.dump(report_input, f, indent=2)
                click.echo(f"Report input written to {save_input}")

    click.echo("Scheduling report generation")
    response = api.generate_report(*ctx.get_api_data(), report_input)
    if not response.status_code == 200:
        cli.err_exit(response_err_msg(response))
        return
    __show_report_summary([response.json()], lib.OUTPUT_WIDE)


def handle_get_report_status(rid: str, output: str):
    ctx = cfg.get_current_context()
    report = api.get_report_status(*ctx.get_api_data(), rid)
    if output in [lib.OUTPUT_DEFAULT, lib.OUTPUT_WIDE]:
        __show_report_summary([report], output)
    else:
        cli.show(report, output)


def handle_get_report_download(rid: str, output_format: str, file: Optional[IO]):
    if output_format == "pdf" and not file:
        cli.err_exit("PDF is a binary format, use -f/--file to save to file")

    ctx = cfg.get_current_context()
    report = api.get_report_download(*ctx.get_api_data(), rid, output_format)
    if file:
        file.write(report)
        click.echo(f"Report {rid} saved to {file.name}")
    else:
        if output_format == "json":
            report = json.loads(report.decode())
            cli.show(report, lib.OUTPUT_JSON)
        else:
            cli.show(report.decode(), lib.OUTPUT_RAW)


def handle_get_report_list(output: str):
    ctx = cfg.get_current_context()
    result = api.get_report_list(*ctx.get_api_data())
    reports = result.get("reports")
    if reports is None:
        cli.err_exit("Missing reports value in get reports api response")
    if output in [lib.OUTPUT_DEFAULT, lib.OUTPUT_WIDE]:
        __show_report_summary(reports, output)
    else:
        cli.show(reports, output)


def handle_delete_report(rid: str):
    ctx = cfg.get_current_context()
    api.delete_report(*ctx.get_api_data(), rid)
    cli.show(f"Report {rid} deleted", lib.OUTPUT_RAW)


# ----------------------------------------------------------------- #
#               Helper functions                                    #
# ----------------------------------------------------------------- #


def __collect_report_arg(nr: int, arg: Dict) -> Any:
    required = arg.get("required", False)
    arg_descr = f"\n{nr + 1}. {arg['name']}: {arg['description']}, type: {arg['type']}"
    if required:
        arg_descr += " (required)"
    click.echo(arg_descr)

    prompt_args: Dict = {}
    prompt_text = f"Enter value for {arg['name']}"
    if not required:
        prompt_text += " (optional, press enter to skip)"
        prompt_args["default"] = "__skipped__"
        prompt_args["show_default"] = False
    if type_arg := __type_check_arg(arg["type"]):
        prompt_args["type"] = type_arg
    if conv_arg := __convert_argval(arg["type"]):
        prompt_args["value_proc"] = conv_arg
    value = click.prompt(prompt_text, **prompt_args)
    click.echo(f"Value entered: {value}")
    return value


def __type_check_arg(arg_type: str) -> Optional[Type]:
    if arg_type == "timestamp":
        return float
    return None


def __convert_argval(arg_type) -> Optional[Callable[[str], Any]]:
    if arg_type == "timestamp":
        return float
    return None


def __show_report_summary(reports: List[Dict], output: str):
    wide = output == lib.OUTPUT_WIDE
    summary = __reports_summary_output(reports, wide)
    cli.show(summary, lib.OUTPUT_RAW)


def __reports_summary_output(reports: List[Dict], wide=False) -> str:
    header = ["REPORT ID", "STATUS", "REPORT TYPE"]
    tag_headerset = set()
    if wide:
        header.append("FORMATS")
        for report in reports:
            tags = report["input"].get("report_tags")
            if tags:
                tag_headerset.update(tags.keys())
    tag_headers = sorted(list(tag_headerset))
    header.extend(tag_headers)
    if wide:
        header.append("ERROR")
    data = []
    for report in reports:
        data.append(__report_summary_data(report, wide, tag_headers))
    return tabulate(data, header, tablefmt="plain")


def __report_summary_data(report: Dict, wide=False, tag_headers: List = None) -> List:
    if tag_headers is None:
        tag_headers = []
    rv = [
        report["id"],
        report["status"],
        report["input"]["report_id"],
    ]
    if wide:
        rv.append(",".join(report["formats"]))
        tags = report["input"].get("report_tags")
        if tags:
            for hdr in tag_headers:
                tagv = tags.get(hdr, "")
                if hdr == "time_scheduled" or hdr == "time_published":
                    tagv = lib.epoch_to_zulu(tagv)
                rv.append(tagv)
        rv.append(report.get("error", ""))
    return rv
