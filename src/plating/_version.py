#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Version handling for plating.

This module uses the shared versioning utility from provide-foundation.
"""

from __future__ import annotations

from provide.foundation.utils.versioning import get_version

__version__ = get_version("plating", caller_file=__file__)

__all__ = ["__version__"]

# 🍽️📖🔚
