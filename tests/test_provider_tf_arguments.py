#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""A generated provider block may only name arguments the provider accepts.

Terraform refuses an entire configuration over one argument it does not
recognise, so a guessed name does not degrade -- it stops the example running
at all. `provider_testmode = true` was written into five of terraform-provider-
pyvider's examples; the attribute is called `pyvider_testmode`, and every one of
those five failed with "Unsupported argument" from the day they were generated.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from plating.compiler.single import SingleExampleCompiler

TESTMODE = "pyvider_testmode"


@pytest.fixture
def component_dir(tmp_path: Path) -> Path:
    d = tmp_path / "component"
    d.mkdir()
    return d


def _provider_tf(component_dir: Path, *, is_test_only: bool, attributes: set[str] | None) -> str:
    SingleExampleCompiler("pyvider", "0.5.0", attributes)._generate_provider_tf(component_dir, is_test_only)
    return (component_dir / "provider.tf").read_text(encoding="utf-8")


class TestProviderArguments:
    def test_the_known_attribute_is_emitted(self, component_dir: Path) -> None:
        out = _provider_tf(component_dir, is_test_only=True, attributes={TESTMODE, "api_token"})

        assert f"{TESTMODE} = true" in out

    def test_an_unknown_attribute_is_not_guessed(self, component_dir: Path) -> None:
        """The provider has a config block, and no testmode attribute in it."""
        out = _provider_tf(component_dir, is_test_only=True, attributes={"api_token"})

        assert TESTMODE not in out
        assert "testmode = true" not in out

    def test_nothing_is_emitted_when_the_schema_is_unknown(self, component_dir: Path) -> None:
        out = _provider_tf(component_dir, is_test_only=True, attributes=None)

        assert "= true" not in out

    def test_the_old_wrong_name_is_never_written(self, component_dir: Path) -> None:
        """`provider_testmode` is not an attribute of any provider seen so far."""
        for attributes in (None, set(), {TESTMODE}, {"api_token"}):
            out = _provider_tf(component_dir, is_test_only=True, attributes=attributes)
            assert "provider_testmode" not in out

    def test_a_test_only_component_is_told_how_to_be_published(self, component_dir: Path) -> None:
        """Without the argument, the reader still needs to know what to do."""
        out = _provider_tf(component_dir, is_test_only=True, attributes=None)

        assert "PYVIDER_TESTMODE=true" in out
        assert "test_only" in out

    def test_a_normal_component_gets_no_testmode_anything(self, component_dir: Path) -> None:
        out = _provider_tf(component_dir, is_test_only=False, attributes={TESTMODE})

        assert "testmode" not in out.lower()
        assert "PYVIDER_TESTMODE" not in out

    def test_the_required_providers_block_is_always_written(self, component_dir: Path) -> None:
        out = _provider_tf(component_dir, is_test_only=False, attributes=None)

        assert 'source  = "local/providers/pyvider"' in out
        assert 'version = ">= 0.5.0"' in out
        assert 'provider "pyvider"' in out


# 🧪🔧🔚
