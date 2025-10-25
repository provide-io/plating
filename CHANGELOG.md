# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Foundation integration documentation section
- PlatingContext documentation in API reference
- Grouped examples documentation and best practices
- Fixtures directory support documentation
- Complete error class hierarchy documentation

### Changed
- Updated API documentation with correct imports and modern async API
- Fixed PlatingBundle initialization examples
- Standardized template file extension to `.tmpl.md` throughout docs
- Updated bundle structure to include fixtures directory
- Enhanced error handling examples with all error classes

### Removed
- Historical/proposed feature documentation moved to archive

### Fixed
- Corrected version format consistency (0.0.1000-0)
- Updated component type examples with correct syntax
- Fixed async/await patterns in code examples

## [0.0.1000-0] - 2025-10-25

### Added
- Initial release of plating documentation generation system
- Support for Terraform/OpenTofu provider documentation generation
- Automatic component discovery via pyvider.hub integration
- Jinja2 template processing with custom functions
- PlatingBundle system for managing documentation assets
- PlatingAdorner for automatic component decoration
- PlatingPlater for documentation rendering
- Async rendering pipeline support
- Schema extraction and markdown generation
- Example and fixture file management
- Template validation and linting integration
- UV package manager support and tooling

### Changed
- Line length standardized to 111 characters
- Modern Python typing throughout (dict, list, set instead of Dict, List, Set)

### Technical Details
- Python 3.11+ required
- Dependencies: jinja2, rich, pyvider ecosystem, provide-foundation
- Development tools: ruff (linting/formatting), mypy (type checking), pytest
- UV-based development workflow

### Documentation
- Comprehensive README with UV installation instructions
- CLAUDE.md development guidance
- End-to-end examples and test coverage
- Complete API reference documentation
- Authoring guide for plating bundles
- Future proposals directory for enhancement ideas

## [0.0.1000-0] - 2025-10-25

Initial pre-release version.