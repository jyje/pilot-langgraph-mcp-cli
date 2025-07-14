# CLI E2E Testing

Complete E2E testing system for `my-mcp` CLI commands and option combinations.

## Goals

- **100% CLI option coverage** - Test all CLI options and combinations
- **Regression prevention** - Ensure new features don't break existing ones
- **Stability assurance** - All CLI commands work as expected

## Directory Structure

```
tests/
├── __init__.py              # Test package
├── conftest.py              # pytest configuration and fixtures
├── e2e/                     # E2E test directory
│   ├── __init__.py
│   ├── test_chat_command.py         # chat command tests
│   ├── test_agent_export_command.py # agent export tests
│   └── test_basic_commands.py       # info, version, setup tests
└── README.md                # This file
```

## Quick Start

### Install Dependencies

```bash
make install-test-deps
```

### Run Tests

```bash
# All E2E tests
make test

# Specific commands
make test-chat      # chat command only
make test-agent     # agent command only
make test-basic     # info, version, setup

# Quick smoke test
make test-smoke
```

## Test Commands

| Command | Description |
|---------|-------------|
| `make test` | Run all E2E tests |
| `make test-smoke` | Quick smoke tests |
| `make test-chat` | Chat command tests only |
| `make test-agent` | Agent export tests only |
| `make test-basic` | Basic command tests |
| `make test-coverage` | Tests with coverage |
| `make test-parallel` | Parallel execution |
| `make test-failed` | Re-run failed tests only |

## Test Coverage

### Commands Tested
- `my-mcp chat` - All option combinations (30+ test cases)
- `my-mcp agent export` - All option combinations (20+ test cases)
- `my-mcp info/version/setup` - Basic and global option combinations

### Options Tested
- Individual options: `--once`, `--no-stream`, `--debug`, `--save`, `--format`, `--output`
- Short options: `-f`, `-o`, `-v`, `-q`, `-c`
- Option combinations: 2, 3, 4+ options together
- Global options: `--verbose`, `--quiet`, `--output`, `--config`
- Error cases: Invalid values, non-existent files
- Edge cases: Empty values, special characters, unicode

## Adding New Features

When adding new CLI commands or options, **E2E tests are mandatory**.

### New Command Checklist
- [ ] Create `tests/e2e/test_[command]_command.py`
- [ ] Test all individual options
- [ ] Test all option combinations
- [ ] Test global option combinations
- [ ] Test error cases
- [ ] Run `make test-e2e` to verify

### Existing Command Updates
- [ ] Update corresponding test file
- [ ] Add tests for new option combinations
- [ ] Run regression tests

See `.cursor/rules/debug-rules.mdc` for detailed requirements.

## Fixtures

Common fixtures in `conftest.py`:
- `cli_runner` - Typer CLI test runner
- `temp_config_file` - Temporary config file
- `mock_mcp_servers` - MCP server mocking
- `mock_agent_service` - Agent service mocking
- `temp_output_dir` - Temporary output directory

Auto-mocked:
- Settings file check (`check_settings`)
- OpenAI API calls
- MCP server connections

---

**Core principle: New feature → E2E test required** 