# pilot-langgraph-mcp-cli

*Read this in other languages: [English](README.md), [한국어](README.ko.md)*

A LangGraph-based chatbot CLI tool using OpenAI API with MCP (Model Context Protocol) support.

## Key Features

- **Interactive Chatbot**: Real-time conversation with AI
- **Streaming Response**: Real-time response output with real-time tool usage tracking
- **MCP Server Support**: Extensible tool system via Model Context Protocol
- **Tool Registry System**: Centralized tool management and registration
- **Enhanced DateTime Tools**: Built-in date/time tools with security validation
- **Workflow Visualization**: Export LangGraph workflow as Mermaid diagrams with tool information
- **Real-time Tool Tracking**: Live display of tool execution with debug mode support
- **Configuration Management**: Flexible configuration management
- **Comprehensive E2E Testing**: Complete CLI option coverage with automated testing

## Installation & Setup

**Requirements**: Python 3.12+

### 1. Package Installation

```bash
# Install in development mode
pip install -e .

# Or use uv (recommended)
uv pip install -e .
```

### 2. Configuration File Setup

```bash
# Generate configuration file template
my-mcp setup

# Or create manually
cp settings.sample.yaml settings.yaml
```

### 3. OpenAI API Key Configuration

Edit the `settings.yaml` file to configure your OpenAI API key:

```yaml
openai:
  api_key: "your-actual-openai-api-key"
  model: "gpt-4o-mini"
  temperature: 0.7
  max_tokens: 1000
  streaming: true

# Optional MCP server configuration
mcp:
  servers:
    # Add your MCP servers here
```

## Usage

### Starting the Chatbot

```bash
# Start interactive chatbot
my-mcp chat

# One-time question
my-mcp chat "Hello, how's the weather today?"

# Disable streaming
my-mcp chat --no-stream

# Enable debug mode (shows tool IDs and workflow steps)
my-mcp chat --debug

# Save conversation
my-mcp chat --save
```

### Workflow Visualization

```bash
# Export graph structure as Mermaid diagram
my-mcp agent export

# Include AI auto-description with tool information
my-mcp agent export --ai-description

# Export as JSON format
my-mcp agent export --format json
```

### Other Commands

```bash
# Check information
my-mcp info

# Check version
my-mcp version

# Help
my-mcp --help
```

## Project Structure

```
pilot-langgraph-mcp-cli/
├── src/
│   ├── config.py              # Configuration management
│   ├── main.py                # CLI entry point
│   └── my_mcp/
│       ├── __init__.py
│       ├── logging.py         # Logging configuration
│       ├── agent/
│       │   ├── __init__.py
│       │   └── service.py     # LangGraph chatbot service
│       ├── mcp/               # MCP (Model Context Protocol) support
│       │   ├── __init__.py
│       │   ├── client.py      # MCP client implementation
│       │   ├── registry.py    # MCP server registry
│       │   └── server.py      # MCP server interface
│       ├── tools/             # Tool system
│       │   ├── __init__.py
│       │   ├── datetime_tools.py  # Enhanced datetime tools
│       │   └── registry.py    # Tool registry management
│       └── utils/
│           ├── __init__.py
│           ├── diagram_utils.py   # Workflow visualization with tool support
│           ├── markdown_utils.py
│           └── output_utils.py
├── settings.sample.yaml       # Configuration template
├── settings.yaml             # Actual configuration
├── pyproject.toml            # Project configuration
└── README.md
```

## Testing

This project includes comprehensive E2E testing for all CLI commands and option combinations.

### Running Tests

```bash
# Install test dependencies
make install-test-deps

# Run all E2E tests
make test

# Quick smoke test
make test-smoke

# Test specific commands
make test-chat      # Chat command tests
make test-agent     # Agent command tests
make test-basic     # Basic command tests
```

See [`tests/README.md`](tests/README.md) for detailed testing documentation.

## Development

### Key Dependencies

- `typer`: CLI framework
- `rich`: Terminal UI
- `dynaconf`: Configuration management
- `openai`: OpenAI API client
- `langgraph`: LangGraph workflow
- `langchain`: LangChain framework
- `langchain-mcp-adapters`: MCP integration for LangChain
- `mcp`: Model Context Protocol implementation
- `httpx`: HTTP client for MCP communication
- `loguru`: Logging library
- `jsonschema`: JSON schema validation

### Logging Configuration

You can configure logging in `settings.yaml`:

```yaml
logging:
  level: "INFO"
  format: "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>"
  file_enabled: false
  file_path: "logs/app.log"
```

## License

This project is distributed under the MIT License. 