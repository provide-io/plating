# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Tests for reading pyvider's config out of pyproject.toml.

`[tool.pyvider]` is the PEP 518 location and the one pyvider's own CLI reads,
so plating has to read it too -- providers put their component packages there
and plating was looking only at the top-level `[pyvider]` table.
"""

from pathlib import Path

import pytest

from plating.cli.utils.pyproject import (
    get_provider_name_from_pyproject,
    get_pyvider_component_packages,
)


@pytest.fixture
def pyproject(tmp_path: Path):
    def _write(body: str) -> Path:
        path = tmp_path / "pyproject.toml"
        path.write_text(body)
        return path

    return _write


class TestComponentPackages:
    @pytest.mark.parametrize("section", ["tool.pyvider", "pyvider"])
    def test_read_from_either_section(self, pyproject, section: str) -> None:
        path = pyproject(f'[{section}]\ncomponent_packages = ["mypkg.components"]\n')
        assert get_pyvider_component_packages(path) == ["mypkg.components"]

    def test_scoped_section_wins(self, pyproject) -> None:
        path = pyproject(
            '[pyvider]\ncomponent_packages = ["top.level"]\n\n'
            '[tool.pyvider]\ncomponent_packages = ["scoped"]\n'
        )
        assert get_pyvider_component_packages(path) == ["scoped"]

    def test_absent_returns_none(self, pyproject) -> None:
        assert get_pyvider_component_packages(pyproject('[project]\nname = "x"\n')) is None

    def test_missing_file_returns_none(self, tmp_path: Path) -> None:
        assert get_pyvider_component_packages(tmp_path / "nope.toml") is None


class TestProviderName:
    @pytest.mark.parametrize("section", ["tool.pyvider", "pyvider"])
    @pytest.mark.parametrize("key", ["name", "provider_name"])
    def test_read_from_either_section_and_key(self, pyproject, section: str, key: str) -> None:
        path = pyproject(f'[{section}]\n{key} = "myprovider"\n')
        assert get_provider_name_from_pyproject(path) == "myprovider"

    def test_scoped_section_wins(self, pyproject) -> None:
        path = pyproject('[pyvider]\nname = "toplevel"\n\n[tool.pyvider]\nname = "scoped"\n')
        assert get_provider_name_from_pyproject(path) == "scoped"

    def test_canonical_key_wins_over_alias(self, pyproject) -> None:
        path = pyproject('[tool.pyvider]\nname = "canonical"\nprovider_name = "alias"\n')
        assert get_provider_name_from_pyproject(path) == "canonical"

    def test_tool_plating_remains_the_last_resort(self, pyproject) -> None:
        path = pyproject('[tool.plating]\nprovider_name = "legacy"\n')
        assert get_provider_name_from_pyproject(path) == "legacy"

    def test_pyvider_section_beats_tool_plating(self, pyproject) -> None:
        path = pyproject('[tool.pyvider]\nname = "current"\n\n[tool.plating]\nprovider_name = "legacy"\n')
        assert get_provider_name_from_pyproject(path) == "current"

    def test_absent_returns_none(self, pyproject) -> None:
        assert get_provider_name_from_pyproject(pyproject('[project]\nname = "x"\n')) is None
