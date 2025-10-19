from __future__ import annotations

from pathlib import Path

from attrs import define

#
# plating/bundles/base.py
#
"""Base PlatingBundle class for managing component documentation assets."""


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

        # Check for flat .tf files
        if any(self.examples_dir.glob("*.tf")):
            return True

        # Check for grouped examples (subdirectories with main.tf)
        for subdir in self.examples_dir.iterdir():
            if subdir.is_dir() and (subdir / "main.tf").exists():
                return True

        return False

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
        """Load all example files - both flat .tf and grouped subdirs.

        Returns:
            Dictionary mapping example name to content:
            - Flat .tf files: key is filename stem (e.g., "basic.tf" -> "basic")
            - Grouped examples: key is subdirectory name (e.g., "full_stack/main.tf" -> "full_stack")
        """
        examples: dict[str, str] = {}
        if not self.examples_dir.exists():
            return examples

        # Load flat .tf files (backward compatible)
        for example_file in self.examples_dir.glob("*.tf"):
            try:
                examples[example_file.stem] = example_file.read_text(encoding="utf-8")
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
                    fixtures[str(rel_path)] = fixture_file.read_text(encoding="utf-8")
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
                fixtures[str(rel_path)] = file_path

        return fixtures
