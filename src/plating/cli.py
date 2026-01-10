#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Plating CLI - Legacy module for backward compatibility.

This module now re-exports from plating.cli.main.
"""

from plating.cli.main import main

__all__ = ["main"]


if __name__ == "__main__":
    main()
