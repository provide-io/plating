# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- Package renamed from "garnish" to "plating"
- Terminology updated: "dress" operations renamed to "adorn"
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

## [0.1.0] - 2025-01-XX

Initial pre-release version extracted from tofusoup project.