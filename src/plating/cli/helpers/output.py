# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Output formatting helpers for CLI commands."""

from provide.foundation import pout

from plating.types import PlateResult


def print_plate_success(result: PlateResult) -> None:
    """Print success message for plate operation.

    Args:
        result: Plate operation result
    """
    # Print summary with file count and duration
    pout(f"✅ Generated {result.files_generated} files in {result.duration_seconds:.1f}s")

    if result.output_files:
        for file in result.output_files[:10]:  # Show first 10
            pout(f"  • {file}")
        if len(result.output_files) > 10:
            pout(f"  ... and {len(result.output_files) - 10} more")
