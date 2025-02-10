"""Shared options across the delete subcommands."""

import click


def delete_options(f):
    """options common to all delete subcommands"""
    f = click.argument("name_or_id", required=False)(f)
    f = click.option(
        "-y",
        "--yes",
        "--assume-yes",
        is_flag=True,
        help='Automatic yes to prompts; assume "yes" as answer to all prompts'
        " and run non-interactively.",
    )(f)
    f = click.help_option("-h", "--help", hidden=True)(f)
    return f
