# BlenderMCP - Blender Model Context Protocol Integration

⚠️ 
# Work in progress: This branch is under active development and not yet tested—use at your own risk.
⚠️

BlenderMCP connects Blender to Claude AI through the Model Context Protocol (MCP), allowing Claude to directly interact with and control Blender. This integration enables prompt assisted 3D modeling, scene creation, and manipulation.

Setting up the Chat GPT Version is explainer in the 'OPENAI_SETUP.md', Claude is replaced with ChatGPT.

[Full tutorial](https://www.youtube.com/watch?v=lCyQ717DuzQ)

### Join the Community

Give feedback, get inspired, and build on top of the MCP: [Discord](https://discord.gg/z5apgR8TFU)

### Supporters

**Top supporters:**

[CodeRabbit](https://www.coderabbit.ai/)

**All supporters:**

[Support this project](https://github.com/sponsors/ahujasid)

## Release notes (1.1.0)

- Added support for Poly Haven assets through their API
- Added support to prompt 3D models using Hyper3D Rodin
- For newcomers, you can go straight to Installation. For existing users, see the points below
- Download the latest addon.py file and replace the older one, then add it to Blender
- Delete the MCP server from Claude and add it back again, and you should be good to go!

## Features

- **Two-way communication**: Connect Claude AI to Blender through a socket-based server
- **Object manipulation**: Create, modify, and delete 3D objects in Blender
- **Material control**: Apply and modify materials and colors
- **Scene inspection**: Get detailed information about the current Blender scene
- **Code execution**: Run arbitrary Python code in Blender from Claude

## Components

The system consists of two main components:

1. **Blender Addon (`addon.py`)**: A Blender addon that creates a socket server within Blender to receive and execute commands
2. **MCP Server (`src/blender_mcp/server.py`)**: A Python server that implements the Model Context Protocol and connects to the Blender addon

## Installation


### Prerequisites

- Blender 3.0 or newer
- Python 3.10 or newer
- uv package manager: 

**If you're on Mac, please install uv as**
```bash
brew install uv
```
**On Windows**
```bash
powershell -c "irm https://astral.sh/uv/install.ps1 | iex" 
```
and then
```bash
set Path=C:\Users\nntra\.local\bin;%Path%
```

Otherwise installation instructions are on their website: [Install uv](https://docs.astral.sh/uv/getting-started/installation/)

**⚠️ Do not proceed before installing UV**


### Claude for Desktop Integration

[Watch the setup instruction video](https://www.youtube.com/watch?v=neoK_WMq92g) (Assuming you have already installed uv)

Go to Claude > Settings > Developer > Edit Config > claude_desktop_config.json to include the following:

```json
{
    "mcpServers": {
        "blender": {
            "command": "uvx",
            "args": [
                "blender-mcp"
            ]
        }
    }
}
```

### Cursor integration

For Mac users, go to Settings > MCP and paste the following 

- To use as a global server, use "add new global MCP server" button and paste
- To use as a project specific server, create `.cursor/mcp.json` in the root of the project and paste


```json
{
    "mcpServers": {
        "blender": {
            "command": "uvx",
            "args": [
                "blender-mcp"
            ]
        }
    }
}
```

For Windows users, go to Settings > MCP > Add Server, add a new server with the following settings:

```json
{
    "mcpServers": {
        "blender": {
            "command": "cmd",
            "args": [
                "/c",
                "uvx",
                "blender-mcp"
            ]
        }
    }
}
```

[Cursor setup video](https://www.youtube.com/watch?v=wgWsJshecac)

**⚠️ Only run one instance of the MCP server (either on Cursor or Claude Desktop), not both**

### Installing the Blender Addon

1. Download the `addon.py` file from this repo
1. Open Blender
2. Go to Edit > Preferences > Add-ons
3. Click "Install..." and select the `addon.py` file
4. Enable the addon by checking the box next to "Interface: Blender MCP"


## Usage

### Starting the Connection
![BlenderMCP in the sidebar](assets/addon-instructions.png)

1. In Blender, go to the 3D View sidebar (press N if not visible)
2. Find the "BlenderMCP" tab
3. Turn on the Poly Haven checkbox if you want assets from their API (optional)
4. Click "Connect to Claude"
5. Make sure the MCP server is running in your terminal

### Using with Claude

Once the config file has been set on Claude, and the addon is running on Blender, you will see a hammer icon with tools for the Blender MCP.

![BlenderMCP in the sidebar](assets/hammer-icon.png)

#### Capabilities

- Get scene and object information 
- Create, delete and modify shapes
- Apply or create materials for objects
- Execute any Python code in Blender
- Download the right models, assets and HDRIs through [Poly Haven](https://polyhaven.com/)
- AI generated 3D models through [Hyper3D Rodin](https://hyper3d.ai/)


### Example Commands

Here are some examples of what you can ask Claude to do:

- "Create a low poly scene in a dungeon, with a dragon guarding a pot of gold" [Demo](https://www.youtube.com/watch?v=DqgKuLYUv00)
- "Create a beach vibe using HDRIs, textures, and models like rocks and vegetation from Poly Haven" [Demo](https://www.youtube.com/watch?v=I29rn92gkC4)
- Give a reference image, and create a Blender scene out of it [Demo](https://www.youtube.com/watch?v=FDRb03XPiRo)
- "Generate a 3D model of a garden gnome through Hyper3D"
- "Get information about the current scene, and make a threejs sketch from it" [Demo](https://www.youtube.com/watch?v=jxbNI5L7AH8)
- "Make this car red and metallic" 
- "Create a sphere and place it above the cube"
- "Make the lighting like a studio"
- "Point the camera at the scene, and make it isometric"

## Hyper3D integration

Hyper3D's free trial key allows you to generate a limited number of models per day. If the daily limit is reached, you can wait for the next day's reset or obtain your own key from hyper3d.ai and fal.ai.

## Troubleshooting

- **Connection issues**: Make sure the Blender addon server is running, and the MCP server is configured on Claude, DO NOT run the uvx command in the terminal. Sometimes, the first command won't go through but after that it starts working.
- **Timeout errors**: Try simplifying your requests or breaking them into smaller steps
- **Poly Haven integration**: Claude is sometimes erratic with its behaviour
- **Have you tried turning it off and on again?**: If you're still having connection errors, try restarting both Claude and the Blender server


## Technical Details

### Communication Protocol

The system uses a simple JSON-based protocol over TCP sockets:

- **Commands** are sent as JSON objects with a `type` and optional `params`
- **Responses** are JSON objects with a `status` and `result` or `message`

## Limitations & Security Considerations

- The `execute_blender_code` tool allows running arbitrary Python code in Blender, which can be powerful but potentially dangerous. Use with caution in production environments. ALWAYS save your work before using it.
- Poly Haven requires downloading models, textures, and HDRI images. If you do not want to use it, please turn it off in the checkbox in Blender. 
- Complex operations might need to be broken down into smaller steps


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This is a third-party integration and not made by Blender. Made by [Siddharth](https://x.com/sidahuj)

# BlenderMCP OpenAI Adapter

This package provides an adapter to use OpenAI models (like GPT-4) with the BlenderMCP project instead of Claude.

## Installation

You can install the adapter using pip:

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

2. Set up your OpenAI API key as an environment variable:
   ```bash
   # Linux/macOS
   export OPENAI_API_KEY=your_api_key_here
   
   # Windows (Command Prompt)
   set OPENAI_API_KEY=your_api_key_here
   
   # Windows (PowerShell)
   $env:OPENAI_API_KEY="your_api_key_here"
   ```

3. Make sure you have already set up BlenderMCP according to the main project instructions.

## Usage

### Command Line

The simplest way to use the adapter is via the command line:

```bash
blender-mcp-openai --model gpt-4
```

Optional arguments:
- `--model`: Specify the OpenAI model to use (default: gpt-4)
- `--api-key`: Directly provide your OpenAI API key (alternatively, set the OPENAI_API_KEY environment variable)
- `--temperature`: Set the temperature for model responses (default: 0.7)
- `--max-tokens`: Set the maximum number of tokens to generate
- `--system-prompt`: Provide a system prompt to prepend to conversations
- `--config-file`: Path to a configuration file (see example below)
- `--log-level`: Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--log-file`: Path to a log file for output
- `--json-logs`: Output logs in JSON format

### Configuration File

For more customization, you can use a configuration file:

```bash
blender-mcp-openai --config-file config.json
```

Example configuration file (config.json):

```json
{
  "openai": {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2000,
    "system_prompt": "You are a Blender assistant, helping users with 3D modeling and animation tasks.",
    "additional_params": {
      "response_format": { "type": "text" }
    }
  },
  "log_level": "INFO",
  "log_file": "blender_mcp_openai.log",
  "json_logging": false,
  "mcp_connection": {
    "host": "localhost",
    "port": 9876
  }
}
```

### Integration with Claude Desktop or Cursor

To use the OpenAI adapter with Claude Desktop or Cursor, create a configuration file:

For Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "blender": {
      "command": "blender-mcp-openai",
      "args": [
        "--model",
        "gpt-4"
      ]
    }
  }
}
```

For Cursor (`mcp.json`):

```json
{
  "mcpServers": {
    "blender": {
      "command": "blender-mcp-openai",
      "args": [
        "--model",
        "gpt-4"
      ]
    }
  }
}
```

## Programmatic Usage

You can also use the adapter programmatically in your own Python code:

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

## Backward Compatibility

For backward compatibility with the original single-file implementation, a legacy entry point is provided:

```bash
openai_adapter --model gpt-4
```

## Architecture

The adapter is built with a modular architecture:

- `adapter.py`: Main adapter class that coordinates all components
- `schema.py`: Schema extraction for OpenAI function calling
- `dispatch.py`: Tool execution and error handling
- `streaming.py`: Advanced streaming with tool call processing
- `context.py`: Context management for MCP tools
- `config.py`: Configuration handling
- `cli.py`: Command-line interface
- `logging_utils.py`: Logging utilities
- `backward_compat.py`: Backward compatibility support

## Advanced Features

### Real Context Injection

The adapter provides real context objects to MCP tools instead of empty mocks, ensuring that tools that rely on session state or permissions work correctly.

### Advanced Schema Extraction

The schema extractor uses type hints and docstrings to generate detailed JSON schemas for OpenAI function calling, with support for nested types, unions, and optionals.

### Structured Error Handling

Errors during tool execution are handled gracefully and reported with structured information, making debugging easier.

### Advanced Streaming

The streaming implementation can detect and process tool calls mid-stream, allowing for interactive workflows.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
