#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""An example may declare what it needs in order to run.

Requirements are not one-dimensional -- a Terraform floor, an OpenTofu
incompatibility, an extra `init` flag, an environment variable, network egress --
so they are declared in a sidecar beside the example rather than encoded in its
filename. Whatever executes the generated tree never sees the .plating bundle, so
the sidecar has to survive compilation to be worth declaring.
"""

from pathlib import Path

import pytest

from plating.bundles.base import EXAMPLE_METADATA_SUFFIX, PlatingBundle

SIDECAR = """# Terraform decodes a state_store block with a nil evaluation context.
[requirements]
terraform_min = "1.14.0"
opentofu = false
init_flags = ["-enable-pluggable-state-storage-experiment"]
"""


def _bundle(tmp_path: Path, name: str = "filesystem_store") -> PlatingBundle:
    plating_dir = tmp_path / f"{name}.plating"
    (plating_dir / "examples").mkdir(parents=True)
    (plating_dir / "docs").mkdir(parents=True)
    return PlatingBundle(name=name, plating_dir=plating_dir, component_type="state_store")


@pytest.mark.unit
def test_an_example_without_a_sidecar_declares_nothing(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    (bundle.examples_dir / "example.tf").write_text("# nothing special")

    assert bundle.example_metadata("example") == {}


@pytest.mark.unit
def test_requirements_are_read_from_the_sidecar(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    (bundle.examples_dir / "example.tf").write_text("# needs an experiment flag")
    (bundle.examples_dir / f"example{EXAMPLE_METADATA_SUFFIX}").write_text(SIDECAR)

    requirements = bundle.example_metadata("example")

    assert requirements["terraform_min"] == "1.14.0"
    assert requirements["opentofu"] is False
    assert requirements["init_flags"] == ["-enable-pluggable-state-storage-experiment"]


@pytest.mark.unit
def test_a_sidecar_belongs_to_one_example_not_the_bundle(tmp_path: Path) -> None:
    """Two examples in one bundle can have different requirements."""
    bundle = _bundle(tmp_path)
    for name in ("basic", "advanced"):
        (bundle.examples_dir / f"{name}.tf").write_text("# example")
    (bundle.examples_dir / f"advanced{EXAMPLE_METADATA_SUFFIX}").write_text(SIDECAR)

    assert bundle.example_metadata("basic") == {}
    assert bundle.example_metadata("advanced")["terraform_min"] == "1.14.0"


@pytest.mark.unit
def test_a_malformed_sidecar_does_not_break_a_docs_build(tmp_path: Path) -> None:
    """Degrade to "declares nothing" rather than failing the whole build."""
    bundle = _bundle(tmp_path)
    (bundle.examples_dir / "example.tf").write_text("# example")
    (bundle.examples_dir / f"example{EXAMPLE_METADATA_SUFFIX}").write_text("this = is not [ toml")

    assert bundle.example_metadata("example") == {}


@pytest.mark.unit
def test_a_sidecar_is_never_mistaken_for_an_example(tmp_path: Path) -> None:
    """A bundle holding only a sidecar has no examples to compile."""
    bundle = _bundle(tmp_path)
    (bundle.examples_dir / f"example{EXAMPLE_METADATA_SUFFIX}").write_text(SIDECAR)

    assert bundle.has_examples() is False


@pytest.mark.unit
def test_the_sidecar_survives_compilation_into_the_generated_tree(tmp_path: Path) -> None:
    """The point of declaring requirements is that a runner can act on them.

    `soup stir` and CI see only the compiled `examples/` tree, never the .plating
    bundle, so a sidecar that stopped at the bundle would be inert.
    """
    from plating.compiler.single import SingleExampleCompiler

    bundle = _bundle(tmp_path / "src", name="filesystem_store")
    (bundle.examples_dir / "example.tf").write_text(
        'resource "pyvider_filesystem_store" "x" {\n  path = "tfstate"\n}\n'
    )
    (bundle.examples_dir / f"example{EXAMPLE_METADATA_SUFFIX}").write_text(SIDECAR)

    out = tmp_path / "examples"
    SingleExampleCompiler("pyvider").compile_examples([bundle], out)

    generated = out / "state_store" / "filesystem_store" / f"example{EXAMPLE_METADATA_SUFFIX}"
    assert generated.exists(), "requirements did not reach the generated tree"
    # Verbatim, so the comment explaining *why* survives for whoever reads it.
    assert generated.read_text() == SIDECAR


@pytest.mark.unit
def test_an_example_with_no_requirements_generates_no_sidecar(tmp_path: Path) -> None:
    from plating.compiler.single import SingleExampleCompiler

    bundle = _bundle(tmp_path / "src", name="filesystem_store")
    (bundle.examples_dir / "example.tf").write_text('resource "x" "y" {}\n')

    out = tmp_path / "examples"
    SingleExampleCompiler("pyvider").compile_examples([bundle], out)

    component_dir = out / "state_store" / "filesystem_store"
    assert list(component_dir.glob(f"*{EXAMPLE_METADATA_SUFFIX}")) == []
