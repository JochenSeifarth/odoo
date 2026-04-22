# Odoo Development Agent Instructions

This file provides essential guidance for AI coding agents working on the Odoo codebase. It focuses on project-specific patterns, conventions, and setup that enable immediate productivity.

## Development Environment Setup

- **Python Version**: 3.10+ required
- **Database**: PostgreSQL (local Unix socket connection)
- **Virtual Environment**: Use `venv_odoo` in project root
- **Dependencies**: Install via `pip install -r requirements.txt`
- **Configuration**: Use `rya-odoo-DEV.conf` for development (auto-reload enabled)

## Key Commands

### Database Management
- Initialize: `./odoo-bin db init <dbname> --with-demo`
- Upgrade modules: `./odoo-bin -c rya-odoo-DEV.conf -u module1,module2 --stop-after-init`
- Drop: `./odoo-bin db drop <dbname>`

### Testing
- Run tests: `./odoo-bin shell -d <dbname>` then `run_tests(env, test_tags=['standard'])`
- Unit tests require `workers=0` in config

### Development Server
- Start: `./odoo-bin -c rya-odoo-DEV.conf`
- Auto-reload enabled in dev config

## Architecture Overview

### Core Structure
- **Framework**: `/odoo/` contains ORM, CLI, web framework
- **Modules**: `/addons/` contains 600+ business modules
- **Custom Module**: `event_rya` extends event management with geolocation and pricing

### Model Patterns
- Inherit from `models.Model`
- Use `_inherit` for extension, `_name` for new models
- Declarative fields with `fields.Type(...)`
- Computed fields require `@api.depends('field1', 'field2')`
- Constraints: `@api.constrains('field')`
- UI reactions: `@api.onchange('field')`

### View System
- XML-based: Form, Tree, Kanban, Search
- Inheritance: `inherit_id="module.view_id"` with XPath modifications
- Widgets: many2one, kanban_state, badge, etc.

### Security
- Access control via `security/ir.model.access.csv`
- Record rules with domain filtering
- Multi-company support with `company_id` context

## Coding Conventions

### Imports
- Order: future → stdlib → third-party → odoo → local
- Use `from __future__ import annotations` for type hints

### Module Structure
- `__manifest__.py`: Dependencies, data files, assets
- Models in `models/`, views in `views/`
- Security rules in `security/`
- Tests in `tests/test_*.py`

### Patterns
- Mixins for cross-cutting concerns (mail.thread, image.mixin)
- Domain-based queries: `[('field', 'operator', value)]`
- RecordSet operations: `.mapped()`, `.filtered()`, `.sorted()`

## Common Pitfalls

- Command option order matters for `odoo-bin db`
- Always activate venv before running scripts
- Tests require `workers=0` (single-threaded)
- Include both `at_install` and `post_install` test tags
- Master password required for `--stop-after-init`
- PostgreSQL socket connection assumes local server

## Quality Standards

- Linter: Ruff (config in `ruff.toml`)
- Line length: Not enforced (excluded from ruff)
- Typed imports encouraged

## Documentation Links

- [Odoo Developer Tutorials](https://www.odoo.com/documentation/master/developer/howtos.html)
- [Coding Guidelines](https://www.odoo.com/documentation/latest/contributing/development/coding_guidelines.html)
- [Contribution Wiki](https://github.com/odoo/odoo/wiki/Contributing)
- [Local README](README.md)
- [Contributing Guide](CONTRIBUTING.md)

## Key Reference Files

- Example models: `addons/crm/models/crm_lead.py`
- View inheritance: Any `views/*.xml` in addons
- Security: `addons/*/security/ir.model.access.csv`
- Tests: `addons/*/tests/test_*.py`
- ORM source: `odoo/orm/models.py`, `odoo/orm/fields.py`</content>
<parameter name="filePath">/home/jochen/git/odoo/AGENTS.md