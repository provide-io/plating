#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Base PlatingBundle class for managing component documentation assets."""

from __future__ import annotations

from pathlib import Path
import tomllib

from attrs import define

#
# plating/bundles/base.py
#

# Flat example files a bundle may hold. List resources are queried from
# .tfquery.hcl files, which Terraform will not accept as configuration.
EXAMPLE_FILE_PATTERNS = ("*.tf", "*.tfquery.hcl")

# An example may sit beside a sidecar declaring what it needs in order to run:
# `example.tf` is described by `example.meta.toml`. The suffix is deliberately
# outside EXAMPLE_FILE_PATTERNS so a sidecar is never mistaken for an example.
#
# It exists because an example's requirements are not one-dimensional. Some need
# a Terraform floor; some cannot run under OpenTofu at all; some need an extra
# `init` flag; some need an environment variable or network egress. A filename
# convention can encode one of those, and the rest end up undeclared -- which is
# what happened, leaving `soup stir` unable to reach the state store and the docs
# explaining a shared-secret requirement in hand-written prose.
EXAMPLE_METADATA_SUFFIX = ".meta.toml"

# Requirements that hold for every example in a bundle go in one file rather than
# being copied into each sidecar. Every example of a component that keeps
# encrypted private state needs the same shared secret; stating that once per
# example meant eight identical files, and eight places to forget when it
# changes. The leading underscore keeps it out of the way of an example named
# after it, and sorts it first so defaults are read before overrides.
BUNDLE_METADATA_NAME = f"_requirements{EXAMPLE_METADATA_SUFFIX}"


@define
class PlatingBundle:
    """Represents a single .plating bundle with its assets."""

    name: str
    plating_dir: Path
    component_type: str

    @property
    def docs_dir(self) -> Path:
        """Directory containing documentation templates."""
        return self.plating_dir / "docs"

    @property
    def examples_dir(self) -> Path:
        """Directory containing example files."""
        return self.plating_dir / "examples"

    @property
    def fixtures_dir(self) -> Path:
        """Directory containing fixture files."""
        return self.examples_dir / "fixtures"

    def has_main_template(self) -> bool:
        """Check if bundle has a main template file."""
        template_file = self.docs_dir / f"{self.name}.tmpl.md"
        pyvider_template = self.docs_dir / f"pyvider_{self.name}.tmpl.md"
        main_template = self.docs_dir / "main.md.j2"

        return any(template.exists() for template in [template_file, pyvider_template, main_template])

    def has_examples(self) -> bool:
        """Check if bundle has example files (flat .tf or grouped)."""
        if not self.examples_dir.exists():
            return False

        # Check for flat example files
        if any(any(self.examples_dir.glob(pattern)) for pattern in EXAMPLE_FILE_PATTERNS):
            return True

        # Check for grouped examples (subdirectories with main.tf)
        return any(subdir.is_dir() and (subdir / "main.tf").exists() for subdir in self.examples_dir.iterdir())

    def _read_requirements(self, path: Path) -> dict[str, object]:
        """The [requirements] table of one sidecar, or {} when there is none.

        A malformed sidecar is not fatal: returning {} degrades to the behaviour
        before requirements existed, rather than failing a docs build over
        metadata that only describes an example.
        """
        if not path.exists():
            return {}
        try:
            with path.open("rb") as handle:
                parsed = tomllib.load(handle)
        except (OSError, tomllib.TOMLDecodeError):
            return {}
        requirements = parsed.get("requirements", {})
        return requirements if isinstance(requirements, dict) else {}

    def bundle_metadata(self) -> dict[str, object]:
        """Requirements shared by every example in this bundle."""
        return self._read_requirements(self.examples_dir / BUNDLE_METADATA_NAME)

    def example_metadata(self, example_name: str) -> dict[str, object]:
        """Requirements for one example: the bundle's, plus its own.

        Requirements accumulate and are never cancelled. A per-example sidecar
        can add a constraint or extend a list, but cannot declare that this
        example escapes one the bundle imposes -- a runner that wrongly skips
        loses one result, where one that wrongly runs reports a failure
        indistinguishable from a real defect.
        """
        merged: dict[str, object] = dict(self.bundle_metadata())
        own = self._read_requirements(self.examples_dir / f"{example_name}{EXAMPLE_METADATA_SUFFIX}")
        for key, value in own.items():
            existing = merged.get(key)
            if isinstance(existing, list) and isinstance(value, list):
                merged[key] = existing + [item for item in value if item not in existing]
            else:
                merged[key] = value
        return merged

    def load_main_template(self) -> str | None:
        """Load the main template file for this component."""
        template_file = self.docs_dir / f"{self.name}.tmpl.md"
        pyvider_template = self.docs_dir / f"pyvider_{self.name}.tmpl.md"
        main_template = self.docs_dir / "main.md.j2"

        # First, try component-specific templates
        for template_path in [template_file, pyvider_template]:
            if template_path.exists():
                try:
                    return template_path.read_text(encoding="utf-8")
                except Exception:
                    return None

        # Only use main.md.j2 if it's the only component in this bundle directory
        # Check if this bundle contains multiple components by looking for other .tmpl.md files
        if main_template.exists():
            component_templates = list(self.docs_dir.glob("*.tmpl.md"))
            if len(component_templates) <= 1:  # Only this component or no specific templates
                try:
                    return main_template.read_text(encoding="utf-8")
                except Exception:
                    return None

        return None

    def load_examples(self) -> dict[str, str]:
        """Load all example files - both flat and grouped subdirs.

        Returns:
            Dictionary mapping example name to content:
            - Flat files: key is filename stem (e.g., "basic.tf" -> "basic")
            - Grouped examples: key is subdirectory name (e.g., "full_stack/main.tf" -> "full_stack")
        """
        examples: dict[str, str] = {}
        if not self.examples_dir.exists():
            return examples

        # Load flat example files (backward compatible)
        for pattern in EXAMPLE_FILE_PATTERNS:
            for example_file in self.examples_dir.glob(pattern):
                try:
                    # "example.tfquery.hcl" keys as "example", the same as
                    # "example.tf" would -- a template asks for the example by
                    # name, not by the extension its component type demands.
                    examples[example_file.name.split(".", 1)[0]] = example_file.read_text(encoding="utf-8")
                except Exception:
                    continue

        # Load grouped examples (subdirectories with main.tf)
        for subdir in self.examples_dir.iterdir():
            if subdir.is_dir():
                main_tf = subdir / "main.tf"
                if main_tf.exists():
                    try:
                        examples[subdir.name] = main_tf.read_text(encoding="utf-8")
                    except Exception:
                        continue

        return examples

    def load_partials(self) -> dict[str, str]:
        """Load all partial files from docs directory."""
        partials: dict[str, str] = {}
        if not self.docs_dir.exists():
            return partials

        for partial_file in self.docs_dir.glob("_*"):
            if partial_file.is_file():
                try:
                    partials[partial_file.name] = partial_file.read_text(encoding="utf-8")
                except Exception:
                    continue
        return partials

    def load_fixtures(self) -> dict[str, str]:
        """Load all fixture files from fixtures directory."""
        fixtures: dict[str, str] = {}
        if not self.fixtures_dir.exists():
            return fixtures

        for fixture_file in self.fixtures_dir.rglob("*"):
            if fixture_file.is_file():
                try:
                    rel_path = fixture_file.relative_to(self.fixtures_dir)
                    fixtures[rel_path.as_posix()] = fixture_file.read_text(encoding="utf-8")
                except Exception:
                    continue
        return fixtures

    def get_example_groups(self) -> list[str]:
        """Get names of example groups (subdirectories with main.tf).

        Returns:
            List of group names (subdirectory names)
        """
        if not self.examples_dir.exists():
            return []

        group_names = []
        for subdir in self.examples_dir.iterdir():
            if subdir.is_dir() and (subdir / "main.tf").exists():
                group_names.append(subdir.name)

        return group_names

    def load_group_fixtures(self, group_name: str) -> dict[str, Path]:
        """Load fixture files from a specific example group.

        Args:
            group_name: Name of the example group

        Returns:
            Dictionary mapping relative path to source Path object
        """
        group_fixtures_dir = self.examples_dir / group_name / "fixtures"
        if not group_fixtures_dir.exists():
            return {}

        fixtures = {}
        for file_path in group_fixtures_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(group_fixtures_dir)
                fixtures[rel_path.as_posix()] = file_path

        return fixtures


# 🍽️📖🔚
