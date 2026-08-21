#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Every component type's examples have to be found and written out.

The compiler recognised two block keywords, `resource` and `data`, and globbed
only `*.tf`. So an action, an ephemeral resource, a list resource and a state
store each looked like a bundle whose examples referenced nothing: the
directory was created and left empty, and `soup stir` counted it as passing
because an empty directory applies nothing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from plating.bundles import PlatingBundle
from plating.compiler.single import SingleCompilationResult, SingleExampleCompiler
from plating.types import ComponentType

CASES = [
    ("action", ComponentType.ACTION, "pyvider_echo", 'action "pyvider_echo" "example" {\n}\n', ".tf"),
    (
        "ephemerals",
        ComponentType.EPHEMERAL_RESOURCE,
        "pyvider_lease",
        'ephemeral "pyvider_lease" "example" {\n}\n',
        ".tf",
    ),
    (
        "state_stores",
        ComponentType.STATE_STORE,
        "pyvider_filesystem_store",
        'terraform {\n  state_store "pyvider_filesystem_store" {\n    provider "pyvider" {}\n  }\n}\n',
        ".tf",
    ),
    (
        "list_resources",
        ComponentType.LIST_RESOURCE,
        "pyvider_directory_entry",
        'list "pyvider_directory_entry" "example" {\n  provider = pyvider\n}\n',
        ".tfquery.hcl",
    ),
]


@pytest.mark.parametrize(("dirname", "comp_type", "component", "body", "suffix"), CASES)
def test_the_example_is_written_out(
    tmp_path: Path, dirname: str, comp_type: ComponentType, component: str, body: str, suffix: str
) -> None:
    """The bundle directory is deliberately not named after the component.

    `filesystem_store.plating` documents `pyvider_filesystem_store`, and
    `directory_entries.plating` documents `pyvider_directory_entry`, so a
    compiler that matches on the directory name finds nothing.
    """
    plating_dir = tmp_path / f"{dirname}.plating"
    (plating_dir / "docs").mkdir(parents=True)
    (plating_dir / "docs" / f"{component}.tmpl.md").write_text("# x", encoding="utf-8")
    (plating_dir / "examples").mkdir()
    (plating_dir / "examples" / f"example{suffix}").write_text(body, encoding="utf-8")

    bundle = PlatingBundle(name=dirname, plating_dir=plating_dir, component_type=comp_type.value)
    out = tmp_path / "examples"
    out.mkdir()

    compiler = SingleExampleCompiler("pyvider", "0.5.0")
    compiler._compile_component_examples(bundle, out, SingleCompilationResult())

    written = sorted(p.name for p in (out / dirname).iterdir()) if (out / dirname).exists() else []
    assert written, f"{comp_type.value} produced an empty directory"
    assert f"example{suffix}" in written, f"expected example{suffix}, got {written}"
    assert "provider.tf" in written


def test_a_state_store_keeps_its_terraform_block(tmp_path: Path) -> None:
    """A state store is configured *inside* `terraform {}`.

    The provider-block stripper removes terraform blocks, which for this one
    component removes the example itself.
    """
    plating_dir = tmp_path / "state_stores.plating"
    (plating_dir / "docs").mkdir(parents=True)
    (plating_dir / "docs" / "pyvider_filesystem_store.tmpl.md").write_text("# x", encoding="utf-8")
    (plating_dir / "examples").mkdir()
    body = 'terraform {\n  state_store "pyvider_filesystem_store" {\n    path = "./s"\n  }\n}\n'
    (plating_dir / "examples" / "example.tf").write_text(body, encoding="utf-8")

    bundle = PlatingBundle(
        name="state_stores", plating_dir=plating_dir, component_type=ComponentType.STATE_STORE.value
    )
    out = tmp_path / "examples"
    out.mkdir()
    SingleExampleCompiler("pyvider", "0.5.0")._compile_component_examples(
        bundle, out, SingleCompilationResult()
    )

    written = (out / "state_stores" / "example.tf").read_text(encoding="utf-8")
    assert "state_store" in written
    assert "path" in written


# 🧪📂🔚
