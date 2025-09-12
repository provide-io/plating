#
# plating/types.py
#
"""Type definitions for the plating system."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ComponentType(Enum):
    """Type-safe component types."""
    RESOURCE = "resource"
    DATA_SOURCE = "data_source" 
    FUNCTION = "function"
    PROVIDER = "provider"
    
    @property
    def display_name(self) -> str:
        """Get the formatted display name."""
        return {
            self.RESOURCE: "Resource",
            self.DATA_SOURCE: "Data Source", 
            self.FUNCTION: "Function",
            self.PROVIDER: "Provider"
        }[self]
        
    @property
    def output_subdir(self) -> str:
        """Get the output subdirectory name."""
        return {
            self.RESOURCE: "resources",
            self.DATA_SOURCE: "data_sources",
            self.FUNCTION: "functions", 
            self.PROVIDER: "providers"
        }[self]


@dataclass
class ArgumentInfo:
    """Information about a function argument."""
    name: str
    type: str
    description: str = ""
    required: bool = True


@dataclass 
class SchemaInfo:
    """Structured schema information."""
    description: str = ""
    attributes: dict[str, dict] = field(default_factory=dict)
    blocks: dict[str, dict] = field(default_factory=dict)
    
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


@dataclass
class PlatingContext:
    """Type-safe context for template rendering."""
    name: str
    component_type: ComponentType
    provider_name: str
    description: str = ""
    schema: SchemaInfo | None = None
    examples: dict[str, str] = field(default_factory=dict)
    
    # For functions specifically
    signature: str | None = None
    arguments: list[ArgumentInfo] | None = None
    
    def to_dict(self) -> dict[str, any]:
        """Convert to dictionary for template rendering."""
        result = {
            "name": self.name,
            "component_type": self.component_type.display_name,
            "provider_name": self.provider_name,
            "description": self.description,
            "examples": self.examples,
        }
        
        if self.schema:
            result["schema_markdown"] = self.schema.to_markdown()
            
        if self.signature:
            result["signature"] = self.signature
            
        if self.arguments:
            result["arguments"] = "\n".join(
                f"- `{arg.name}` ({arg.type}) - {arg.description}" 
                for arg in self.arguments
            )
            
        return result


@dataclass
class AdornResult:
    """Result from adorn operations."""
    components_processed: int
    templates_generated: int
    examples_created: int
    errors: list[str] = field(default_factory=list)
    
    @property
    def success(self) -> bool:
        """Whether the operation succeeded."""
        return len(self.errors) == 0


@dataclass 
class PlateResult:
    """Result from plate operations."""
    bundles_processed: int
    files_generated: int
    duration_seconds: float
    errors: list[str] = field(default_factory=list)
    output_files: list[Path] = field(default_factory=list)
    
    @property
    def success(self) -> bool:
        """Whether the operation succeeded."""
        return len(self.errors) == 0


@dataclass
class ValidationResult:
    """Result from validation operations."""
    total: int
    passed: int
    failed: int
    skipped: int = 0
    duration_seconds: float = 0.0
    failures: dict[str, str] = field(default_factory=dict)
    terraform_version: str = ""
    
    @property
    def success(self) -> bool:
        """Whether all validations passed."""
        return self.failed == 0


# 🍲🏷️✨