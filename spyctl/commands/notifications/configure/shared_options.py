"""Shared options for configuring notification settings."""

from typing import Dict

import click

import spyctl.spyctl_lib as lib
from spyctl.api.notification_targets import get_notification_targets
from spyctl.api.notification_templates import get_notification_templates
from spyctl.config import configs as cfg


def notification_settings_options(f):
    """Add notification settings options to a click command."""
    f = click.option(
        "--is-disabled",
        help="Disable notifications.",
        is_flag=True,
        metavar="",
    )(f)
    f = click.option(
        "--cooldown",
        help="The cooldown period in seconds.",
        type=click.INT,
        metavar="",
    )(f)
    f = click.option(
        "--cooldown-by",
        help="The cooldown by field(s).",
        type=lib.ListParam(),
        metavar="",
    )(f)
    f = click.option(
        "--aggregate-by",
        hidden=True,
        help="The aggregate by field(s).",
        type=lib.ListParam(),
        metavar="",
    )(f)
    f = click.option(
        "--aggregate",
        help="The aggregate function(s).",
        hidden=True,
        is_flag=True,
        metavar="",
    )(f)
    f = click.option(
        "--aggregate-seconds",
        help="The aggregate seconds.",
        hidden=True,
        type=click.INT,
        metavar="",
    )(f)
    f = click.option(
        "--targets",
        help="The Name or UID of targets to send notifications to.",
        type=lib.ListParam(),
        metavar="",
    )(f)
    f = click.option(
        "--target-map",
        help="Map target names to template names, can be used multiple times."
        " Usage: --target-map TGT_NAME=TEMPLATE_NAME",
        type=lib.DictParam(),
        multiple=True,
        metavar="",
    )(f)
    return f


def get_target_map(**kwargs) -> Dict:
    """Get the target map from the kwargs."""
    ctx = cfg.get_current_context()
    targets = kwargs.pop("targets", [])
    target_mappings = kwargs.pop("target_map", [])
    target_map = {}
    if targets:
        for tgt_name_or_uid in targets:
            tgt_params = {
                "name_or_uid_equals": tgt_name_or_uid,
            }
            tgts, _ = get_notification_targets(*ctx.get_api_data(), **tgt_params)
            if not tgts:
                lib.err_exit(f"Target '{tgt_name_or_uid}' not found")
            tgt = tgts[0]
            target_map[tgt["uid"]] = ""
    if target_mappings:
        for single_map in target_mappings:
            tgt_name_or_uid, tmpl_name_or_uid = next(iter(single_map.items()))
            tgt_params = {
                "name_or_uid_equals": tgt_name_or_uid,
            }
            tgts, _ = get_notification_targets(*ctx.get_api_data(), **tgt_params)
            if not tgts:
                lib.err_exit(f"Target '{tgt_name_or_uid}' not found")
            tgt = tgts[0]
            tmpl_params = {
                "name_or_uid_equals": tmpl_name_or_uid,
            }
            tmpls, _ = get_notification_templates(*ctx.get_api_data(), **tmpl_params)
            if not tmpls:
                lib.err_exit(f"Template '{tmpl_name_or_uid}' not found")
            tmpl = tmpls[0]
            target_map[tgt["uid"]] = tmpl["uid"]
    return target_map
