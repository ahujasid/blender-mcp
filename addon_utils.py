import bpy
import math
import random
import os
from pathlib import Path
from datetime import datetime

# --- Screenshot Configuration ---
# Screenshots for history are stored in the user's Blender datafiles directory,
# typically found under: .../Blender/[version]/datafiles/blender_mcp_screenshots/
SCREENSHOT_DIR_PATH = Path(bpy.utils.user_resource('DATAFILES', path="blender_mcp_screenshots"))

def _ensure_screenshot_dir_exists():
    """Ensures the screenshot directory exists."""
    print(f"BlenderMCP: Target screenshot directory: {SCREENSHOT_DIR_PATH}")
    if not SCREENSHOT_DIR_PATH.exists():
        print(f"BlenderMCP: Directory does not exist, attempting to create.")
        os.makedirs(SCREENSHOT_DIR_PATH, exist_ok=True) # exist_ok=True is important
    if SCREENSHOT_DIR_PATH.exists():
        print(f"BlenderMCP: Screenshot directory is accessible.")
    else:
        print(f"BlenderMCP: ERROR - Screenshot directory still does not exist after attempting creation.")

def get_screenshot_filepath():
    """Generates a unique filepath for a new screenshot."""
    _ensure_screenshot_dir_exists()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return SCREENSHOT_DIR_PATH / f"capture_{timestamp}.png"
# --- End Screenshot Configuration ---

# --- Utility Functions for Complex Object Creation ---
# These functions are intended to be callable via the 'execute_code' MCP command,
# allowing an LLM to request the creation of these procedurally generated objects.

def create_modified_cube(name="ModifiedCube", size=2, subdiv_levels=2, bevel_width=0.05, bevel_segments=2, solidify_thickness=0.1, displace_strength=0.2, displace_midlevel=0.5, base_location=(0,0,0)):
    """
    Creates a cube with several modifiers applied for a more complex shape.
    Intended for use by an LLM via the 'execute_code' command.

    Parameters:
    - name (str): Name for the new cube object.
    - size (float): Size of the initial cube.
    - subdiv_levels (int): Viewport and render subdivision levels for the Subdivision Surface modifier.
    - bevel_width (float): Width for the Bevel modifier.
    - bevel_segments (int): Number of segments for the Bevel modifier.
    - solidify_thickness (float): Thickness for the Solidify modifier.
    - displace_strength (float): Strength for the Displace modifier.
    - displace_midlevel (float): Midlevel for the Displace modifier.
    - base_location (tuple): (x, y, z) location for the cube.

    Returns:
    bpy.types.Object: The created and modified cube object.
    """
    bpy.ops.mesh.primitive_cube_add(size=size, location=base_location)
    obj = bpy.context.object
    obj.name = name
    # Subdivision
    subdiv_mod = obj.modifiers.new(name="Subdivision", type='SUBSURF')
    subdiv_mod.levels = subdiv_levels
    subdiv_mod.render_levels = subdiv_levels
    # Bevel
    bevel_mod = obj.modifiers.new(name="Bevel", type='BEVEL')
    bevel_mod.width = bevel_width
    bevel_mod.segments = bevel_segments
    # Solidify
    solidify_mod = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
    solidify_mod.thickness = solidify_thickness
    # Displace
    displace_mod = obj.modifiers.new(name="Displace", type='DISPLACE')
    tex_name = f"{name}_DisplaceTex"
    if tex_name in bpy.data.textures: displace_tex = bpy.data.textures[tex_name]
    else: displace_tex = bpy.data.textures.new(name=tex_name, type='CLOUDS')
    displace_mod.texture = displace_tex
    displace_mod.strength = displace_strength
    displace_mod.mid_level = displace_midlevel
    return obj

def create_voronoi_rock(name="Rock", size=1.0, voronoi_scale=1.0, voronoi_randomness=1.0, subdiv_levels=2, smooth_iterations=5, base_location=(0,0,0)):
    """
    Creates a rock-like object using an IcoSphere and Voronoi displacement.
    Intended for use by an LLM via the 'execute_code' command.
    Parameters: (omitted for brevity)
    Returns: bpy.types.Object: The created rock object.
    """
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=size/2, location=base_location)
    obj = bpy.context.object
    obj.name = name
    # Displace
    displace_mod = obj.modifiers.new(name="Displace", type='DISPLACE')
    tex_name = f"{name}_VoronoiTex"
    if tex_name in bpy.data.textures: voronoi_tex = bpy.data.textures[tex_name]
    else: voronoi_tex = bpy.data.textures.new(name=tex_name, type='VORONOI')
    voronoi_tex.noise_scale = voronoi_scale
    voronoi_tex.intensity = voronoi_randomness
    displace_mod.texture = voronoi_tex
    displace_mod.strength = 1.0
    # Subdivision
    subdiv_mod = obj.modifiers.new(name="Subdivision", type='SUBSURF')
    subdiv_mod.levels = subdiv_levels
    subdiv_mod.render_levels = subdiv_levels
    # Smooth
    smooth_mod = obj.modifiers.new(name="Smooth", type='SMOOTH')
    smooth_mod.iterations = smooth_iterations
    return obj

def create_parametric_gear(name="Gear", teeth=12, radius=1.0, addendum=0.1, dedendum=0.125, bevel_width=0.02, bevel_segments=2, solidify_thickness=0.2, base_location=(0,0,0)):
    """
    Creates a gear-like object. Attempts 'Add Mesh: Extra Objects' addon's gear.
    Falls back to a cylinder placeholder if unavailable/fails.
    Intended for use by an LLM via the 'execute_code' command.
    Parameters: (omitted for brevity)
    Returns: bpy.types.Object: The created gear object or placeholder.
    """
    obj = None
    text_obj = None
    if hasattr(bpy.ops.mesh, 'primitive_gear_add'):
        try:
            bpy.ops.mesh.primitive_gear_add(num_teeth=teeth, radius=radius, addendum=addendum, dedendum=dedendum, base_radius=radius-addendum-dedendum, location=base_location, align='WORLD')
            obj = bpy.context.object
            obj.name = name
        except TypeError as e:
            print(f"Error calling primitive_gear_add: {e}")
            obj = None
    if obj is None:
        print("Add Mesh: Extra Objects (primitive_gear_add) not available/failed. Creating cylinder placeholder.")
        bpy.ops.mesh.primitive_cylinder_add(vertices=teeth*2, radius=radius, depth=solidify_thickness, location=base_location, end_fill_type='NGON')
        obj = bpy.context.object
        obj.name = name
        text_loc = (base_location[0], base_location[1], base_location[2] + radius + 0.2)
        bpy.ops.object.text_add(location=text_loc)
        text_obj = bpy.context.object
        text_obj.data.body = "Gear Placeholder (Extra Objects addon disabled or failed)"
        text_obj.scale = (0.3,0.3,0.3)
        text_obj.parent = obj
    if obj:
        bevel_mod = obj.modifiers.new(name="Bevel", type='BEVEL')
        bevel_mod.width = bevel_width
        bevel_mod.segments = bevel_segments
        bevel_mod.limit_method = 'ANGLE'
        is_2d_profile = True
        if obj.type == 'MESH' and len(obj.data.polygons) > 0:
            verts = [v.co.z for v in obj.data.vertices]
            if verts and (max(verts) - min(verts)) > 0.001: is_2d_profile = False
        if is_2d_profile:
             solidify_mod = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
             solidify_mod.thickness = solidify_thickness
        elif not hasattr(bpy.ops.mesh, 'primitive_gear_add') or text_obj: pass
        else: print(f"Gear '{name}' might have its own thickness. Solidify modifier skipped.")
    return obj

def create_pipe_joint(name="PipeJoint", main_pipe_radius=0.5, main_pipe_length=2.0, branch_pipe_radius=0.3, branch_pipe_length=1.5, branch_angle_degrees=90.0, segments=32, bevel_width=0.05, bevel_segments=3, base_location=(0,0,0)):
    """
    Creates a pipe joint using two cylinders and a boolean union. Main pipe Y-aligned.
    Branch angle 0 for T, 90 for L-junction (off +Y end, towards +Z).
    Intended for use by an LLM via the 'execute_code' command.
    Parameters: (omitted for brevity)
    Returns: bpy.types.Object: The created pipe joint object.
    """
    bpy.ops.mesh.primitive_cylinder_add(vertices=segments, radius=main_pipe_radius, depth=main_pipe_length, location=(base_location[0], base_location[1] + main_pipe_length / 2, base_location[2]), rotation=(math.pi/2, 0, 0))
    main_cyl = bpy.context.object
    main_cyl.name = f"{name}_Main"
    bpy.ops.mesh.primitive_cylinder_add(vertices=segments, radius=branch_pipe_radius, depth=branch_pipe_length, location=(base_location[0], base_location[1] + main_pipe_length / 2, base_location[2] + branch_pipe_length / 2))
    branch_cyl = bpy.context.object
    branch_cyl.name = f"{name}_Branch"
    if math.isclose(branch_angle_degrees, 90.0):
        branch_cyl.location = (base_location[0], base_location[1] + main_pipe_length, base_location[2] + branch_pipe_length / 2)
    elif math.isclose(branch_angle_degrees, 0.0):
        branch_cyl.location = (base_location[0], base_location[1] + main_pipe_length / 2, base_location[2] + main_pipe_radius + branch_pipe_length / 2)
    else:
        branch_cyl.location = (base_location[0], base_location[1] + main_pipe_length / 2, base_location[2] + main_pipe_radius + branch_pipe_length / 2)
        branch_cyl.rotation_euler.rotate_axis('X', math.radians(branch_angle_degrees))
    bpy.context.view_layer.objects.active = main_cyl
    main_cyl.select_set(True)
    branch_cyl.select_set(True)
    bool_mod = main_cyl.modifiers.new(name="BranchUnion", type='BOOLEAN')
    bool_mod.object = branch_cyl
    bool_mod.operation = 'UNION'
    bool_mod.solver = 'FAST'
    try: bpy.ops.object.modifier_apply({'object': main_cyl}, modifier=bool_mod.name)
    except RuntimeError as e:
        print(f"Error applying boolean for {name}: {e}.")
        # If boolean fails, parent instead of erroring out completely, or just return main_cyl
        # branch_cyl.parent = main_cyl # Optional: parent if union fails
        return main_cyl
    if branch_cyl.name in bpy.data.objects: bpy.data.objects.remove(branch_cyl, do_unlink=True)
    main_cyl.name = name
    bevel_mod = main_cyl.modifiers.new(name="Bevel", type='BEVEL')
    bevel_mod.width = bevel_width
    bevel_mod.segments = bevel_segments
    bevel_mod.limit_method = 'ANGLE'
    return main_cyl

def create_simple_tree(name="SimpleTree", trunk_height=3.0, trunk_radius_bottom=0.3, trunk_radius_top=0.2, canopy_type='sphere', canopy_radius=1.5, canopy_elements=5, canopy_subdivisions=2, base_location=(0,0,0)):
    """
    Creates a simple tree with a tapered trunk and choice of canopy.
    Intended for use by an LLM via the 'execute_code' command.
    Parameters: (omitted for brevity)
    Returns: bpy.types.Object: The main parent object of the tree.
    """
    trunk_location = (base_location[0], base_location[1], base_location[2] + trunk_height / 2)
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=trunk_radius_bottom, radius2=trunk_radius_top, depth=trunk_height, location=trunk_location, end_fill_type='NGON')
    trunk = bpy.context.object
    trunk.name = f"{name}_Trunk"
    canopy_base_z = base_location[2] + trunk_height
    if canopy_type == 'sphere':
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(base_location[0], base_location[1], canopy_base_z))
        canopy_parent = bpy.context.object
        canopy_parent.name = f"{name}_CanopyParent"
        for i in range(canopy_elements):
            offset_radius = canopy_radius * 0.6
            rand_x = base_location[0] + random.uniform(-offset_radius, offset_radius)
            rand_y = base_location[1] + random.uniform(-offset_radius, offset_radius)
            rand_z = canopy_base_z + random.uniform(0, canopy_radius * 0.5)
            current_radius = canopy_radius * random.uniform(0.7, 1.2)
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=canopy_subdivisions, radius=current_radius, location=(rand_x, rand_y, rand_z))
            sphere = bpy.context.object
            sphere.name = f"{name}_CanopySphere_{i+1}"
            displace_mod = sphere.modifiers.new(name="DisplaceCanopy", type='DISPLACE')
            tex_name = f"{name}_CanopyDisplaceTex_{i+1}"
            if tex_name in bpy.data.textures: canopy_displace_tex = bpy.data.textures[tex_name]
            else:
                canopy_displace_tex = bpy.data.textures.new(name=tex_name, type='CLOUDS')
                canopy_displace_tex.noise_scale = current_radius * 0.8
            displace_mod.texture = canopy_displace_tex
            displace_mod.strength = current_radius * 0.2
            sphere.parent = canopy_parent
        canopy_parent.parent = trunk
    elif canopy_type == 'cone_cluster':
        cone_canopy_loc_z = canopy_base_z + canopy_radius * 0.75
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=canopy_radius, radius2=0, depth=canopy_radius*1.5, location=(base_location[0], base_location[1], cone_canopy_loc_z), end_fill_type='NGON')
        cone_canopy = bpy.context.object
        cone_canopy.name = f"{name}_Canopy_Cone"
        cone_canopy.parent = trunk
    trunk.name = name
    bpy.context.view_layer.objects.active = trunk
    trunk.select_set(True)
    return trunk

def create_chain_link(name="ChainLink", link_overall_radius=0.5, link_torus_radius=0.1, main_segments=48, minor_segments=24, base_location=(0,0,0), elongated_scale=(1.5, 1.0, 1.0)):
    """
    Creates a single chain link, potentially elongated, from a torus primitive.
    This function is intended to be called by an LLM via the 'execute_code' command.
    Parameters: (omitted for brevity)
    Returns: bpy.types.Object: The created chain link object.
    """
    bpy.ops.mesh.primitive_torus_add(major_radius=link_overall_radius, minor_radius=link_torus_radius, major_segments=main_segments, minor_segments=minor_segments, location=base_location, align='WORLD')
    link = bpy.context.object
    link.name = name
    link.scale[0] *= elongated_scale[0]
    link.scale[1] *= elongated_scale[1]
    link.scale[2] *= elongated_scale[2]
    if bpy.context.view_layer.objects.active != link:
        bpy.ops.object.select_all(action='DESELECT')
        link.select_set(True)
        bpy.context.view_layer.objects.active = link
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return link

def add_detail_shape(
    target_object_name: str,
    shape_type: str = 'SPHERE',
    operation: str = 'DIFFERENCE',
    shape_size: tuple = (0.2,),
    location: tuple = (0,0,0),
    orientation_euler_degrees: tuple = (0,0,0),
    segments: int = 32
):
    """
    Adds a detail to a target object by creating a primitive shape and
    performing a boolean operation. Intended for use by an LLM via 'execute_code'.

    Parameters:
    - target_object_name (str): Name of the existing object to modify.
    - shape_type (str): Type of primitive to create ('SPHERE', 'CUBE', 'CYLINDER').
    - operation (str): Boolean operation ('DIFFERENCE', 'UNION', 'INTERSECT').
    - shape_size (tuple): Dimensions of the primitive.
        - For 'SPHERE': (radius,) e.g., (0.5,).
        - For 'CUBE': (size,) e.g., (1.0,). (Uses this for X,Y,Z dimensions of the cube).
        - For 'CYLINDER': (radius, depth), e.g., (0.3, 1.0).
    - location (tuple): World-space (x,y,z) for the center of the primitive.
    - orientation_euler_degrees (tuple): (rx,ry,rz) Euler rotation in degrees for the primitive.
    - segments (int): Number of segments for spheres or cylinders.

    Returns:
    - dict: A status dictionary, e.g.,
             {"status": "success", "message": "Operation completed."} or
             {"status": "error", "message": "Error details."}
    """
    target_obj = bpy.data.objects.get(target_object_name)
    if not target_obj: return {"status": "error", "message": f"Target object '{target_object_name}' not found."}
    if target_obj.type != 'MESH': return {"status": "error", "message": f"Target object '{target_object_name}' is not a mesh."}
    orientation_radians = tuple(math.radians(angle) for angle in orientation_euler_degrees)
    detail_obj = None
    if bpy.context.object_mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    try:
        if shape_type == 'SPHERE':
            if not shape_size or len(shape_size) < 1: return {"status": "error", "message": "shape_size must provide (radius,) for SPHERE."}
            bpy.ops.mesh.primitive_uv_sphere_add(radius=shape_size[0], segments=segments, ring_count=segments // 2, location=location, rotation=orientation_radians)
        elif shape_type == 'CUBE':
            if not shape_size or len(shape_size) < 1: return {"status": "error", "message": "shape_size must provide (size,) for CUBE."}
            bpy.ops.mesh.primitive_cube_add(size=shape_size[0], location=location, rotation=orientation_radians)
        elif shape_type == 'CYLINDER':
            if not shape_size or len(shape_size) < 2: return {"status": "error", "message": "shape_size must provide (radius, depth) for CYLINDER."}
            bpy.ops.mesh.primitive_cylinder_add(radius=shape_size[0], depth=shape_size[1], vertices=segments, location=location, rotation=orientation_radians)
        else: return {"status": "error", "message": f"Unsupported shape_type: '{shape_type}'. Supported: SPHERE, CUBE, CYLINDER."}
        detail_obj = bpy.context.object
        if detail_obj is None: return {"status": "error", "message": "Failed to create detail shape primitive."}
        detail_obj.name = f"{target_object_name}_detail_shape_temp"
    except Exception as e:
        if detail_obj and detail_obj.name in bpy.data.objects: bpy.data.objects.remove(detail_obj, do_unlink=True)
        return {"status": "error", "message": f"Error creating primitive '{shape_type}': {str(e)}"}
    try:
        bpy.ops.object.select_all(action='DESELECT')
        target_obj.select_set(True)
        bpy.context.view_layer.objects.active = target_obj
        bool_mod = target_obj.modifiers.new(name="DetailBoolean", type='BOOLEAN')
        bool_mod.object = detail_obj
        bool_mod.operation = operation
        bool_mod.solver = 'FAST'
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        if detail_obj.name in bpy.data.objects: bpy.data.objects.remove(detail_obj, do_unlink=True)
        return {"status": "success", "message": f"Boolean '{operation}' with shape '{shape_type}' completed on '{target_object_name}'."}
    except Exception as e:
        if detail_obj and detail_obj.name in bpy.data.objects: bpy.data.objects.remove(detail_obj, do_unlink=True)
        return {"status": "error", "message": f"Boolean operation failed: {str(e)}"}
# --- End Utility Functions ---
