# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Complete documentation overhaul with new structure:
  - `quick-start.md` - 5-minute getting started guide
  - `api-reference.md` - Clean, complete API documentation
  - `cli-reference.md` - Full CLI command reference with auto-detection
  - `registry-pattern.md` - Registry architecture documentation
  - `performance.md` - Performance optimization guide
  - `examples.md` - Complete working examples
  - `troubleshooting.md` - Common issues and solutions
- Foundation integration documentation with resilience patterns
- PlatingContext documentation as primary configuration method
- Grouped examples documentation and best practices
- Fixtures directory support documentation
- Complete error class hierarchy (8 error types)
- Component registry documentation
- Async-first architecture documentation

### Changed

- Restructured documentation for clarity and completeness
- Focused on end-state implementation (async-only)
- Updated all code examples to use modern async API
- Renamed `04-authoring-plating-bundles.md` to `authoring-bundles.md`
- Standardized template file extension to `.tmpl.md` throughout
- Updated bundle structure to include fixtures directory
- Enhanced error handling examples with all error classes

### Removed

- Deprecated API documentation (PlatingAdorner, PlatingDiscovery direct access)
- Migration guides (no backward compatibility needed)
- Old API.md replaced with clean api-reference.md
- Internal implementation details from public documentation
- Historical/proposed feature documentation moved to archive

### Fixed

- Corrected PlatingBundle import paths
- Fixed all async/await patterns in examples
- Corrected version format consistency (0.0.1000-0)
- Updated component type examples with correct syntax
- Fixed incorrect error class names in documentation

## [0.5.1] - 2026-08-21

### Fixed

- **Generated nav sections are lists, not mappings.** mkdocs takes a nav section as a list of single-key mappings; the generator emitted one mapping of many keys. It passes `Nav().validate()`, so nothing caught it, but the build refuses it -- "Expected nav to be a list, got dict with keys (...)" -- and under `--strict` that aborts. terraform-provider-pyvider could not build its documentation at all.
- **`mkdocs.yml` no longer comes back with escaped non-ASCII.** The generator rewrites the caller's whole file, and `yaml.dump` escapes by default, so a copyright line reading `©2024-2025 provide.io llc<br/>🛠️ with 💚` returned as `\U0001F6E0` escapes: valid YAML, unreadable in a hand-maintained file.

## [0.5.0] - 2026-08-20

### Added

- **Documentation for the four tfprotov6.11 component types.** Ephemeral resources, list resources, state stores and actions each get their own registry directory (`ephemeral-resources/`, `list-resources/`, `state-stores/`, `actions/`), template builder, example builder and nav section, following terraform-plugin-docs' layout.
- `ComponentType` gained the four members plus the properties that drive them: `plural_name`, `output_subdir`, `source_package`, `example_filename`, `example_suffix`, `is_schema_backed` and `documentable()`.

### Fixed

- **Schema extraction produced empty pages.** The extractor called `discover_components("pyvider.components")` -- a module path where an entry-point group was wanted -- so every schema came back empty. It now drives pyvider's own `ComponentDiscovery` into a fresh registry and falls back to entry points.
- **cty types rendered as `{}`.** Attribute types went through `attrs.asdict`, which flattens a cty type into nothing useful. They now go through `encode_cty_type_to_wire_json`, so `bool` renders as `Boolean`.
- **`--global-partials-dir` produced one file instead of every file.** A `Path / str` TypeError was caught by an `except` too narrow to see it, and the failure was silent.
- **`adorn` would overwrite hand-written templates.** `_is_adorned()` did not discount the provider prefix, so an existing bundle read as absent. It also reported "all components already have bundles" when the hub returned nothing at all, because an empty result short-circuited the registry fallback.

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
