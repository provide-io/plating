# Bundle Discovery Pattern for Foundation

> **Status:** 💡 Proposal
> **Date:** 2025-01-25
> **Implementation:** Not yet started
> **Discussion:** This is a forward-looking proposal for extracting plating's bundle discovery into foundation

## Overview

The `PlatingBundle` and `PlatingDiscovery` patterns from plating are generic and reusable for any packaged asset discovery. This could become a foundation module.

## Proposed Foundation Module: `provide.foundation.discovery`

### Core Classes

```python
@dataclass
class ResourceBundle:
    """Generic resource bundle for any packaged assets."""
    name: str
    bundle_dir: Path
    resource_type: str
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def assets_dir(self) -> Path:
        """Directory containing assets."""
        return self.bundle_dir / "assets"
    
    @property  
    def config_dir(self) -> Path:
        """Directory containing configuration."""
        return self.bundle_dir / "config"
    
    def load_assets(self) -> dict[str, str]:
        """Load all asset files as string content."""
        # Implementation similar to PlatingBundle.load_examples
        
    def load_metadata(self) -> dict[str, Any]:
        """Load bundle metadata from config files."""
        # Implementation for loading YAML/JSON metadata

class ResourceDiscovery:
    """Discover resource bundles from installed packages."""
    
    def __init__(self, package_pattern: str = "*.resources"):
        self.package_pattern = package_pattern
    
    def discover_bundles(self, resource_type: str | None = None) -> list[ResourceBundle]:
        """Discover all resource bundles from packages."""
        # Generic implementation for any package discovery
        
    def scan_directory(self, directory: Path) -> list[ResourceBundle]:
        """Scan a directory for resource bundles."""
        # Local directory scanning
```

### Usage Examples

```python
# For documentation generation (current plating use case)
from provide.foundation.discovery import ResourceDiscovery, ResourceBundle

discovery = ResourceDiscovery("*.components")  
doc_bundles = discovery.discover_bundles(resource_type="documentation")

# For plugin discovery
plugin_discovery = ResourceDiscovery("*.plugins")
plugins = plugin_discovery.discover_bundles(resource_type="extension")

# For template discovery  
template_discovery = ResourceDiscovery("*.templates")
templates = template_discovery.discover_bundles(resource_type="jinja2")
```

### Benefits

1. **Reusability**: Any project needing asset/resource discovery
2. **Standardization**: Common pattern across provide ecosystem
3. **Extensibility**: Support for different bundle types and metadata formats
4. **Performance**: Caching and optimization opportunities

### Migration Path

1. Extract plating's bundle logic to foundation
2. Update plating to use foundation's discovery module  
3. Provide backward compatibility adapters
4. Document migration guide for other projects

### Implementation Notes

- Support multiple asset directories per bundle
- Flexible metadata loading (YAML, JSON, TOML)
- Plugin hooks for custom bundle types
- Caching layer for performance
- Async discovery support for large package sets