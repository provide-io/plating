# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0] - 2026-08-24

### Added

- **An example can declare what it needs in order to run.** `example.tf` is described by `example.meta.toml`, and requirements shared by every example in a bundle go in one `examples/_requirements.meta.toml`. Requirements are not one-dimensional -- a Terraform floor, an OpenTofu incompatibility, an extra `init` flag, an environment variable, network egress -- so a filename convention could only ever encode one of them and leave the rest undeclared. That is the state this replaces: nothing could tell `soup stir` that the filesystem state store needs `-enable-pluggable-state-storage-experiment`, and a shared-secret prerequisite survived only as hand-written prose in a doc template.

  Requirements accumulate and are never cancelled: a per-example sidecar can add a constraint or extend a list, but cannot declare itself exempt from one its bundle imposes. A runner that wrongly skips loses one result; one that wrongly runs reports a failure indistinguishable from a real defect.

  Sidecars are copied verbatim into the compiled example tree rather than re-serialised, because whatever runs those directories never sees the `.plating` bundle -- and a parse/dump round-trip would drop the comments explaining why each requirement exists. The suffix sits outside `EXAMPLE_FILE_PATTERNS`, so a sidecar is never mistaken for an example and a bundle holding only one still reports no examples.

  Reading is deliberately forgiving: missing and malformed both mean "declares nothing". These describe an example; they are not a gate, and failing a docs build over unparseable metadata trades a small problem for a larger one.

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

## [0.5.4] - 2026-08-21

### Fixed

- **Every component type's examples are found and written out.** The compiler recognised two block keywords, `resource` and `data`, and globbed only `*.tf`. An action, an ephemeral resource, a list resource and a state store therefore each looked like a bundle referencing nothing: the directory was created and left empty, and `soup stir` counted it as a pass because an empty directory applies nothing. It now knows `action`, `ephemeral`, `list` and `state_store`, reads `*.tfquery.hcl` as well, matches on the component names a bundle documents rather than its directory name, keeps a state store's `terraform` block instead of stripping it, and writes a query file back with its own extension.
- **A generated `provider.tf` no longer guesses an argument name.** For a test-only component the compiler wrote `provider_testmode = true` into the provider block. No provider publishes an attribute by that name -- pyvider's is `pyvider_testmode` -- and Terraform refuses an entire configuration over one argument it does not recognise, so five of terraform-provider-pyvider's examples failed with "Unsupported argument" from the day they were generated and had never once run. An argument is emitted now only when the caller passes `provider_attributes` and the name is in it; otherwise the block carries a comment saying the provider must be started with `PYVIDER_TESTMODE=true`, which is the mechanism that actually works and the one the conformance suite uses.

## [0.5.3] - 2026-08-21

Never published. No tag, no release and no PyPI upload carries this number -- the sequence goes 0.5.2 straight to 0.5.4. The change below is not lost: it shipped inside 0.5.4, whose tag contains both `0df28a6` and `caaaf5d`. Recorded here rather than renumbered, so the history matches what was actually released.

### Added

- **A test-only component's page says it is unreachable.** `subcategory: "Test Mode"` groups these pages in the navigation, which tells a reader they are grouped -- not that a provider started normally never publishes them. terraform-provider-pyvider shipped fourteen such components (every action, ephemeral resource, list resource and state store it had) and nothing on the page said `tofu providers schema` would show none of them. The notice is injected after the first heading, before the example a reader would otherwise copy, as a plain markdown blockquote the registry can render.

## [0.5.2] - 2026-08-21

### Fixed

- **Provider index links the file the renderer actually wrote.** The index stripped the provider prefix itself instead of going through `document_filename`, which is right for a resource and wrong for a function that genuinely carries one: `pyvider_nested_data_processor` is written to `functions/pyvider_nested_data_processor.md` while the index pointed at `functions/nested_data_processor.md`. Under `mkdocs --strict` one such link aborts the whole build. The navigation and the renderer already shared the rule; the index was the caller that never adopted it.

## [0.5.1] - 2026-08-21

### Fixed

- **Generated nav sections are lists, not mappings.** mkdocs takes a nav section as a list of single-key mappings; the generator emitted one mapping of many keys. It passes `Nav().validate()`, so nothing caught it, but the build refuses it -- "Expected nav to be a list, got dict with keys (...)" -- and under `--strict` that aborts. terraform-provider-pyvider could not build its documentation at all.
- **Every file read and write names its encoding.** Without one Python uses the locale default, which is cp1252 on Windows, and plating writes documentation full of emoji -- `mkdocs.yml` could not even be read back: `UnicodeDecodeError: 'charmap' codec can't decode byte 0x8f`. Six call sites in `nav_generator`, `linting`, `types` and the two `processor` modules.
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
