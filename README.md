# BlenderMCP - Blender Model Context Protocol Integration

BlenderMCP connects Blender to Claude AI through the Model Context Protocol (MCP), allowing Claude to directly interact with and control Blender. This integration enables prompt assisted 3D modeling, scene creation, and manipulation.

## Release notes (1.2.0)

- Added Geometry Nodes functionality support, allowing control of Blender's Geometry Nodes system through natural language
- Support for creating common Geometry Nodes setups such as arrays, point scattering, deformation, and boolean operations
- Support for creating Geometry Nodes setups through natural language descriptions
- Support for getting and modifying Geometry Nodes modifier information
- 新增几何节点(Geometry Nodes)功能支持，允许通过自然语言控制Blender的几何节点系统
- 支持创建常见的几何节点设置，如阵列、散点分布、变形和布尔操作
- 支持通过自然语言描述创建几何节点设置
- 支持获取和修改几何节点修改器信息
- For newcomers, you can go straight to Installation. For existing users, see the points below
- Download the latest addon.py file and replace the older one, then add it to Blender
- Delete the MCP server from Claude and add it back again, and you should be good to go!
- 对于新用户，请直接查看安装说明。对于现有用户，请查看下面的更新说明
- 下载最新的addon.py文件并替换旧文件，然后将其添加到Blender中
- 从Claude中删除MCP服务器并重新添加，然后就可以开始使用了！

## Features

- **Two-way communication**: Connect Claude AI to Blender through a socket-based server
- **Object manipulation**: Create, modify, and delete 3D objects in Blender
- **Material control**: Apply and modify materials and colors
- **Scene inspection**: Get detailed information about the current Blender scene
- **Code execution**: Run arbitrary Python code in Blender from Claude

## Components

The system consists of three main components:

1. **Blender Addon (`addon.py`)**: A Blender addon that creates a socket server within Blender to receive and execute commands
2. **MCP Server (`src/blender_mcp/server.py`)**: A Python server that implements the Model Context Protocol and connects to the Blender addon
3. **Geometry Nodes Module (`src/blender_mcp/geometry_nodes.py`)**: A Python module that provides functions for creating and manipulating Geometry Nodes in Blender

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

Run blender-mcp without installing it permanently through uvx. Go to Cursor Settings > MCP and paste this as a command.

```bash
uvx blender-mcp
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

#### Tools

- `get_scene_info` - Gets scene information
- `get_object_info` - Gets detailed information for a specific object in the scene
- `create_primitive` - Create basic primitive objects with optional color
- `set_object_property` - Set a single property of an object
- `create_object` - Create a new object with detailed parameters
- `modify_object` - Modify an existing object's properties
- `delete_object` - Remove an object from the scene
- `set_material` - Apply or create materials for objects
- `execute_blender_code` - Run any Python code in Blender
- `get_polyhaven_categories` - Get a list of categories for PolyHaven assets (HDRIs, textures, models)
- `search_polyhaven_assets` - Search for assets on PolyHaven with optional category filtering
- `download_polyhaven_asset` - Download and import a PolyHaven asset into Blender

#### Geometry Nodes Tools / 几何节点工具

- `create_geometry_nodes` - Create a Geometry Nodes setup with precise control over nodes and connections
- `create_common_geometry_node_setup` - Create predefined Geometry Nodes setups like arrays, point scattering, deformation, or boolean operations
- `create_geometry_nodes_from_description` - Create Geometry Nodes setups based on natural language descriptions
- `get_geometry_nodes_info` - Get information about Geometry Nodes modifiers on an object
- `modify_geometry_nodes` - Modify properties of Geometry Nodes modifiers
- `create_geometry_nodes` - 创建一个几何节点设置，允许精确控制节点和连接
- `create_common_geometry_node_setup` - 创建预定义的几何节点设置，如阵列、散点分布、变形或布尔操作
- `create_geometry_nodes_from_description` - 根据自然语言描述创建几何节点设置
- `get_geometry_nodes_info` - 获取对象上的几何节点修改器信息
- `modify_geometry_nodes` - 修改几何节点修改器的属性

To see everything in Poly Haven, [see here](https://polyhaven.com/)

### Example Commands

Here are some examples of what you can ask Claude to do:

- "Create a low poly scene in a dungeon, with a dragon guarding a pot of gold" [Demo](https://www.youtube.com/watch?v=DqgKuLYUv00)
- "Create a beach vibe using HDRIs, textures, and models like rocks and vegetation from Poly Haven" [Demo](https://www.youtube.com/watch?v=I29rn92gkC4)
- Give a reference image, and create a Blender scene out of it [Demo](https://www.youtube.com/watch?v=FDRb03XPiRo)
- "Get information about the current scene, and make a threejs sketch from it" [Demo](https://www.youtube.com/watch?v=jxbNI5L7AH8)
- "Make this car red and metallic" 
- "Create a sphere and place it above the cube"
- "Make the lighting like a studio"
- "Point the camera at the scene, and make it isometric"

#### Geometry Nodes Example Commands / 几何节点示例命令

- "Create a 3x3 grid array on the cube with spacing of 2"
- "Randomly distribute 100 points on the sphere surface"
- "Apply noise deformation to the cube with strength of 0.5"
- "Perform a boolean subtraction operation on the cube using a sphere of size 1.5"
- "Create a wave deformation effect and apply it to the plane"
- "Add a Geometry Nodes modifier to the cube to create a fractal effect"
- "在立方体上创建一个3x3的网格阵列，间距为2"
- "在球体表面上随机分布100个点"
- "使用噪波变形立方体，强度为0.5"
- "使用球体对立方体进行布尔减法操作，球体大小为1.5"
- "创建一个波浪变形效果，应用到平面上"
- "在立方体上添加几何节点修改器，创建一个分形效果"

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

This is a third-party integration and not made by Blender.
