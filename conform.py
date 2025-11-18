#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""This script enforces header and footer conformance on Python source files."""

import ast
from pathlib import Path
import sys

HEADER_SPDX = [
    "# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.",
    "# SPDX-License-Identifier: Apache-2.0",
    "#",
]
PLACEHOLDER_DOCSTRING = '"""TODO: Add module docstring."""'
FOOTER = "# 🍽️📖🔚"


def get_module_docstring_and_body_start(source: str) -> tuple[str | None, int]:
    """
    Safely extracts the module docstring and the start line of the main code body.
    """
    try:
        tree = ast.parse(source)
        docstring = ast.get_docstring(tree)

        node_index = 1 if docstring else 0
        if len(tree.body) > node_index:
            body_node = tree.body[node_index]
            start_line = body_node.lineno - 1
            if hasattr(body_node, "decorator_list") and body_node.decorator_list:
                start_line = body_node.decorator_list[0].lineno - 1
            return docstring, start_line
        return docstring, -1
    except (SyntaxError, ValueError):
        return None, 0


def process_file(filepath: str | Path) -> None:
    """Applies header/footer conformance to a single Python file."""
    filepath = Path(filepath)
    try:
        with filepath.open(encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return

    lines = content.split("\n")
    original_first_line = lines[0] if lines else ""

    # 1. Determine first line
    is_executable = original_first_line.startswith("#!")
    new_header_lines = [original_first_line] if is_executable else ["# "]
    new_header_lines.extend(HEADER_SPDX)

    # 2. Handle Docstring
    existing_docstring, body_start_line = get_module_docstring_and_body_start(content)
    docstring_block = f'"""{existing_docstring}"""' if existing_docstring else PLACEHOLDER_DOCSTRING
    new_header_lines.extend(["", docstring_block])

    # 3. Get the code body
    core_body_lines = lines[body_start_line:] if body_start_line != -1 else []

    # 4. Strip old footers and trailing whitespace
    body_content = "\n".join(core_body_lines).rstrip()

    final_body_lines = list(body_content.split("\n"))

    # 5. Construct final content
    full_header = "\n".join(new_header_lines)
    final_body = "\n".join(final_body_lines)

    final_content = (full_header + "\n\n" + final_body).rstrip()
    final_content += f"\n\n{FOOTER}\n"

    # 6. Write back to file
    try:
        with filepath.open("w", encoding="utf-8") as f:
            f.write(final_content)
    except Exception as e:
        print(f"Error writing to {filepath}: {e}", file=sys.stderr)


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 conform.py <file1.py> <file2.py> ...", file=sys.stderr)
        sys.exit(1)

    for filepath in sys.argv[1:]:
        process_file(filepath)


if __name__ == "__main__":
    main()

# 🍽️📖🔚
