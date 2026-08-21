#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for the tfprotov6.11 component types.

Ephemeral resources, list resources, state stores and actions have to travel
the whole pipeline -- discovery, schema extraction, adorning, rendering -- and
land in the directory layout terraform-plugin-docs publishes to the registry.
"""

from pathlib import Path

import pytest

from plating.adorner.adorner import _ADORNABLE_TYPES, _is_adorned
from plating.bundles import PlatingBundle
from plating.discovery import PlatingDiscovery
from plating.schema.helpers import extract_component_schemas, get_component_schema
from plating.templating.generator import TemplateGenerator
from plating.types import ComponentType, SchemaInfo
from tests.nav_shape import as_mapping

PROTOCOL_TYPES = [
    ComponentType.EPHEMERAL_RESOURCE,
    ComponentType.LIST_RESOURCE,
    ComponentType.STATE_STORE,
    ComponentType.ACTION,
]


class TestComponentTypeModel:
    """The enum is the single source of truth for names and paths."""

    @pytest.mark.parametrize(
        ("component_type", "display", "subdir", "package"),
        [
            (ComponentType.EPHEMERAL_RESOURCE, "Ephemeral Resource", "ephemeral-resources", "ephemerals"),
            (ComponentType.LIST_RESOURCE, "List Resource", "list-resources", "list_resources"),
            (ComponentType.STATE_STORE, "State Store", "state-stores", "state_stores"),
            (ComponentType.ACTION, "Action", "actions", "actions"),
        ],
    )
    def test_registry_layout_matches_upstream(self, component_type, display, subdir, package) -> None:
        """Directory names match what terraform-plugin-docs writes."""
        assert component_type.display_name == display
        assert component_type.output_subdir == subdir
        assert component_type.source_package == package

    def test_every_type_has_a_plural_name(self) -> None:
        for component_type in ComponentType:
            assert component_type.plural_name.endswith("s")

    def test_documentable_covers_protocol_types_and_excludes_provider(self) -> None:
        documentable = ComponentType.documentable()
        for component_type in PROTOCOL_TYPES:
            assert component_type in documentable
        assert ComponentType.PROVIDER not in documentable

    def test_output_subdirs_are_unique(self) -> None:
        subdirs = [member.output_subdir for member in ComponentType]
        assert len(subdirs) == len(set(subdirs))

    def test_list_resource_examples_are_query_files(self) -> None:
        """A list resource's example is a query file; Terraform rejects it as .tf."""
        assert ComponentType.LIST_RESOURCE.example_filename == "list-resource.tfquery.hcl"
        assert ComponentType.LIST_RESOURCE.example_suffix == ".tfquery.hcl"
        assert ComponentType.ACTION.example_suffix == ".tf"

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("ephemeral_resource", ComponentType.EPHEMERAL_RESOURCE),
            ("ephemeral-resources", ComponentType.EPHEMERAL_RESOURCE),
            ("state_store", ComponentType.STATE_STORE),
            ("state-stores", ComponentType.STATE_STORE),
            ("ACTION", ComponentType.ACTION),
        ],
    )
    def test_from_value_accepts_dimension_and_directory_names(self, value, expected) -> None:
        assert ComponentType.from_value(value) is expected

    def test_from_value_rejects_unknown(self) -> None:
        with pytest.raises(ValueError, match="Unknown component type"):
            ComponentType.from_value("provisioner")

    def test_only_functions_are_signature_backed(self) -> None:
        assert not ComponentType.FUNCTION.is_schema_backed
        for component_type in PROTOCOL_TYPES:
            assert component_type.is_schema_backed


class TestBundleDiscovery:
    """A bundle's type is inferred from the package its .plating sits in."""

    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            ("pyvider/components/ephemerals/lease.plating", "ephemeral_resource"),
            ("pyvider/components/list_resources/secret_notes.plating", "list_resource"),
            ("pyvider/components/state_stores/filesystem_store.plating", "state_store"),
            ("pyvider/components/actions/echo.plating", "action"),
            ("pyvider/components/resources/file_content.plating", "resource"),
            ("pyvider/components/data_sources/file_info.plating", "data_source"),
            ("pyvider/components/functions/numeric.plating", "function"),
            ("pyvider/components/provider.plating", "provider"),
        ],
    )
    def test_component_type_from_path(self, path, expected) -> None:
        discovery = PlatingDiscovery()
        assert discovery._determine_component_type(Path(path)) == expected

    def test_list_resources_are_not_mistaken_for_resources(self) -> None:
        """ "list_resources" ends in a segment a naive check would claim."""
        discovery = PlatingDiscovery()
        resolved = discovery._determine_component_type(Path("pkg/list_resources/notes.plating"))
        assert resolved == ComponentType.LIST_RESOURCE.value


class TestExampleLoading:
    """Query-file examples have to load like .tf examples do."""

    def test_tfquery_example_is_loaded_under_its_bare_name(self, tmp_path: Path) -> None:
        examples = tmp_path / "notes.plating" / "examples"
        examples.mkdir(parents=True)
        (examples / "example.tfquery.hcl").write_text('list "pyvider_secret_note" "all" {}\n')

        bundle = PlatingBundle(
            name="notes", plating_dir=tmp_path / "notes.plating", component_type="list_resource"
        )

        assert bundle.has_examples()
        assert "example" in bundle.load_examples()
        assert "pyvider_secret_note" in bundle.load_examples()["example"]

    def test_tf_examples_still_load(self, tmp_path: Path) -> None:
        examples = tmp_path / "lease.plating" / "examples"
        examples.mkdir(parents=True)
        (examples / "basic.tf").write_text('ephemeral "pyvider_lease" "held" {}\n')

        bundle = PlatingBundle(
            name="lease", plating_dir=tmp_path / "lease.plating", component_type="ephemeral_resource"
        )

        assert set(bundle.load_examples()) == {"basic"}


class TestSchemaExtraction:
    """Every schema-backed type reads the same get_schema() contract."""

    class _Component:
        _is_test_only = True

        def __init__(self, schema) -> None:
            self._schema = schema

        def get_schema(self):
            return self._schema

    class _Schema:
        def __init__(self, block) -> None:
            self.version = 1
            self.block = block

    class _Block:
        def __init__(self, attributes) -> None:
            self.attributes = attributes
            self.block_types = {}
            self.description = "A state store."

    class _Attribute:
        def __init__(self, name, required=False, computed=False) -> None:
            self.name = name
            self.type = None
            self.description = f"The {name}."
            self.required = required
            self.optional = not required and not computed
            self.computed = computed
            self.sensitive = False
            self.write_only = False
            self.deprecated = False

    def _component(self):
        block = self._Block({"path": self._Attribute("path", required=True)})
        return self._Component(self._Schema(block))

    def test_schemas_extracted_for_protocol_types(self) -> None:
        schemas = extract_component_schemas({"pyvider_fs": self._component()})

        assert "pyvider_fs" in schemas
        assert schemas["pyvider_fs"]["test_only"] is True
        assert "path" in schemas["pyvider_fs"]["block"]["attributes"]

    def test_component_schema_is_found_by_type_derived_key(self) -> None:
        """The lookup key is derived from the type, not branched per type."""
        provider_schema = {"state_store_schemas": extract_component_schemas({"pyvider_fs": self._component()})}
        bundle = PlatingBundle(
            name="fs", plating_dir=Path("state_stores/fs.plating"), component_type="state_store"
        )

        schema_info = get_component_schema(bundle, ComponentType.STATE_STORE, provider_schema)

        assert schema_info is not None
        assert "path" in schema_info.attributes


class TestSchemaMarkdown:
    """Attribute types render with the spellings the registry publishes."""

    def test_cty_type_names_map_to_registry_names(self) -> None:
        schema = SchemaInfo(
            attributes={
                "enabled": {"type": "bool", "computed": True, "description": "Whether it is on."},
                "count": {"type": "number", "required": True, "description": "How many."},
                "tags": {"type": ["list", "string"], "optional": True, "description": "Tags."},
            }
        )

        markdown = schema.to_markdown()

        assert "- `enabled` (Boolean) - Whether it is on." in markdown
        assert "- `count` (Number) - How many." in markdown
        assert "- `tags` (List of String) - Tags." in markdown

    def test_undocumented_attribute_has_no_trailing_dash(self) -> None:
        schema = SchemaInfo(attributes={"path": {"type": "string", "required": True}})

        assert "- `path` (String)\n" in schema.to_markdown()


class TestGeneratedScaffolding:
    """Adorning a protocol component produces usable HCL and frontmatter."""

    @pytest.fixture
    def generator(self) -> TemplateGenerator:
        return TemplateGenerator()

    class _Component:
        """Holds a lease."""

        _is_test_only = False

    class _TestOnlyComponent:
        """Holds a lease."""

        _is_test_only = True

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("component_type", "heading"),
        [
            ("ephemeral_resource", "Ephemeral Resource"),
            ("list_resource", "List Resource"),
            ("state_store", "State Store"),
            ("action", "Action"),
        ],
    )
    async def test_template_titles_the_component_type(self, generator, component_type, heading) -> None:
        template = await generator.generate_template("pyvider_thing", component_type, self._Component)

        assert f'page_title: "{heading}: pyvider_thing"' in template
        assert f"# pyvider_thing ({heading})" in template
        assert "{{ schema() }}" in template
        # schema() emits its own "## Schema"; a literal one would duplicate it.
        assert "## Schema" not in template

    @pytest.mark.asyncio
    async def test_test_only_components_are_grouped_under_test_mode(self, generator) -> None:
        template = await generator.generate_template(
            "pyvider_lease", "ephemeral_resource", self._TestOnlyComponent
        )

        assert 'subcategory: "Test Mode"' in template

    @pytest.mark.asyncio
    async def test_ordinary_components_get_no_subcategory(self, generator) -> None:
        template = await generator.generate_template("pyvider_lease", "ephemeral_resource", self._Component)

        assert "subcategory:" not in template

    @pytest.mark.asyncio
    async def test_ephemeral_example_uses_an_ephemeral_block(self, generator) -> None:
        example = await generator.generate_example("pyvider_lease", "ephemeral_resource")

        assert example.startswith('ephemeral "pyvider_lease" "example"')

    @pytest.mark.asyncio
    async def test_list_example_is_a_query_block_naming_its_provider(self, generator) -> None:
        example = await generator.generate_example("pyvider_secret_note", "list_resource")

        assert 'list "pyvider_secret_note" "example"' in example
        assert "provider = pyvider" in example
        assert "config {" in example

    @pytest.mark.asyncio
    async def test_state_store_example_declares_its_provider_inline(self, generator) -> None:
        """The store loads before the provider is configured, so it names it."""
        example = await generator.generate_example("pyvider_fs", "state_store")

        assert 'state_store "pyvider_fs"' in example
        assert 'provider "pyvider" {}' in example

    @pytest.mark.asyncio
    async def test_action_example_shows_a_trigger(self, generator) -> None:
        example = await generator.generate_example("pyvider_echo", "action")

        assert 'action "pyvider_echo" "example"' in example
        assert "action_trigger" in example


class TestAdornDetection:
    """A component with a bundle must not be re-adorned over its templates."""

    def test_prefixed_component_matches_its_bundle(self) -> None:
        assert _is_adorned("pyvider_secret_note", {"secret_note"})

    def test_unprefixed_component_matches_exactly(self) -> None:
        assert _is_adorned("lease", {"lease"})

    def test_missing_component_is_reported_missing(self) -> None:
        assert not _is_adorned("pyvider_lease", {"secret_note", "file_content"})

    def test_partial_name_is_not_a_match(self) -> None:
        assert not _is_adorned("pyvider_secret_note", {"note"})

    def test_all_protocol_types_are_adornable(self) -> None:
        for component_type in PROTOCOL_TYPES:
            assert component_type.value in _ADORNABLE_TYPES


class TestNavigationLinks:
    """Navigation must link to the file the renderer actually wrote."""

    def _bundle(self, name: str, component_type: ComponentType) -> PlatingBundle:
        return PlatingBundle(
            name=name,
            plating_dir=Path(f"{component_type.source_package}/{name}.plating"),
            component_type=component_type.value,
        )

    @pytest.mark.parametrize(
        ("component_type", "name", "expected"),
        [
            (ComponentType.EPHEMERAL_RESOURCE, "pyvider_lease", "ephemeral-resources/lease.md"),
            (ComponentType.LIST_RESOURCE, "pyvider_secret_note", "list-resources/secret_note.md"),
            (ComponentType.STATE_STORE, "pyvider_fs", "state-stores/fs.md"),
            (ComponentType.ACTION, "pyvider_echo", "actions/echo.md"),
            (ComponentType.FUNCTION, "add", "functions/add.md"),
        ],
    )
    def test_nav_path_matches_rendered_filename(self, component_type, name, expected) -> None:
        from plating.mkdocs import MkdocsNavGenerator

        generator = MkdocsNavGenerator(Path(), provider_name="pyvider")
        section = generator._generate_capability_section(
            "Test Mode", {component_type.value: [(self._bundle(name, component_type), component_type)]}
        )

        links = as_mapping(as_mapping(section["Test Mode"])[component_type.plural_name])
        assert expected in links.values()

    def test_filename_rule_is_shared_with_the_renderer(self) -> None:
        from plating.core.doc_generator import document_filename

        assert document_filename("pyvider_lease", ComponentType.EPHEMERAL_RESOURCE, "pyvider") == "lease"
        # A function keeps its bare name, prefix-looking or not.
        assert document_filename("to_snake_case", ComponentType.FUNCTION, "pyvider") == "to_snake_case"
        # Without a provider name there is nothing to strip.
        assert document_filename("timed_token", ComponentType.RESOURCE, None) == "timed_token"


# 🍽️📖🔚
