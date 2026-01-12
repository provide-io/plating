# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Main CLI entry point with Click group and command registration."""

from pathlib import Path

import click
from provide.foundation import logger
from provide.foundation.cli.decorators import logging_options

from plating.cli.commands.adorn import adorn_command
from plating.cli.commands.info import info_command
from plating.cli.commands.plate import plate_command
from plating.cli.commands.stats import stats_command
from plating.cli.commands.validate import validate_command


@click.group()
@logging_options
@click.pass_context
def main(ctx: click.Context, log_level: str | None, log_file: Path | None, log_format: str) -> None:
    """Plating - Modern async documentation generator with foundation integration."""
    # Configure logging if options provided
    if log_level:
        from provide.foundation import LoggingConfig, TelemetryConfig, get_hub

        hub = get_hub()
        from typing import Literal, cast

        LogLevel = Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE", "NOTSET"]
        updated_config = TelemetryConfig(
            service_name="plating",
            logging=LoggingConfig(default_level=cast(LogLevel, log_level.upper())),
        )
        hub.initialize_foundation(config=updated_config)
        logger.debug(f"Log level set to {log_level.upper()}")

    # Store options in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["log_level"] = log_level
    ctx.obj["log_file"] = log_file
    ctx.obj["log_format"] = log_format


# Register commands
main.add_command(adorn_command)
main.add_command(plate_command)
main.add_command(validate_command)
main.add_command(info_command)
main.add_command(stats_command)


if __name__ == "__main__":
    main()
