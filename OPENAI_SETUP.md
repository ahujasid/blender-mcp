# Using BlenderMCP with OpenAI Models

This guide explains how to use the `blender-mcp-openai` package to connect BlenderMCP with OpenAI models like GPT-4 instead of using Claude.

## Installation

Install the package:

```bash
pip install blender-mcp-openai
```

Or directly from the repository:

```bash
git clone https://github.com/yourusername/blender-mcp-openai.git
cd blender-mcp-openai
pip install -e .
```

## Prerequisites

1. Install the OpenAI Python library:
   ```bash
   pip install openai
   ```

2. Set up your OpenAI API key:
   - Set it as an environment variable: `export OPENAI_API_KEY=your_api_key_here`
   - Or pass it as a command-line argument (see below)

3. Make sure you have already set up BlenderMCP according to the main project instructions.

## Usage

### Method 1: Run the adapter directly

Simply run the adapter command, which will start the MCP server using OpenAI models:

```bash
blender-mcp-openai --model gpt-4
```

Optional arguments:
- `--model`: Specify the OpenAI model to use (default: gpt-4)
- `--api-key`: Directly provide your OpenAI API key
- `--temperature`: Set the temperature for model responses (default: 0.7)
- `--max-tokens`: Set the maximum number of tokens to generate
- `--system-prompt`: Provide a system prompt to prepend to conversations
- `--config-file`: Path to a configuration file
- `--log-level`: Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--log-file`: Path to a log file for output
- `--json-logs`: Output logs in JSON format

### Method 2: Use a configuration file

Create a `config.json` file:

```json
{
  "openai": {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2000,
    "system_prompt": "You are a Blender assistant, helping users with 3D modeling and animation tasks."
  },
  "log_level": "INFO",
  "log_file": "blender_mcp_openai.log"
}
```

Then run:

```bash
blender-mcp-openai --config-file config.json
```

### Method 3: Configure in Claude Desktop or Cursor

#### Claude Desktop

Create or update your `claude_desktop_config.json` file:

```json
{
  "mcpServers": {
    "blender": {
      "command": "blender-mcp-openai",
      "args": [
        "--model",
        "gpt-4",
        "--system-prompt",
        "You are a helpful Blender assistant."
      ]
    }
  }
}
```

#### Cursor

Create or update your `mcp.json` file:

```json
{
  "mcpServers": {
    "blender": {
      "command": "blender-mcp-openai",
      "args": [
        "--model",
        "gpt-4",
        "--system-prompt",
        "You are a helpful Blender assistant."
      ]
    }
  }
}
```

## Advanced Usage

### Programmatic Usage

You can use the adapter programmatically in your own Python code:

```python
from blender_mcp_openai import OpenAIAdapter
from blender_mcp_openai.config import OpenAIConfig

# Create a configuration
config = OpenAIConfig(
    model="gpt-4",
    temperature=0.7,
    system_prompt="You are a Blender assistant."
)

# Create the adapter
adapter = OpenAIAdapter(config)

# Send a chat message
response = adapter.chat([
    {"role": "user", "content": "Create a cube in Blender"}
])

print(response)

# Or with streaming
for chunk in adapter.chat(
    [{"role": "user", "content": "Create a cube in Blender"}],
    stream=True
):
    print(chunk, end="", flush=True)
```

## Troubleshooting

### Common Issues

1. **API Key Issues**: Make sure your OpenAI API key is set correctly.
   - Check that the `OPENAI_API_KEY` environment variable is set.
   - Or pass the API key directly with `--api-key`.

2. **Import Errors**: If you get import errors for the BlenderMCP module:
   - Make sure BlenderMCP is installed and accessible in your Python path.
   - The adapter will try to find the module in several locations.

3. **Tool Errors**: If tools fail to execute:
   - Check the log file for detailed error messages.
   - Make sure you have the latest version of BlenderMCP.

### Getting Help

If you encounter any issues, please:
1. Check the log file (if available).
2. Try running with `--log-level DEBUG` for more detailed information.
3. File an issue on the GitHub repository with the details of your problem.

## Legacy Support

For backward compatibility with the original single-file implementation, a legacy entry point is provided:

```bash
openai_adapter --model gpt-4
```

## Available Models

You can use any OpenAI chat model, including:
- `gpt-4`
- `gpt-4-turbo`
- `gpt-4o`
- `gpt-3.5-turbo`

## How It Works

The adapter:
1. Imports the original BlenderMCP server code 
2. Extracts the MCP tools and converts them to OpenAI function calling format
3. Provides an interface to send messages to OpenAI models
4. Handles tool calls by executing the original MCP functions

This approach maintains compatibility with the original project while minimizing modifications needed when the original project is updated.

## Updating

When the original BlenderMCP project is updated, you typically won't need to modify this adapter unless:
1. The structure of the MCP server changes significantly
2. New tools are added (they will be automatically detected)
3. The tool calling mechanism changes 