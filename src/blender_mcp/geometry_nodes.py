"""
Blender Geometry Nodes integration for BlenderMCP.

This module provides functions to create and manipulate Geometry Nodes modifiers
and node trees in Blender through the MCP protocol.
"""

import logging

# Configure logging
logger = logging.getLogger("BlenderGeometryNodes")

# List of common Geometry Nodes node types
GEOMETRY_NODE_TYPES = {
    # Input nodes
    "input_position": "GeometryNodeInputPosition",
    "input_normal": "GeometryNodeInputNormal",
    "input_id": "GeometryNodeInputID",
    "input_index": "GeometryNodeInputIndex",
    "input_material_index": "GeometryNodeInputMaterialIndex",
    
    # Attribute nodes
    "attribute_statistic": "GeometryNodeAttributeStatistic",
    "attribute_domain_size": "GeometryNodeAttributeDomainSize",
    
    # Geometry nodes
    "mesh_primitive_cube": "GeometryNodeMeshCube",
    "mesh_primitive_cylinder": "GeometryNodeMeshCylinder",
    "mesh_primitive_sphere": "GeometryNodeMeshIcoSphere",
    "mesh_primitive_grid": "GeometryNodeMeshGrid",
    "mesh_primitive_circle": "GeometryNodeMeshCircle",
    "mesh_primitive_line": "GeometryNodeMeshLine",
    "mesh_primitive_cone": "GeometryNodeMeshCone",
    
    # Mesh operations
    "mesh_boolean": "GeometryNodeMeshBoolean",
    "mesh_to_points": "GeometryNodeMeshToPoints",
    "mesh_to_curve": "GeometryNodeMeshToCurve",
    "mesh_extrude": "GeometryNodeExtrudeMesh",
    "mesh_subdivide": "GeometryNodeSubdivideMesh",
    "mesh_triangulate": "GeometryNodeTriangulateMesh",
    
    # Point operations
    "points_to_vertices": "GeometryNodePointsToVertices",
    "points_to_volume": "GeometryNodePointsToVolume",
    
    # Curve operations
    "curve_primitive_line": "GeometryNodeCurvePrimitiveLine",
    "curve_primitive_circle": "GeometryNodeCurvePrimitiveCircle",
    "curve_to_mesh": "GeometryNodeCurveToMesh",
    "curve_to_points": "GeometryNodeCurveToPoints",
    "curve_length": "GeometryNodeCurveLength",
    
    # Instances
    "instance_on_points": "GeometryNodeInstanceOnPoints",
    "realize_instances": "GeometryNodeRealizeInstances",
    
    # Transforms
    "transform": "GeometryNodeTransform",
    "translate": "GeometryNodeTranslate",
    "rotate": "GeometryNodeRotate",
    "scale": "GeometryNodeScale",
    
    # Materials
    "set_material": "GeometryNodeSetMaterial",
    "material_selection": "GeometryNodeMaterialSelection",
    
    # Utilities
    "math": "ShaderNodeMath",
    "vector_math": "ShaderNodeVectorMath",
    "boolean_math": "FunctionNodeBooleanMath",
    "combine_xyz": "ShaderNodeCombineXYZ",
    "separate_xyz": "ShaderNodeSeparateXYZ",
    "map_range": "ShaderNodeMapRange",
    
    # Geometry operations
    "join_geometry": "GeometryNodeJoinGeometry",
    "separate_geometry": "GeometryNodeSeparateGeometry",
    "transform_geometry": "GeometryNodeTransform",
    
    # Group nodes
    "group_input": "NodeGroupInput",
    "group_output": "NodeGroupOutput",
}

def create_geometry_nodes_setup(params):
    """
    Generate Python code to create a Geometry Nodes setup in Blender.
    
    Args:
        params (dict): Parameters for the Geometry Nodes setup
            - object_name (str): Name of the object to add the modifier to
            - setup_name (str): Name for the Geometry Nodes modifier and node group
            - nodes (list): List of node definitions
            - links (list): List of connections between nodes
            
    Returns:
        str: Python code to execute in Blender
    """
    object_name = params.get("object_name")
    setup_name = params.get("setup_name", "GeometryNodes")
    nodes = params.get("nodes", [])
    links = params.get("links", [])
    
    if not object_name:
        return "# Error: No object name provided"
    
    if not nodes:
        return "# Error: No nodes provided"
    
    # Generate code to create the Geometry Nodes modifier and node group
    code = [
        f"import bpy",
        f"",
        f"# Get the object",
        f"obj = bpy.data.objects.get('{object_name}')",
        f"",
        f"if not obj:",
        f"    raise Exception(f'Object {object_name} not found')",
        f"",
        f"# Create a new Geometry Nodes modifier or use existing one",
        f"mod = obj.modifiers.get('{setup_name}')",
        f"if not mod:",
        f"    mod = obj.modifiers.new(name='{setup_name}', type='NODES')",
        f"",
        f"# Create a new node group or use existing one",
        f"if mod.node_group is None:",
        f"    node_group = bpy.data.node_groups.new(name='{setup_name}', type='GeometryNodeTree')",
        f"    mod.node_group = node_group",
        f"else:",
        f"    node_group = mod.node_group",
        f"",
        f"# Clear existing nodes and links",
        f"node_group.nodes.clear()",
        f"node_group.links.clear()",
        f"",
        f"# Create input and output sockets if needed",
        f"if 'Geometry' not in node_group.inputs:",
        f"    node_group.inputs.new('NodeSocketGeometry', 'Geometry')",
        f"if 'Geometry' not in node_group.outputs:",
        f"    node_group.outputs.new('NodeSocketGeometry', 'Geometry')",
        f"",
        f"# Create nodes",
        f"nodes = {{}}"
    ]
    
    # Generate code for each node
    for i, node_def in enumerate(nodes):
        node_id = node_def.get("id", f"node_{i}")
        node_type = node_def.get("type")
        node_name = node_def.get("name", node_id)
        node_location = node_def.get("location", [0, 0])
        node_params = node_def.get("params", {})
        
        if not node_type:
            code.append(f"# Warning: Node {node_id} has no type specified")
            continue
        
        # Get the Blender node type from our mapping
        blender_node_type = GEOMETRY_NODE_TYPES.get(node_type, node_type)
        
        code.append(f"")
        code.append(f"# Create node: {node_name} ({node_type})")
        code.append(f"nodes['{node_id}'] = node_group.nodes.new('{blender_node_type}')")
        code.append(f"nodes['{node_id}'].name = '{node_name}'")
        code.append(f"nodes['{node_id}'].location = ({node_location[0]}, {node_location[1]})")
        
        # Set node parameters
        for param_name, param_value in node_params.items():
            if isinstance(param_value, str):
                code.append(f"nodes['{node_id}'].{param_name} = '{param_value}'")
            else:
                code.append(f"nodes['{node_id}'].{param_name} = {param_value}")
    
    # Generate code for links
    if links:
        code.append(f"")
        code.append(f"# Create links")
        
        for link in links:
            from_node = link.get("from_node")
            from_socket = link.get("from_socket")
            to_node = link.get("to_node")
            to_socket = link.get("to_socket")
            
            if not all([from_node, from_socket, to_node, to_socket]):
                code.append(f"# Warning: Link has missing information: {link}")
                continue
            
            code.append(f"node_group.links.new(nodes['{from_node}'].outputs['{from_socket}'], nodes['{to_node}'].inputs['{to_socket}'])")
    
    # Connect group input and output if they exist
    code.append(f"")
    code.append(f"# Connect group input and output if they exist")
    code.append(f"group_input = next((n for n in nodes.values() if n.type == 'GROUP_INPUT'), None)")
    code.append(f"group_output = next((n for n in nodes.values() if n.type == 'GROUP_OUTPUT'), None)")
    code.append(f"")
    code.append(f"if group_input and group_output:")
    code.append(f"    # Find the last geometry output before the group output")
    code.append(f"    for node in nodes.values():")
    code.append(f"        if node != group_output and 'Geometry' in node.outputs:")
    code.append(f"            for link in node_group.links:")
    code.append(f"                if link.to_node == group_output and link.to_socket.name == 'Geometry':")
    code.append(f"                    # Already connected")
    code.append(f"                    break")
    code.append(f"            else:")
    code.append(f"                # Not connected yet, try to connect")
    code.append(f"                for output in node.outputs:")
    code.append(f"                    if 'Geometry' in output.name:")
    code.append(f"                        for input in group_output.inputs:")
    code.append(f"                            if 'Geometry' in input.name:")
    code.append(f"                                node_group.links.new(output, input)")
    code.append(f"                                break")
    code.append(f"                        break")
    
    return "\n".join(code)

def create_common_geometry_setup(params):
    """
    Generate code for common geometry node setups based on high-level descriptions.
    
    Args:
        params (dict): Parameters for the geometry setup
            - type (str): Type of setup (e.g., "array", "scatter", "deform")
            - object_name (str): Name of the object to add the modifier to
            - setup_params (dict): Parameters specific to the setup type
            
    Returns:
        str: Python code to execute in Blender
    """
    setup_type = params.get("type", "").lower()
    object_name = params.get("object_name")
    setup_params = params.get("setup_params", {})
    
    if not object_name:
        return "# Error: No object name provided"
    
    if not setup_type:
        return "# Error: No setup type provided"
    
    # Define the nodes and links based on the setup type
    nodes = []
    links = []
    
    if setup_type == "array":
        # Create a simple array setup using instances on points
        count_x = setup_params.get("count_x", 3)
        count_y = setup_params.get("count_y", 3)
        count_z = setup_params.get("count_z", 1)
        spacing_x = setup_params.get("spacing_x", 2.0)
        spacing_y = setup_params.get("spacing_y", 2.0)
        spacing_z = setup_params.get("spacing_z", 2.0)
        
        nodes = [
            {"id": "group_input", "type": "group_input", "name": "Group Input", "location": [-600, 0]},
            {"id": "group_output", "type": "group_output", "name": "Group Output", "location": [600, 0]},
            
            {"id": "mesh_line_x", "type": "mesh_primitive_line", "name": "Line X", "location": [-400, 100],
             "params": {"count_segments_input": count_x}},
            {"id": "mesh_line_y", "type": "mesh_primitive_line", "name": "Line Y", "location": [-400, -100],
             "params": {"count_segments_input": count_y}},
            {"id": "mesh_line_z", "type": "mesh_primitive_line", "name": "Line Z", "location": [-400, -300],
             "params": {"count_segments_input": count_z}},
            
            {"id": "combine_xyz", "type": "combine_xyz", "name": "Combine XYZ", "location": [-200, 0]},
            {"id": "scale", "type": "scale", "name": "Scale", "location": [0, 0],
             "params": {"scale": [spacing_x, spacing_y, spacing_z]}},
            
            {"id": "mesh_to_points", "type": "mesh_to_points", "name": "Mesh to Points", "location": [200, 0]},
            {"id": "instance_on_points", "type": "instance_on_points", "name": "Instance on Points", "location": [400, 0]},
        ]
        
        links = [
            {"from_node": "group_input", "from_socket": "Geometry", "to_node": "instance_on_points", "to_socket": "Instance"},
            {"from_node": "mesh_line_x", "from_socket": "Mesh", "to_node": "mesh_to_points", "to_socket": "Mesh"},
            {"from_node": "mesh_to_points", "from_socket": "Points", "to_node": "instance_on_points", "to_socket": "Points"},
            {"from_node": "instance_on_points", "from_socket": "Instances", "to_node": "group_output", "to_socket": "Geometry"},
        ]
    
    elif setup_type == "scatter":
        # Create a point scatter setup
        count = setup_params.get("count", 100)
        seed = setup_params.get("seed", 0)
        min_distance = setup_params.get("min_distance", 0.1)
        density_max = setup_params.get("density_max", 10.0)
        
        nodes = [
            {"id": "group_input", "type": "group_input", "name": "Group Input", "location": [-600, 0]},
            {"id": "group_output", "type": "group_output", "name": "Group Output", "location": [600, 0]},
            
            {"id": "distribute_points", "type": "GeometryNodeDistributePointsOnFaces", "name": "Distribute Points", 
             "location": [-200, 0],
             "params": {"distribute_method": "'POISSON'", "density_max": density_max, "seed": seed}},
            
            {"id": "instance_on_points", "type": "instance_on_points", "name": "Instance on Points", "location": [200, 0]},
            {"id": "mesh_sphere", "type": "mesh_primitive_sphere", "name": "Sphere", "location": [0, -200],
             "params": {"radius": 0.1}},
        ]
        
        links = [
            {"from_node": "group_input", "from_socket": "Geometry", "to_node": "distribute_points", "to_socket": "Mesh"},
            {"from_node": "distribute_points", "from_socket": "Points", "to_node": "instance_on_points", "to_socket": "Points"},
            {"from_node": "mesh_sphere", "from_socket": "Mesh", "to_node": "instance_on_points", "to_socket": "Instance"},
            {"from_node": "instance_on_points", "from_socket": "Instances", "to_node": "group_output", "to_socket": "Geometry"},
        ]
    
    elif setup_type == "deform":
        # Create a simple deformation setup
        strength = setup_params.get("strength", 1.0)
        deform_type = setup_params.get("deform_type", "noise").lower()
        
        nodes = [
            {"id": "group_input", "type": "group_input", "name": "Group Input", "location": [-600, 0]},
            {"id": "group_output", "type": "group_output", "name": "Group Output", "location": [600, 0]},
            
            {"id": "position", "type": "input_position", "name": "Position", "location": [-400, 0]},
            {"id": "normal", "type": "input_normal", "name": "Normal", "location": [-400, -200]},
        ]
        
        if deform_type == "noise":
            nodes.extend([
                {"id": "noise_texture", "type": "ShaderNodeTexNoise", "name": "Noise Texture", "location": [-200, 0],
                 "params": {"scale": 1.0}},
                {"id": "vector_math", "type": "vector_math", "name": "Vector Math", "location": [0, 0],
                 "params": {"operation": "'MULTIPLY'", "scale": strength}},
                {"id": "set_position", "type": "GeometryNodeSetPosition", "name": "Set Position", "location": [200, 0]},
            ])
            
            links = [
                {"from_node": "group_input", "from_socket": "Geometry", "to_node": "set_position", "to_socket": "Geometry"},
                {"from_node": "position", "from_socket": "Position", "to_node": "noise_texture", "to_socket": "Vector"},
                {"from_node": "noise_texture", "from_socket": "Color", "to_node": "vector_math", "to_socket": "Vector"},
                {"from_node": "normal", "from_socket": "Normal", "to_node": "vector_math", "to_socket": "Vector1"},
                {"from_node": "vector_math", "from_socket": "Vector", "to_node": "set_position", "to_socket": "Offset"},
                {"from_node": "set_position", "from_socket": "Geometry", "to_node": "group_output", "to_socket": "Geometry"},
            ]
        elif deform_type == "wave":
            nodes.extend([
                {"id": "separate_xyz", "type": "separate_xyz", "name": "Separate XYZ", "location": [-200, 0]},
                {"id": "math_sin", "type": "math", "name": "Sine", "location": [0, 0],
                 "params": {"operation": "'SINE'"}},
                {"id": "math_multiply", "type": "math", "name": "Multiply", "location": [200, 0],
                 "params": {"operation": "'MULTIPLY'", "value1": strength}},
                {"id": "combine_xyz", "type": "combine_xyz", "name": "Combine XYZ", "location": [400, 0],
                 "params": {"z": 0.0}},
                {"id": "set_position", "type": "GeometryNodeSetPosition", "name": "Set Position", "location": [600, 0]},
            ])
            
            links = [
                {"from_node": "group_input", "from_socket": "Geometry", "to_node": "set_position", "to_socket": "Geometry"},
                {"from_node": "position", "from_socket": "Position", "to_node": "separate_xyz", "to_socket": "Vector"},
                {"from_node": "separate_xyz", "from_socket": "X", "to_node": "math_sin", "to_socket": "Value"},
                {"from_node": "math_sin", "from_socket": "Value", "to_node": "math_multiply", "to_socket": "Value"},
                {"from_node": "math_multiply", "from_socket": "Value", "to_node": "combine_xyz", "to_socket": "Y"},
                {"from_node": "separate_xyz", "from_socket": "X", "to_node": "combine_xyz", "to_socket": "X"},
                {"from_node": "combine_xyz", "from_socket": "Vector", "to_node": "set_position", "to_socket": "Offset"},
                {"from_node": "set_position", "from_socket": "Geometry", "to_node": "group_output", "to_socket": "Geometry"},
            ]
    
    elif setup_type == "boolean":
        # Create a boolean operation setup
        operation = setup_params.get("operation", "DIFFERENCE").upper()
        primitive_type = setup_params.get("primitive_type", "cube").lower()
        primitive_size = setup_params.get("primitive_size", 1.0)
        primitive_location = setup_params.get("primitive_location", [0, 0, 0])
        
        nodes = [
            {"id": "group_input", "type": "group_input", "name": "Group Input", "location": [-600, 0]},
            {"id": "group_output", "type": "group_output", "name": "Group Output", "location": [600, 0]},
            
            {"id": "boolean", "type": "mesh_boolean", "name": "Boolean", "location": [200, 0],
             "params": {"operation": f"'{operation}'"}},
        ]
        
        if primitive_type == "cube":
            nodes.append({
                "id": "mesh_cube", "type": "mesh_primitive_cube", "name": "Cube", "location": [-200, -200],
                "params": {"size": primitive_size}
            })
            primitive_node_id = "mesh_cube"
        elif primitive_type == "sphere":
            nodes.append({
                "id": "mesh_sphere", "type": "mesh_primitive_sphere", "name": "Sphere", "location": [-200, -200],
                "params": {"radius": primitive_size}
            })
            primitive_node_id = "mesh_sphere"
        elif primitive_type == "cylinder":
            nodes.append({
                "id": "mesh_cylinder", "type": "mesh_primitive_cylinder", "name": "Cylinder", "location": [-200, -200],
                "params": {"radius": primitive_size, "depth": primitive_size * 2}
            })
            primitive_node_id = "mesh_cylinder"
        
        # Add transform node for the primitive
        nodes.append({
            "id": "transform", "type": "transform", "name": "Transform", "location": [0, -200],
            "params": {"translation": primitive_location}
        })
        
        links = [
            {"from_node": "group_input", "from_socket": "Geometry", "to_node": "boolean", "to_socket": "Mesh 1"},
            {"from_node": primitive_node_id, "from_socket": "Mesh", "to_node": "transform", "to_socket": "Geometry"},
            {"from_node": "transform", "from_socket": "Geometry", "to_node": "boolean", "to_socket": "Mesh 2"},
            {"from_node": "boolean", "from_socket": "Mesh", "to_node": "group_output", "to_socket": "Geometry"},
        ]
    
    # Create the full setup
    setup_params = {
        "object_name": object_name,
        "setup_name": f"GN_{setup_type.capitalize()}",
        "nodes": nodes,
        "links": links
    }
    
    return create_geometry_nodes_setup(setup_params)

def parse_natural_language_to_geometry_nodes(params):
    """
    Parse natural language description into a Geometry Nodes setup.
    
    This is a placeholder for a more sophisticated natural language processing function.
    In a real implementation, this would use more advanced NLP techniques or call an external API.
    
    Args:
        params (dict): Parameters for the parsing
            - description (str): Natural language description of the desired setup
            - object_name (str): Name of the object to add the modifier to
            
    Returns:
        str: Python code to execute in Blender
    """
    description = params.get("description", "").lower()
    object_name = params.get("object_name")
    
    if not object_name:
        return "# Error: No object name provided"
    
    if not description:
        return "# Error: No description provided"
    
    # Simple keyword matching for now
    setup_params = {}
    
    if "array" in description or "grid" in description or "repeat" in description:
        setup_type = "array"
        
        # Extract parameters from the description
        import re
        
        # Try to find counts
        count_match = re.search(r'(\d+)\s*x\s*(\d+)(?:\s*x\s*(\d+))?', description)
        if count_match:
            setup_params["count_x"] = int(count_match.group(1))
            setup_params["count_y"] = int(count_match.group(2))
            if count_match.group(3):
                setup_params["count_z"] = int(count_match.group(3))
        
        # Try to find spacing
        spacing_match = re.search(r'spacing\s*(?:of)?\s*(\d+(?:\.\d+)?)', description)
        if spacing_match:
            spacing = float(spacing_match.group(1))
            setup_params["spacing_x"] = spacing
            setup_params["spacing_y"] = spacing
            setup_params["spacing_z"] = spacing
    
    elif "scatter" in description or "distribute" in description or "random" in description:
        setup_type = "scatter"
        
        # Extract parameters from the description
        import re
        
        # Try to find count
        count_match = re.search(r'(\d+)\s*(?:points|instances)', description)
        if count_match:
            setup_params["count"] = int(count_match.group(1))
        
        # Try to find density
        density_match = re.search(r'density\s*(?:of)?\s*(\d+(?:\.\d+)?)', description)
        if density_match:
            setup_params["density_max"] = float(density_match.group(1))
    
    elif "deform" in description or "distort" in description or "wave" in description or "noise" in description:
        setup_type = "deform"
        
        if "wave" in description:
            setup_params["deform_type"] = "wave"
        else:
            setup_params["deform_type"] = "noise"
        
        # Extract parameters from the description
        import re
        
        # Try to find strength
        strength_match = re.search(r'strength\s*(?:of)?\s*(\d+(?:\.\d+)?)', description)
        if strength_match:
            setup_params["strength"] = float(strength_match.group(1))
    
    elif "boolean" in description or "subtract" in description or "cut" in description or "intersect" in description:
        setup_type = "boolean"
        
        if "subtract" in description or "cut" in description:
            setup_params["operation"] = "DIFFERENCE"
        elif "intersect" in description:
            setup_params["operation"] = "INTERSECT"
        elif "union" in description:
            setup_params["operation"] = "UNION"
        
        # Determine primitive type
        if "sphere" in description:
            setup_params["primitive_type"] = "sphere"
        elif "cylinder" in description:
            setup_params["primitive_type"] = "cylinder"
        else:
            setup_params["primitive_type"] = "cube"
        
        # Extract parameters from the description
        import re
        
        # Try to find size
        size_match = re.search(r'size\s*(?:of)?\s*(\d+(?:\.\d+)?)', description)
        if size_match:
            setup_params["primitive_size"] = float(size_match.group(1))
        
        # Try to find location
        location_match = re.search(r'at\s*\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)', description)
        if location_match:
            setup_params["primitive_location"] = [
                float(location_match.group(1)),
                float(location_match.group(2)),
                float(location_match.group(3))
            ]
    
    else:
        # Default to a simple deform setup
        setup_type = "deform"
        setup_params["deform_type"] = "noise"
        setup_params["strength"] = 0.5
    
    return create_common_geometry_setup({
        "type": setup_type,
        "object_name": object_name,
        "setup_params": setup_params
    }) 