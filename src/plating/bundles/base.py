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
        """Check if bundle has example files."""
        if not self.examples_dir.exists():
            return False
        return any(self.examples_dir.glob("*.tf"))

    def load_main_template(self) -> str | None:
        """Load the main template file for this component."""
        template_file = self.docs_dir / f"{self.name}.tmpl.md"
        pyvider_template = self.docs_dir / f"pyvider_{self.name}.tmpl.md"
        main_template = self.docs_dir / "main.md.j2"

        for template_path in [template_file, pyvider_template, main_template]:
            if template_path.exists():
                try:
                    return template_path.read_text(encoding="utf-8")
                except Exception:
                    return None
        return None

    def load_examples(self) -> dict[str, str]:
        """Load all example files as a dictionary."""
        examples: dict[str, str] = {}
        if not self.examples_dir.exists():
            return examples

        for example_file in self.examples_dir.glob("*.tf"):
            try:
                examples[example_file.stem] = example_file.read_text(encoding="utf-8")
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
