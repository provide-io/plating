#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Type definitions for the plating system with foundation integration."""

from enum import Enum
import json
from pathlib import Path
from typing import Any, ClassVar

from attrs import define, field
from provide.foundation import CLIContext


class ComponentType(Enum):
    """Type-safe component types for Terraform/OpenTofu providers.

    Supported types:
    - RESOURCE: Terraform resources
    - DATA_SOURCE: Terraform data sources
    - FUNCTION: Provider-defined functions
    - EPHEMERAL_RESOURCE: Short-lived resources (protocol 6.5+)
    - LIST_RESOURCE: Listable resources queried by `terraform query` (6.11)
    - STATE_STORE: Pluggable state storage backends (6.11)
    - ACTION: Provider-defined actions (6.10+)
    - PROVIDER: Provider configuration

    The member values match the dimension names pyvider registers components
    under, and `output_subdir` matches the directory layout terraform-plugin-docs
    publishes to the Terraform Registry. Keeping both in sync with upstream is
    what lets a schema key be derived as f"{type.value}_schemas" and a docs path
    as output_dir / type.output_subdir, with no per-type branching.
    """

    # Terraform/OpenTofu component types
    RESOURCE = "resource"
    DATA_SOURCE = "data_source"
    FUNCTION = "function"
    EPHEMERAL_RESOURCE = "ephemeral_resource"
    LIST_RESOURCE = "list_resource"
    STATE_STORE = "state_store"
    ACTION = "action"
    PROVIDER = "provider"

    @property
    def display_name(self) -> str:
        """Get the formatted display name."""
        return {
            self.RESOURCE: "Resource",
            self.DATA_SOURCE: "Data Source",
            self.FUNCTION: "Function",
            self.EPHEMERAL_RESOURCE: "Ephemeral Resource",
            self.LIST_RESOURCE: "List Resource",
            self.STATE_STORE: "State Store",
            self.ACTION: "Action",
            self.PROVIDER: "Provider",
        }[self]

    @property
    def plural_name(self) -> str:
        """Get the plural display name used for section headings and nav."""
        return {
            self.RESOURCE: "Resources",
            self.DATA_SOURCE: "Data Sources",
            self.FUNCTION: "Functions",
            self.EPHEMERAL_RESOURCE: "Ephemeral Resources",
            self.LIST_RESOURCE: "List Resources",
            self.STATE_STORE: "State Stores",
            self.ACTION: "Actions",
            self.PROVIDER: "Providers",
        }[self]

    @property
    def output_subdir(self) -> str:
        """Get the output subdirectory name for Terraform Registry structure."""
        return {
            self.RESOURCE: "resources",
            self.DATA_SOURCE: "data-sources",
            self.FUNCTION: "functions",
            self.EPHEMERAL_RESOURCE: "ephemeral-resources",
            self.LIST_RESOURCE: "list-resources",
            self.STATE_STORE: "state-stores",
            self.ACTION: "actions",
            self.PROVIDER: "providers",
        }[self]

    @property
    def source_package(self) -> str:
        """Get the source sub-package a component of this type lives in.

        Used to infer a bundle's type from the path of its .plating directory.
        """
        return {
            self.RESOURCE: "resources",
            self.DATA_SOURCE: "data_sources",
            self.FUNCTION: "functions",
            self.EPHEMERAL_RESOURCE: "ephemerals",
            self.LIST_RESOURCE: "list_resources",
            self.STATE_STORE: "state_stores",
            self.ACTION: "actions",
            self.PROVIDER: "providers",
        }[self]

    @property
    def example_filename(self) -> str:
        """Get the conventional example filename for this type.

        Mirrors terraform-plugin-docs, which looks for a per-type filename
        rather than a generic one -- notably list resources, whose examples are
        query files rather than configuration.
        """
        return {
            self.RESOURCE: "resource.tf",
            self.DATA_SOURCE: "data-source.tf",
            self.FUNCTION: "function.tf",
            self.EPHEMERAL_RESOURCE: "ephemeral-resource.tf",
            self.LIST_RESOURCE: "list-resource.tfquery.hcl",
            self.STATE_STORE: "state-store.tf",
            self.ACTION: "action.tf",
            self.PROVIDER: "provider.tf",
        }[self]

    @property
    def example_suffix(self) -> str:
        """Get the file suffix an example for this type must carry.

        Only list resources differ: their examples are query files, which
        Terraform will not read from a .tf file.
        """
        _, _, suffix = self.example_filename.partition(".")
        return f".{suffix}"

    @property
    def is_schema_backed(self) -> bool:
        """Whether this type documents an attribute schema.

        Functions carry a signature instead of a block schema; every other
        component type renders a schema table.
        """
        return self is not ComponentType.FUNCTION

    @classmethod
    def documentable(cls) -> list["ComponentType"]:
        """Component types rendered into per-type documentation directories.

        Ordered as the docs and navigation should present them. PROVIDER is
        excluded: it renders to a single index page, not a directory.
        """
        return [
            cls.RESOURCE,
            cls.DATA_SOURCE,
            cls.FUNCTION,
            cls.EPHEMERAL_RESOURCE,
            cls.LIST_RESOURCE,
            cls.ACTION,
            cls.STATE_STORE,
        ]

    @classmethod
    def from_value(cls, value: str) -> "ComponentType":
        """Resolve a component type from its dimension name.

        Accepts the registry dimension ("ephemeral_resource") and the docs
        directory name ("ephemeral-resources") alike, so CLI input and
        discovered paths can both be normalised through one entry point.
        """
        normalised = value.strip().lower().replace("-", "_")
        for member in cls:
            if member.value == normalised or member.output_subdir.replace("-", "_") == normalised:
                return member
        raise ValueError(f"Unknown component type: {value}")


@define
class ArgumentInfo:
    """Information about a function argument."""

    name: str
    type: str
    description: str = ""
    required: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "required": self.required,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ArgumentInfo":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            type=data.get("type", ""),
            description=data.get("description", ""),
            required=data.get("required", True),
        )


@define
class SchemaInfo:
    """Structured schema information."""

    description: str = ""
    attributes: dict[str, dict[str, Any]] = field(factory=dict)
    blocks: dict[str, dict[str, Any]] = field(factory=dict)
    test_only: bool = False
    component_of: str | None = None

    @classmethod
    def from_dict(cls, schema_dict: dict[str, Any]) -> "SchemaInfo":
        """Create SchemaInfo from a raw schema dictionary."""
        if not schema_dict:
            return cls()

        block = schema_dict.get("block", {})
        return cls(
            description=schema_dict.get("description", ""),
            attributes=block.get("attributes", {}),
            blocks=block.get("block_types", {}),
            test_only=schema_dict.get("test_only", False),
            component_of=schema_dict.get("component_of"),
        )

    def to_markdown(self) -> str:  # noqa: C901
        """Convert schema to markdown format."""
        if not self.attributes and not self.blocks:
            return ""

        lines = ["## Schema", ""]

        # Group attributes by type
        required_attrs = []
        optional_attrs = []
        computed_attrs = []

        for attr_name, attr_def in self.attributes.items():
            attr_type = self._format_type(attr_def.get("type"))
            description = attr_def.get("description", "")

            if attr_def.get("required"):
                required_attrs.append((attr_name, attr_type, description))
            elif attr_def.get("computed") and not attr_def.get("optional"):
                computed_attrs.append((attr_name, attr_type, description))
            else:
                optional_attrs.append((attr_name, attr_type, description))

        # Format sections
        for heading, attrs in (
            ("### Required", required_attrs),
            ("### Optional", optional_attrs),
            ("### Read-Only", computed_attrs),
        ):
            if not attrs:
                continue
            lines.extend([heading, ""])
            for name, type_str, desc in attrs:
                # An undocumented attribute gets no trailing dash to hang off.
                entry = f"- `{name}` ({type_str})"
                lines.append(f"{entry} - {desc}" if desc else entry)
            lines.append("")

        # Handle nested blocks
        if self.blocks:
            lines.extend(["### Blocks", ""])
            for block_name, block_def in self.blocks.items():
                max_items = block_def.get("max_items", 0)
                if max_items == 1:
                    lines.append(f"- `{block_name}` (Optional)")
                else:
                    lines.append(f"- `{block_name}` (Optional, List)")
            lines.append("")

        return "\n".join(lines)

    # cty type names as they appear on the wire, mapped to the spellings
    # terraform-plugin-docs publishes to the registry.
    _TYPE_DISPLAY_NAMES: ClassVar[dict[str, str]] = {
        "string": "String",
        "bool": "Boolean",
        "number": "Number",
        "dynamic": "Dynamic",
    }

    def _format_type(self, type_info: Any) -> str:
        """Format type information to human-readable string."""
        if not type_info:
            return "String"

        if isinstance(type_info, str):
            return self._TYPE_DISPLAY_NAMES.get(type_info, type_info.title())

        if isinstance(type_info, list) and len(type_info) >= 2:
            container_type = type_info[0]
            element_type = type_info[1]

            if container_type == "list":
                return f"List of {self._format_type(element_type)}"
            elif container_type == "set":
                return f"Set of {self._format_type(element_type)}"
            elif container_type == "map":
                return f"Map of {self._format_type(element_type)}"
            elif container_type == "object":
                return "Object"

        return "Dynamic"


class PlatingCLIContext(CLIContext):
    """Type-safe context for plating operations extending foundation.Context."""

    def __init__(
        self,
        name: str = "",
        component_type: ComponentType = ComponentType.RESOURCE,
        provider_name: str = "",
        description: str = "",
        schema: SchemaInfo | None = None,
        examples: dict[str, str] | None = None,
        signature: str | None = None,
        arguments: list[ArgumentInfo] | None = None,
        global_partials_dir: Path | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.name = name
        self.component_type = component_type
        self.provider_name = provider_name
        self.description = description
        self.schema = schema
        self.examples = examples or {}
        self.signature = signature
        self.arguments = arguments
        self.global_partials_dir = global_partials_dir

    def to_dict(self, include_sensitive: bool = False) -> dict[str, Any]:
        """Convert to dictionary for template rendering."""
        base_dict = super().to_dict(include_sensitive=include_sensitive)
        plating_dict = {
            "name": self.name,
            "component_type": self.component_type.display_name,
            "provider_name": self.provider_name,
            "description": self.description,
            "examples": self.examples,
        }

        if self.schema:
            plating_dict["schema_markdown"] = self.schema.to_markdown()

        if self.signature:
            plating_dict["signature_markdown"] = self.signature

        if self.arguments:
            plating_dict["arguments_markdown"] = "\n".join(
                f"- `{arg.name}` ({arg.type}) - {arg.description}" for arg in self.arguments
            )

        # Include global_partials_dir if set (needed for template rendering)
        if self.global_partials_dir:
            plating_dict["global_partials_dir"] = str(self.global_partials_dir)

        return {**base_dict, **plating_dict}

    @property
    def component_set_context(self) -> dict[str, Any]:
        """Get context specific to ComponentSet operations."""
        return {
            "is_set_operation": hasattr(self, "_is_set_operation") and self._is_set_operation,
            "set_name": getattr(self, "_set_name", ""),
            "domains": getattr(self, "_domains", []),
            "set_metadata": getattr(self, "_set_metadata", {}),
        }

    def set_component_set_context(
        self, set_name: str, domains: list[str], set_metadata: dict[str, Any] | None = None
    ) -> None:
        """Set context for ComponentSet operations."""
        self._is_set_operation = True
        self._set_name = set_name
        self._domains = domains
        self._set_metadata = set_metadata or {}

    @classmethod
    def from_dict(cls, data: dict[str, Any], source: Any = None) -> "PlatingCLIContext":  # noqa: C901
        """Create context from dictionary.

        Args:
            data: Dictionary with context values
            source: Source of the configuration data (ignored for compatibility)

        Returns:
            New PlatingCLIContext instance
        """
        # Extract plating-specific fields
        name = data.get("name", "")
        provider_name = data.get("provider_name", "")
        description = data.get("description", "")
        examples = data.get("examples", {})
        signature = data.get("signature")

        # Handle component_type conversion
        component_type = ComponentType.RESOURCE  # default
        if "component_type" in data:
            comp_type = data["component_type"]
            if isinstance(comp_type, str):
                # Try to find by display name or value
                for ct in ComponentType:
                    if ct.display_name == comp_type or ct.value == comp_type:
                        component_type = ct
                        break
            else:
                component_type = comp_type

        # Handle arguments
        arguments = None
        if "arguments" in data:
            args_data = data["arguments"]
            if isinstance(args_data, list):
                arguments = [ArgumentInfo.from_dict(arg) for arg in args_data]

        # Get parent class fields (log_level, debug, etc.)
        parent_kwargs = {}
        parent_field_names = {
            "log_level",
            "profile",
            "debug",
            "json_output",
            "config_file",
            "log_file",
            "log_format",
            "no_color",
            "no_emoji",
        }
        for key in parent_field_names:
            if key in data:
                parent_kwargs[key] = data[key]

        # Handle Path conversions for parent fields
        if parent_kwargs.get("config_file"):
            parent_kwargs["config_file"] = Path(parent_kwargs["config_file"])
        if parent_kwargs.get("log_file"):
            parent_kwargs["log_file"] = Path(parent_kwargs["log_file"])

        # Create instance with all fields
        return cls(
            name=name,
            component_type=component_type,
            provider_name=provider_name,
            description=description,
            examples=examples,
            signature=signature,
            arguments=arguments,
            **parent_kwargs,
        )

    def save_context(self, path: Path) -> None:
        """Save context to file using foundation's config management."""
        self.save_config(path)

    @classmethod
    def load_context(cls, path: Path) -> "PlatingCLIContext":
        """Load context from file using foundation's config management."""
        # Load the JSON data and create instance from it
        if path.exists():
            data = json.loads(path.read_text())
            return cls.from_dict(data)

        # Return default instance if file doesn't exist
        return cls()


@define
class AdornResult:
    """Result from adorn operations."""

    components_processed: int = 0
    templates_generated: int = 0
    examples_created: int = 0
    errors: list[str] = field(factory=list)

    @property
    def success(self) -> bool:
        """Whether the operation succeeded."""
        return len(self.errors) == 0


@define
class PlateResult:
    """Result from plate operations."""

    bundles_processed: int = 0
    files_generated: int = 0
    duration_seconds: float = 0.0
    errors: list[str] = field(factory=list)
    output_files: list[Path] = field(factory=list)

    @property
    def success(self) -> bool:
        """Whether the operation succeeded."""
        return len(self.errors) == 0


@define
class ValidationResult:
    """Result from validation operations with markdown linting support."""

    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration_seconds: float = 0.0
    failures: dict[str, str] = field(factory=dict)
    errors: list[str] = field(factory=list)  # General errors
    lint_errors: list[str] = field(factory=list)  # Markdown linting errors
    terraform_version: str = ""

    @property
    def success(self) -> bool:
        """Whether all validations passed."""
        return self.failed == 0 and len(self.lint_errors) == 0 and len(self.errors) == 0


@define
class SetOperationResult:
    """Result from ComponentSet operations."""

    set_name: str = ""
    operation: str = ""  # "adorn", "plate", "validate", "generate_all_domains"
    domains_processed: int = 0
    components_processed: int = 0
    files_generated: int = 0
    duration_seconds: float = 0.0
    errors: list[str] = field(factory=list)
    domain_results: dict[str, Any] = field(factory=dict)  # Domain-specific results

    @property
    def success(self) -> bool:
        """Whether the operation succeeded."""
        return len(self.errors) == 0

    def add_domain_result(self, domain: str, result: Any) -> None:
        """Add a domain-specific result."""
        self.domain_results[domain] = result

    def get_domain_result(self, domain: str) -> Any | None:
        """Get result for a specific domain."""
        return self.domain_results.get(domain)

    def get_total_files_generated(self) -> int:
        """Get total files generated across all domains."""
        total = self.files_generated

        for result in self.domain_results.values():
            if hasattr(result, "files_generated"):
                total += result.files_generated

        return total

    def get_all_errors(self) -> list[str]:
        """Get all errors including domain-specific ones."""
        all_errors = self.errors.copy()

        for domain, result in self.domain_results.items():
            if hasattr(result, "errors"):
                for error in result.errors:
                    all_errors.append(f"{domain}: {error}")

        return all_errors


# Alias for backward compatibility and shorter imports
PlatingContext = PlatingCLIContext

# 🍽️📖🔚
