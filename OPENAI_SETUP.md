# Using BlenderMCP with OpenAI Models

This guide explains how to use the `openai_adapter.py` script to connect BlenderMCP with OpenAI models like GPT-4 instead of using Claude.

## Prerequisites

1. Install the OpenAI Python library:
   ```
   pip install openai
   ```

2. Set up your OpenAI API key. You can either:
   - Set it as an environment variable: `export OPENAI_API_KEY=your_api_key_here`
   - Or pass it as a command-line argument (see below)

3. Make sure you have already set up BlenderMCP according to the main project instructions

## Usage

### Method 1: Run the adapter directly

Simply run the adapter script directly, which will start the MCP server using OpenAI models:

```
python openai_adapter.py --model gpt-4
```

Optional arguments:
- `--model`: Specify the OpenAI model to use (default: gpt-4)
- `--api-key`: Directly provide your OpenAI API key if not set as an environment variable

### Method 2: Configure Claude for Desktop

1. In Claude for Desktop, go to Settings > Developer > Edit Config.
2. Update or create `claude_desktop_config.json` to include:

```json
{
    "mcpServers": {
        "blender": {
            "command": "python",
            "args": [
                "openai_adapter.py",
                "--model",
                "gpt-4"
            ]
        }
    }
}
```

3. Save the file and restart Claude.

### Method 3: Configure Cursor

1. Create a `.cursor/mcp.json` file in your project root or update your global MCP configuration.
2. Add the following content:

```json
{
    "mcpServers": {
        "blender": {
            "command": "python",
            "args": [
                "openai_adapter.py",
                "--model",
                "gpt-4"
            ]
        }
    }
}
```

3. Restart Cursor or reload the configuration.

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

## Troubleshooting

- **Import Error**: Make sure the adapter can find the `blender_mcp` module. The script attempts to import it directly or from the `src` directory.
- **Authorization Error**: Check your OpenAI API key is correctly set and has sufficient quota.
- **Tool Execution Error**: If specific tools aren't working, check the logs for detailed error messages.

## Updating

When the original BlenderMCP project is updated, you typically won't need to modify this adapter unless:
1. The structure of the MCP server changes significantly
2. New tools are added (they will be automatically detected)
3. The tool calling mechanism changes 