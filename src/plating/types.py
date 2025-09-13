#
# plating/types.py
#
"""Type definitions for the plating system with foundation integration."""

import json
from enum import Enum
from pathlib import Path
from typing import Any

from attrs import define, field
from provide.foundation import CLIContext


class ComponentType(Enum):
    """Type-safe component types."""
    RESOURCE = "resource"
    DATA_SOURCE = "data_source" 
    FUNCTION = "function"
    PROVIDER = "provider"
    
    # Multi-domain support
    K8S_RESOURCE = "k8s_resource"
    K8S_OPERATOR = "k8s_operator"
    K8S_CRD = "k8s_crd"
    
    CF_RESOURCE = "cf_resource"
    CF_STACK = "cf_stack"
    CF_MACRO = "cf_macro"
    
    API_ENDPOINT = "api_endpoint"
    API_SCHEMA = "api_schema"
    API_CLIENT = "api_client"
    
    GUIDE = "guide"
    TUTORIAL = "tutorial"
    REFERENCE = "reference"
    
    @property
    def display_name(self) -> str:
        """Get the formatted display name."""
        return {
            # Terraform
            self.RESOURCE: "Resource",
            self.DATA_SOURCE: "Data Source", 
            self.FUNCTION: "Function",
            self.PROVIDER: "Provider",
            
            # Kubernetes
            self.K8S_RESOURCE: "Kubernetes Resource",
            self.K8S_OPERATOR: "Kubernetes Operator",
            self.K8S_CRD: "Custom Resource Definition",
            
            # CloudFormation
            self.CF_RESOURCE: "CloudFormation Resource",
            self.CF_STACK: "CloudFormation Stack",
            self.CF_MACRO: "CloudFormation Macro",
            
            # API
            self.API_ENDPOINT: "API Endpoint",
            self.API_SCHEMA: "API Schema",
            self.API_CLIENT: "API Client",
            
            # Documentation
            self.GUIDE: "Guide",
            self.TUTORIAL: "Tutorial",
            self.REFERENCE: "Reference"
        }[self]
        
    @property
    def output_subdir(self) -> str:
        """Get the output subdirectory name."""
        return {
            # Terraform
            self.RESOURCE: "resources",
            self.DATA_SOURCE: "data_sources",
            self.FUNCTION: "functions", 
            self.PROVIDER: "providers",
            
            # Kubernetes
            self.K8S_RESOURCE: "k8s_resources",
            self.K8S_OPERATOR: "k8s_operators",
            self.K8S_CRD: "k8s_crds",
            
            # CloudFormation
            self.CF_RESOURCE: "cf_resources",
            self.CF_STACK: "cf_stacks",
            self.CF_MACRO: "cf_macros",
            
            # API
            self.API_ENDPOINT: "api_endpoints",
            self.API_SCHEMA: "api_schemas",
            self.API_CLIENT: "api_clients",
            
            # Documentation
            self.GUIDE: "guides",
            self.TUTORIAL: "tutorials",
            self.REFERENCE: "reference"
        }[self]


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
            "required": self.required
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ArgumentInfo":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            type=data.get("type", ""),
            description=data.get("description", ""),
            required=data.get("required", True)
        )


@define
class SchemaInfo:
    """Structured schema information."""
    description: str = ""
    attributes: dict[str, dict] = field(factory=dict)
    blocks: dict[str, dict] = field(factory=dict)
    
    @classmethod
    def from_dict(cls, schema_dict: dict) -> "SchemaInfo":
        """Create SchemaInfo from a raw schema dictionary."""
        if not schema_dict:
            return cls()
            
        block = schema_dict.get("block", {})
        return cls(
            description=schema_dict.get("description", ""),
            attributes=block.get("attributes", {}),
            blocks=block.get("block_types", {})
        )
        
    def to_markdown(self) -> str:
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
        if required_attrs:
            lines.extend(["### Required", ""])
            for name, type_str, desc in required_attrs:
                lines.append(f"- `{name}` ({type_str}) - {desc}")
            lines.append("")
            
        if optional_attrs:
            lines.extend(["### Optional", ""])
            for name, type_str, desc in optional_attrs:
                lines.append(f"- `{name}` ({type_str}) - {desc}")
            lines.append("")
            
        if computed_attrs:
            lines.extend(["### Read-Only", ""])
            for name, type_str, desc in computed_attrs:
                lines.append(f"- `{name}` ({type_str}) - {desc}")
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
    
    def _format_type(self, type_info) -> str:
        """Format type information to human-readable string."""
        if not type_info:
            return "String"
            
        if isinstance(type_info, str):
            return type_info.title()
            
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
        **kwargs
    ):
        super().__init__(**kwargs)
        self.name = name
        self.component_type = component_type
        self.provider_name = provider_name
        self.description = description
        self.schema = schema
        self.examples = examples or {}
        self.signature = signature
        self.arguments = arguments
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for template rendering."""
        base_dict = super().to_dict()
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
            plating_dict["signature"] = self.signature
            
        if self.arguments:
            plating_dict["arguments"] = "\n".join(
                f"- `{arg.name}` ({arg.type}) - {arg.description}" 
                for arg in self.arguments
            )
        
        return {**base_dict, **plating_dict}
    
    @property
    def component_set_context(self) -> dict[str, Any]:
        """Get context specific to ComponentSet operations."""
        return {
            "is_set_operation": hasattr(self, '_is_set_operation') and self._is_set_operation,
            "set_name": getattr(self, '_set_name', ""),
            "domains": getattr(self, '_domains', []),
            "set_metadata": getattr(self, '_set_metadata', {})
        }
    
    def set_component_set_context(
        self,
        set_name: str,
        domains: list[str],
        set_metadata: dict[str, Any] | None = None
    ) -> None:
        """Set context for ComponentSet operations."""
        self._is_set_operation = True
        self._set_name = set_name
        self._domains = domains
        self._set_metadata = set_metadata or {}
    
    def from_dict(self, data: dict[str, Any]) -> "PlatingCLIContext":
        """Update from dictionary."""
        # Call parent's from_dict first
        super().from_dict(data)
        
        # Set our custom fields
        self.name = data.get("name", "")
        if "component_type" in data:
            # Handle both string and enum values
            comp_type = data["component_type"]
            if isinstance(comp_type, str):
                # Try to find by display name or value
                for ct in ComponentType:
                    if ct.display_name == comp_type or ct.value == comp_type:
                        self.component_type = ct
                        break
            else:
                self.component_type = comp_type
        self.provider_name = data.get("provider_name", "")
        self.description = data.get("description", "")
        self.examples = data.get("examples", {})
        self.signature = data.get("signature")
        if "arguments" in data:
            args_data = data["arguments"]
            if isinstance(args_data, list):
                self.arguments = [ArgumentInfo.from_dict(arg) for arg in args_data]
        return self
    
    def save_context(self, path: Path) -> None:
        """Save context to file using foundation's config management."""
        self.save_config(path)
    
    @classmethod
    def load_context(cls, path: Path) -> "PlatingCLIContext":
        """Load context from file using foundation's config management."""
        import json
        
        context = cls()
        
        # Load the JSON data and apply it
        if path.exists():
            data = json.loads(path.read_text())
            context.from_dict(data)
        
        return context


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
            if hasattr(result, 'files_generated'):
                total += result.files_generated
        
        return total
    
    def get_all_errors(self) -> list[str]:
        """Get all errors including domain-specific ones."""
        all_errors = self.errors.copy()
        
        for domain, result in self.domain_results.items():
            if hasattr(result, 'errors'):
                for error in result.errors:
                    all_errors.append(f"{domain}: {error}")
        
        return all_errors


# Alias for backward compatibility and shorter imports
PlatingContext = PlatingCLIContext

# 🍲🏷️✨⚡