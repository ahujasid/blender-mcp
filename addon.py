# Blender MCP Addon
# Code created by Siddharth Ahuja: www.github.com/ahujasid © 2025
# This addon connects Blender to various Large Language Models (LLMs) via the MCP server,
# allowing for scene analysis, asset integration (Poly Haven, Hyper3D), and includes
# a screenshot history feature for visual context during LLM interactions.

import bpy
import mathutils
import math # Added import math
import random # Added import random
import json
import threading
import socket
import time
import requests
import tempfile
import traceback
import os
import shutil
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty
import io
from contextlib import redirect_stdout
from pathlib import Path
from datetime import datetime

bl_info = {
    "name": "Blender MCP",
    "author": "BlenderMCP",
    "version": (1, 2),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > BlenderMCP",
    "description": "Connect Blender to Claude via MCP",
    "category": "Interface",
}

RODIN_FREE_TRIAL_KEY = (
    "k9TcfFoEhNd9cCPP2guHAHHHkctZHIRhZDywZ1euGUXwihbYLpOjQhofby80NJez"
)

# --- Screenshot Configuration ---
# Screenshots for history are stored in the user's Blender datafiles directory,
# typically found under: .../Blender/[version]/datafiles/blender_mcp_screenshots/
SCREENSHOT_DIR_PATH = Path(bpy.utils.user_resource('DATAFILES', path="blender_mcp_screenshots"))

def _ensure_screenshot_dir_exists():
    """Ensures the screenshot directory exists."""
    os.makedirs(SCREENSHOT_DIR_PATH, exist_ok=True)

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

    # Subdivision Surface
    subdiv_mod = obj.modifiers.new(name="Subdivision", type='SUBSURF')
    subdiv_mod.levels = subdiv_levels
    subdiv_mod.render_levels = subdiv_levels # Match viewport and render levels

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
    # Check if texture already exists, reuse if so, otherwise create
    if tex_name in bpy.data.textures:
        displace_tex = bpy.data.textures[tex_name]
    else:
        displace_tex = bpy.data.textures.new(name=tex_name, type='CLOUDS')

    displace_mod.texture = displace_tex
    displace_mod.strength = displace_strength
    displace_mod.mid_level = displace_midlevel

    return obj

def create_voronoi_rock(name="Rock", size=1.0, voronoi_scale=1.0, voronoi_randomness=1.0, subdiv_levels=2, smooth_iterations=5, base_location=(0,0,0)):
    """
    Creates a rock-like object using an IcoSphere and Voronoi displacement.
    Intended for use by an LLM via the 'execute_code' command.

    Parameters:
    - name (str): Name for the new rock object.
    - size (float): Approximate overall size of the rock (scales the base IcoSphere radius).
    - voronoi_scale (float): Scale for the Voronoi texture used in displacement.
    - voronoi_randomness (float): 'Intensity' for the Voronoi texture, affecting feature randomness/strength.
    - subdiv_levels (int): Viewport and render subdivision levels for the Subdivision Surface modifier.
    - smooth_iterations (int): Number of iterations for the Smooth modifier.
    - base_location (tuple): (x, y, z) location for the rock.

    Returns:
    bpy.types.Object: The created rock object.
    """
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=size/2, location=base_location) # Using radius for ico_sphere, so size/2
    obj = bpy.context.object
    obj.name = name
    # obj.scale = (size, size, size) # Scaling applied to radius already

    # Displace
    displace_mod = obj.modifiers.new(name="Displace", type='DISPLACE')
    tex_name = f"{name}_VoronoiTex"
    if tex_name in bpy.data.textures:
        voronoi_tex = bpy.data.textures[tex_name]
    else:
        voronoi_tex = bpy.data.textures.new(name=tex_name, type='VORONOI')

    voronoi_tex.noise_scale = voronoi_scale
    # For Voronoi, 'nabla' is not directly 'randomness'.
    # Blender's Voronoi texture has parameters like 'intensity', 'distance_metric', etc.
    # We'll use intensity as a proxy for randomness/strength of displacement features.
    # A common way to control "randomness" is through the noise_scale or by affecting the texture coordinates.
    # For simplicity, we'll map voronoi_randomness to intensity, assuming higher means more varied displacement.
    voronoi_tex.intensity = voronoi_randomness # Using intensity, ensure it's a valid range or map it. Default is 1.0.

    displace_mod.texture = voronoi_tex
    displace_mod.strength = 1.0 # Usually, Voronoi displacement strength is controlled by texture output

    # Subdivision Surface
    subdiv_mod = obj.modifiers.new(name="Subdivision", type='SUBSURF')
    subdiv_mod.levels = subdiv_levels
    subdiv_mod.render_levels = subdiv_levels

    # Smooth
    smooth_mod = obj.modifiers.new(name="Smooth", type='SMOOTH')
    smooth_mod.iterations = smooth_iterations

    return obj

def create_parametric_gear(name="Gear", teeth=12, radius=1.0, addendum=0.1, dedendum=0.125, bevel_width=0.02, bevel_segments=2, solidify_thickness=0.2, base_location=(0,0,0)):
    """
    Creates a gear-like object. Attempts to use the 'Add Mesh: Extra Objects' addon's
    gear primitive. If unavailable or it fails, creates a cylinder placeholder.
    Intended for use by an LLM via the 'execute_code' command.

    Parameters:
    - name (str): Name for the new gear object.
    - teeth (int): Number of teeth for the gear.
    - radius (float): Radius of the gear.
    - addendum (float): Addendum of the gear teeth.
    - dedendum (float): Dedendum of the gear teeth.
    - bevel_width (float): Width for the Bevel modifier.
    - bevel_segments (int): Number of segments for the Bevel modifier.
    - solidify_thickness (float): Thickness for the Solidify modifier (used if gear is 2D or for placeholder).
    - base_location (tuple): (x, y, z) location for the gear.

    Returns:
    bpy.types.Object: The created gear object (or cylinder placeholder).
    """
    obj = None
    text_obj = None
    if hasattr(bpy.ops.mesh, 'primitive_gear_add'):
        try:
            bpy.ops.mesh.primitive_gear_add(
                num_teeth=teeth,
                radius=radius,
                addendum=addendum,
                dedendum=dedendum,
                base_radius=radius - addendum - dedendum, # Example derived parameter
                location=base_location,
                align='WORLD', # Ensure consistent alignment
                # Other params like 'width' (for thickness) might exist, or use solidify
            )
            obj = bpy.context.object
            obj.name = name
            # If gear has its own thickness/width, solidify might be redundant or need adjustment
            # For now, we assume it creates a 2D profile that needs solidification
        except TypeError as e:
            print(f"Error calling primitive_gear_add (likely due to version differences in params): {e}")
            obj = None # Ensure obj is None if creation failed

    if obj is None: # Fallback if primitive_gear_add doesn't exist or failed
        print("Add Mesh: Extra Objects (primitive_gear_add) not available or failed. Creating a cylinder placeholder.")
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=teeth * 2, # Make it somewhat gear-like
            radius=radius,
            depth=solidify_thickness, # Use solidify_thickness for depth here
            location=base_location,
            end_fill_type='NGON'
        )
        obj = bpy.context.object
        obj.name = name

        # Add a text object indicating it's a placeholder
        text_loc = (base_location[0], base_location[1], base_location[2] + radius + 0.2)
        bpy.ops.object.text_add(location=text_loc)
        text_obj = bpy.context.object
        text_obj.data.body = f"Gear Placeholder (Extra Objects addon disabled or failed)"
        text_obj.scale = (0.3, 0.3, 0.3) # Make text smaller
        text_obj.parent = obj # Parent it for clarity

    if obj: # Apply modifiers if we have a mesh object
        # Bevel
        bevel_mod = obj.modifiers.new(name="Bevel", type='BEVEL')
        bevel_mod.width = bevel_width
        bevel_mod.segments = bevel_segments
        bevel_mod.limit_method = 'ANGLE' # Good for gears

        # Solidify (might be redundant if gear addon creates thickness)
        # Check if object already has volume before adding solidify
        is_2d_profile = True # Assume it's 2D initially
        if obj.type == 'MESH' and len(obj.data.polygons) > 0:
            # A simple check: if all Z coords of vertices are very close, it might be flat
            # This is a heuristic and might not be perfect.
            verts = [v.co.z for v in obj.data.vertices]
            if verts:
                min_z, max_z = min(verts), max(verts)
                if (max_z - min_z) > 0.001: # If there's some depth
                    is_2d_profile = False

        if is_2d_profile: # Only add solidify if it seems like a 2D profile
             solidify_mod = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
             solidify_mod.thickness = solidify_thickness
        elif not hasattr(bpy.ops.mesh, 'primitive_gear_add') or text_obj: # If it's the cylinder placeholder
            # The cylinder placeholder already has depth from primitive_cylinder_add
            pass # Don't add another solidify if it's the placeholder cylinder
        else: # Gear from addon likely has its own thickness parameter
            print(f"Gear '{name}' might have its own thickness. Solidify modifier skipped or may need adjustment.")


    return obj # Return the main gear object, not the text placeholder if it exists

def create_pipe_joint(name="PipeJoint", main_pipe_radius=0.5, main_pipe_length=2.0, branch_pipe_radius=0.3, branch_pipe_length=1.5, branch_angle_degrees=90.0, segments=32, bevel_width=0.05, bevel_segments=3, base_location=(0,0,0)):
    """
    Creates a pipe joint using two cylinders and a boolean union.
    Intended for use by an LLM via the 'execute_code' command.

    The main pipe is aligned along the Y-axis by default.
    The branch pipe's position and rotation are calculated for a T-junction
    if branch_angle_degrees is 0, or an L-junction if 90 degrees (coming off the +Y end, bending towards +Z).
    More complex angles/positions might require careful parameter adjustment by the LLM.

    Parameters:
    - name (str): Name for the new pipe joint object.
    - main_pipe_radius (float): Radius of the main pipe.
    - main_pipe_length (float): Length of the main pipe.
    - branch_pipe_radius (float): Radius of the branch pipe.
    - branch_pipe_length (float): Length of the branch pipe.
    - branch_angle_degrees (float): Angle of the branch pipe relative to the main pipe's direction.
                                     0 for T-junction, 90 for L-junction.
    - segments (int): Number of vertices for the cylinders.
    - bevel_width (float): Width for the Bevel modifier on the final joint.
    - bevel_segments (int): Number of segments for the Bevel modifier.
    - base_location (tuple): (x, y, z) base location for the joint.

    Returns:
    bpy.types.Object: The created pipe joint object.
    """
    # Main Cylinder (aligned along Y-axis)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=segments,
        radius=main_pipe_radius,
        depth=main_pipe_length,
        location=(base_location[0], base_location[1] + main_pipe_length / 2, base_location[2]), # Centered for this example
        rotation=(math.pi/2, 0, 0) # Rotate to align with Y-axis
    )
    main_cyl = bpy.context.object
    main_cyl.name = f"{name}_Main"

    # Branch Cylinder (initially aligned along Z-axis)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=segments,
        radius=branch_pipe_radius,
        depth=branch_pipe_length,
        location=(base_location[0], base_location[1] + main_pipe_length / 2, base_location[2] + branch_pipe_length / 2) # Default position before rotation
    )
    branch_cyl = bpy.context.object
    branch_cyl.name = f"{name}_Branch"

    # Position and rotate branch cylinder
    # For a 90-degree L-bend from the +Y end of main_cyl, pointing towards +Z:
    # The main cylinder's effective "end" is at base_location[1] + main_pipe_length.
    # For simplicity, this example creates a T-junction if angle is 0, or an L-bend.
    # More complex scenarios would require more sophisticated positioning logic.

    if math.isclose(branch_angle_degrees, 90.0):
        # L-junction: Branch comes off the +Y end of the main pipe, pointing towards +Z
        # Move branch origin to its base
        branch_cyl.location = (
            base_location[0],
            base_location[1] + main_pipe_length, # At the end of the main pipe
            base_location[2] + branch_pipe_length / 2 # Centered on its own length
        )
        # Rotation for L-bend (already Z-aligned, no further rotation needed if main is Y aligned)
        # If it needed to bend in XY plane from Y-main, it would be rotation around Z.
        # If it needs to bend in ZY plane (up/down) from Y-main, it's rotation around X.
        # This example assumes branch points "up" (+Z) from a Y-aligned main pipe.
        # Default cylinder is Z-aligned.

    elif math.isclose(branch_angle_degrees, 0.0):
        # T-junction: Branch comes from the center of the main pipe, pointing towards +Z
        branch_cyl.location = (
            base_location[0],
            base_location[1] + main_pipe_length / 2, # Center of the main pipe
            base_location[2] + main_pipe_radius + branch_pipe_length / 2 # Offset by main_pipe_radius
        )
    else:
        # General case: position at center of main pipe, then rotate
        # This is a simplified approach; true angled joints require more complex geometry/positioning
        branch_cyl.location = (
            base_location[0],
            base_location[1] + main_pipe_length / 2,
            base_location[2] + main_pipe_radius + branch_pipe_length / 2
        )
        branch_cyl.rotation_euler.rotate_axis('X', math.radians(branch_angle_degrees))


    # Boolean Union
    bpy.context.view_layer.objects.active = main_cyl
    main_cyl.select_set(True)
    branch_cyl.select_set(True) # Select both for some boolean solvers, though modifier uses object field

    bool_mod = main_cyl.modifiers.new(name="BranchUnion", type='BOOLEAN')
    bool_mod.object = branch_cyl
    bool_mod.operation = 'UNION'
    bool_mod.solver = 'FAST' # 'EXACT' can be slower but more robust for complex cases

    try:
        bpy.ops.object.modifier_apply({'object': main_cyl}, modifier=bool_mod.name)
    except RuntimeError as e:
        print(f"Error applying boolean modifier for {name}: {e}. The objects will be left separate.")
        # Optionally, could parent here or leave as is
        return main_cyl # Return main cylinder even if boolean fails, so something is returned

    # Delete the separate branch object as it's now part of main_cyl
    # Ensure branch_cyl is still valid and in current context if boolean failed and we didn't return
    if branch_cyl.name in bpy.data.objects: # Check if it still exists
        bpy.data.objects.remove(branch_cyl, do_unlink=True)

    main_cyl.name = name # Rename the resulting object

    # Bevel Modifier on the final joined mesh
    bevel_mod = main_cyl.modifiers.new(name="Bevel", type='BEVEL')
    bevel_mod.width = bevel_width
    bevel_mod.segments = bevel_segments
    bevel_mod.limit_method = 'ANGLE' # Often good for preventing bevels on flat surfaces

    return main_cyl

def create_simple_tree(name="SimpleTree", trunk_height=3.0, trunk_radius_bottom=0.3, trunk_radius_top=0.2, canopy_type='sphere', canopy_radius=1.5, canopy_elements=5, canopy_subdivisions=2, base_location=(0,0,0)):
    """
    Creates a simple tree with a tapered trunk and a choice of canopy styles.
    Intended for use by an LLM via the 'execute_code' command.

    Parameters:
    - name (str): Name for the new tree (overall parent object if applicable).
    - trunk_height (float): Height of the tree trunk.
    - trunk_radius_bottom (float): Radius of the trunk at its base.
    - trunk_radius_top (float): Radius of the trunk at its top.
    - canopy_type (str): Type of canopy. Options: 'sphere', 'cone_cluster'.
    - canopy_radius (float): Radius of the main canopy element(s).
    - canopy_elements (int): Number of elements for 'sphere' canopy (clustered icospheres).
                           For 'cone_cluster', this might represent number of cones (currently simplified to 1).
    - canopy_subdivisions (int): Subdivisions for icospheres in 'sphere' canopy.
    - base_location (tuple): (x, y, z) base location for the trunk.

    Returns:
    bpy.types.Object: The main parent object of the tree (usually the trunk or a canopy parent).
    """

    # Trunk (using a cone for simplicity of tapering)
    trunk_location = (base_location[0], base_location[1], base_location[2] + trunk_height / 2)
    bpy.ops.mesh.primitive_cone_add(
        vertices=16,
        radius1=trunk_radius_bottom,
        radius2=trunk_radius_top,
        depth=trunk_height,
        location=trunk_location,
        end_fill_type='NGON'
    )
    trunk = bpy.context.object
    trunk.name = f"{name}_Trunk"

    canopy_parent_object = trunk # Default parent is trunk
    canopy_base_z = base_location[2] + trunk_height

    if canopy_type == 'sphere':
        # Create an Empty to parent sphere elements for easier manipulation if needed
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(base_location[0], base_location[1], canopy_base_z))
        canopy_parent = bpy.context.object
        canopy_parent.name = f"{name}_CanopyParent"

        for i in range(canopy_elements):
            # Calculate somewhat random offset, ensuring spheres are mostly above canopy_base_z
            offset_radius = canopy_radius * 0.6 # How far spheres can spread
            rand_x = base_location[0] + random.uniform(-offset_radius, offset_radius)
            rand_y = base_location[1] + random.uniform(-offset_radius, offset_radius)
            # Ensure Z is mostly positive relative to canopy_base_z, but allow some overlap
            rand_z = canopy_base_z + random.uniform(0, canopy_radius * 0.5)

            current_radius = canopy_radius * random.uniform(0.7, 1.2)

            bpy.ops.mesh.primitive_ico_sphere_add(
                subdivisions=canopy_subdivisions,
                radius=current_radius,
                location=(rand_x, rand_y, rand_z)
            )
            sphere = bpy.context.object
            sphere.name = f"{name}_CanopySphere_{i+1}"

            # Optional: Add simple displace for variation
            displace_mod = sphere.modifiers.new(name="DisplaceCanopy", type='DISPLACE')
            tex_name = f"{name}_CanopyDisplaceTex_{i+1}"
            if tex_name in bpy.data.textures:
                canopy_displace_tex = bpy.data.textures[tex_name]
            else:
                canopy_displace_tex = bpy.data.textures.new(name=tex_name, type='CLOUDS')
                canopy_displace_tex.noise_scale = current_radius * 0.8 # Scale texture to sphere size
            displace_mod.texture = canopy_displace_tex
            displace_mod.strength = current_radius * 0.2 # Displacement relative to sphere size

            # Parent sphere to the canopy_parent Empty
            sphere.parent = canopy_parent

        canopy_parent.parent = trunk # Parent the empty (with spheres) to the trunk
        canopy_parent_object = canopy_parent # The empty is now the main canopy object

    elif canopy_type == 'cone_cluster': # Simplified to one large cone for now
        cone_canopy_loc_z = canopy_base_z + canopy_radius * 0.75 # Base of cone canopy slightly above trunk top
        bpy.ops.mesh.primitive_cone_add(
            vertices=16,
            radius1=canopy_radius,
            radius2=0, # Pointy top
            depth=canopy_radius * 1.5,
            location=(base_location[0], base_location[1], cone_canopy_loc_z),
            end_fill_type='NGON'
        )
        cone_canopy = bpy.context.object
        cone_canopy.name = f"{name}_Canopy_Cone"
        cone_canopy.parent = trunk
        canopy_parent_object = cone_canopy

    # Final naming and selection
    # If we used an empty for canopy elements, that empty is parented to trunk.
    # The trunk is the ultimate root of this specific tree structure.
    trunk.name = name # Rename the trunk to the main desired name

    # Ensure the main trunk (which is the root) is the active object to be returned implicitly by ops
    bpy.context.view_layer.objects.active = trunk
    trunk.select_set(True)

    return trunk

def create_chain_link(name="ChainLink", link_overall_radius=0.5, link_torus_radius=0.1, main_segments=48, minor_segments=24, base_location=(0,0,0), elongated_scale=(1.5, 1.0, 1.0)):
    """
    Creates a single chain link, potentially elongated.
    Intended for use by an LLM via the 'execute_code' command.

    Parameters:
    - name (str): Name for the new chain link object.
    - link_overall_radius (float): Major radius of the torus.
    - link_torus_radius (float): Minor radius (thickness) of the torus.
    - main_segments (int): Number of segments for the major radius.
    - minor_segments (int): Number of segments for the minor radius.
    - base_location (tuple): (x, y, z) location for the chain link.
    - elongated_scale (tuple): (x, y, z) scale factors to make the link elongated.
                               (1.0, 1.0, 1.0) for a perfect torus ring.
                               (e.g., 1.5, 1.0, 1.0) stretches it along its local X-axis.
    Returns:
    bpy.types.Object: The created chain link object.
    """
    bpy.ops.mesh.primitive_torus_add(
        major_radius=link_overall_radius,
        minor_radius=link_torus_radius,
        major_segments=main_segments,
        minor_segments=minor_segments,
        location=base_location
    )
    link = bpy.context.object
    link.name = name

    # Apply elongation scale
    link.scale[0] *= elongated_scale[0]
    link.scale[1] *= elongated_scale[1]
    link.scale[2] *= elongated_scale[2]

    # Apply the scale to the mesh data
    # Store active object to restore it later if needed, though primitive_torus_add should set it.
    active_obj = bpy.context.view_layer.objects.active
    bpy.context.view_layer.objects.active = link # Ensure link is active
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.context.view_layer.objects.active = active_obj # Restore active object

    return link

def create_chain_link(name="ChainLink", link_overall_radius=0.5, link_torus_radius=0.1, main_segments=48, minor_segments=24, base_location=(0,0,0), elongated_scale=(1.5, 1.0, 1.0)):
    """
    Creates a single chain link, potentially elongated, from a torus primitive.
    This function is intended to be called by an LLM via the 'execute_code' command.

    Parameters:
    - name (str): Name for the new chain link object.
    - link_overall_radius (float): Major radius of the torus (overall size of the link).
    - link_torus_radius (float): Minor radius of the torus (thickness of the link's wire).
    - main_segments (int): Number of segments for the major radius (around the torus).
    - minor_segments (int): Number of segments for the minor radius (around the wire).
    - base_location (tuple): (x, y, z) world-space location for the chain link's origin.
    - elongated_scale (tuple): (x, y, z) scale factors applied to make the link elongated.
                               A value of (1.0, 1.0, 1.0) results in a standard circular torus.
                               For example, (1.5, 1.0, 1.0) stretches the link along its local X-axis.
                               The scale is applied to the object and then baked into the mesh data.
    Returns:
    bpy.types.Object: The created and potentially elongated chain link object.
    """
    bpy.ops.mesh.primitive_torus_add(
        major_radius=link_overall_radius,
        minor_radius=link_torus_radius,
        major_segments=main_segments,
        minor_segments=minor_segments,
        location=base_location,
        align='WORLD' # Align to world, rotation can be applied later if needed
    )
    link = bpy.context.object
    link.name = name

    # Apply elongation scale relative to current object scale
    link.scale[0] *= elongated_scale[0]
    link.scale[1] *= elongated_scale[1]
    link.scale[2] *= elongated_scale[2]

    # Apply the scale to the mesh data to make it the new base shape
    # This is important for consistent behavior if this link is arrayed or further transformed.
    # Need to ensure the object is active and selected for transform_apply.
    if bpy.context.view_layer.objects.active != link:
        bpy.ops.object.select_all(action='DESELECT')
        link.select_set(True)
        bpy.context.view_layer.objects.active = link

    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    return link
# --- End Utility Functions ---


class BlenderMCPServer:
    def __init__(self, host="localhost", port=9876):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.server_thread = None

    def start(self):
        if self.running:
            print("Server is already running")
            return

        self.running = True

        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)

            # Start server thread
            self.server_thread = threading.Thread(target=self._server_loop)
            self.server_thread.daemon = True
            self.server_thread.start()

            print(f"BlenderMCP server started on {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to start server: {str(e)}")
            self.stop()

    def stop(self):
        self.running = False

        # Close socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

        # Wait for thread to finish
        if self.server_thread:
            try:
                if self.server_thread.is_alive():
                    self.server_thread.join(timeout=1.0)
            except:
                pass
            self.server_thread = None

        print("BlenderMCP server stopped")

    def _server_loop(self):
        """Main server loop in a separate thread"""
        print("Server thread started")
        self.socket.settimeout(1.0)  # Timeout to allow for stopping

        while self.running:
            try:
                # Accept new connection
                try:
                    client, address = self.socket.accept()
                    print(f"Connected to client: {address}")

                    # Handle client in a separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client, args=(client,)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except socket.timeout:
                    # Just check running condition
                    continue
                except Exception as e:
                    print(f"Error accepting connection: {str(e)}")
                    time.sleep(0.5)
            except Exception as e:
                print(f"Error in server loop: {str(e)}")
                if not self.running:
                    break
                time.sleep(0.5)

        print("Server thread stopped")

    def _handle_client(self, client):
        """Handle connected client"""
        print("Client handler started")
        client.settimeout(None)  # No timeout
        buffer = b""

        try:
            while self.running:
                # Receive data
                try:
                    data = client.recv(8192)
                    if not data:
                        print("Client disconnected")
                        break

                    buffer += data
                    try:
                        # Try to parse command
                        command = json.loads(buffer.decode("utf-8"))
                        buffer = b""

                        # Execute command in Blender's main thread
                        def execute_wrapper():
                            try:
                                response = self.execute_command(command)
                                response_json = json.dumps(response)
                                try:
                                    client.sendall(response_json.encode("utf-8"))
                                except:
                                    print(
                                        "Failed to send response - client disconnected"
                                    )
                            except Exception as e:
                                print(f"Error executing command: {str(e)}")
                                traceback.print_exc()
                                try:
                                    error_response = {
                                        "status": "error",
                                        "message": str(e),
                                    }
                                    client.sendall(
                                        json.dumps(error_response).encode("utf-8")
                                    )
                                except:
                                    pass
                            return None

                        # Schedule execution in main thread
                        bpy.app.timers.register(execute_wrapper, first_interval=0.0)
                    except json.JSONDecodeError:
                        # Incomplete data, wait for more
                        pass
                except Exception as e:
                    print(f"Error receiving data: {str(e)}")
                    break
        except Exception as e:
            print(f"Error in client handler: {str(e)}")
        finally:
            try:
                client.close()
            except:
                pass
            print("Client handler stopped")

    def execute_command(self, command):
        """Execute a command in the main Blender thread"""
        try:
            return self._execute_command_internal(command)

        except Exception as e:
            print(f"Error executing command: {str(e)}")
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    def _execute_command_internal(self, command):
        """Internal command execution with proper context"""
        cmd_type = command.get("type")
        params = command.get("params", {})

        # Add a handler for checking PolyHaven status
        if cmd_type == "get_polyhaven_status":
            return {"status": "success", "result": self.get_polyhaven_status()}

        # Base handlers that are always available
        handlers = {
            "get_scene_info": self.get_scene_info,
            "get_object_info": self.get_object_info,
            "execute_code": self.execute_code,
            "get_polyhaven_status": self.get_polyhaven_status,
            "get_hyper3d_status": self.get_hyper3d_status,
            "import_model_from_path": self.import_model_from_path,
            "get_mesh_details": self.get_mesh_details, # Added this line
        }

        # Add Polyhaven handlers only if enabled
        if bpy.context.scene.blendermcp_use_polyhaven:
            polyhaven_handlers = {
                "get_polyhaven_categories": self.get_polyhaven_categories,
                "search_polyhaven_assets": self.search_polyhaven_assets,
                "download_polyhaven_asset": self.download_polyhaven_asset,
                "set_texture": self.set_texture,
            }
            handlers.update(polyhaven_handlers)

        # Add Hyper3d handlers only if enabled
        if bpy.context.scene.blendermcp_use_hyper3d:
            polyhaven_handlers = {
                "create_rodin_job": self.create_rodin_job,
                "poll_rodin_job_status": self.poll_rodin_job_status,
                "import_generated_asset": self.import_generated_asset,
            }
            handlers.update(polyhaven_handlers)

        handler = handlers.get(cmd_type)
        if handler:
            try:
                print(f"Executing handler for {cmd_type}")
                result = handler(**params)
                print(f"Handler execution complete")
                return {"status": "success", "result": result}
            except Exception as e:
                print(f"Error in handler: {str(e)}")
                traceback.print_exc()
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": f"Unknown command type: {cmd_type}"}

    def get_scene_info(self):
        """Get information about the current Blender scene"""
        try:
            print("Getting scene info...")
            # Simplify the scene info to reduce data size
            scene_info = {
                "name": bpy.context.scene.name,
                "object_count": len(bpy.context.scene.objects),
                "objects": [],
                "materials_count": len(bpy.data.materials),
            }

            # Collect minimal object information (limit to first 10 objects)
            for i, obj in enumerate(bpy.context.scene.objects):
                if i >= 10:  # Reduced from 20 to 10
                    break

                obj_info = {
                    "name": obj.name,
                    "type": obj.type,
                    # Only include basic location data
                    "location": [
                        round(float(obj.location.x), 2),
                        round(float(obj.location.y), 2),
                        round(float(obj.location.z), 2),
                    ],
                }
                scene_info["objects"].append(obj_info)

            print(f"Scene info collected: {len(scene_info['objects'])} objects")
            return scene_info
        except Exception as e:
            print(f"Error in get_scene_info: {str(e)}")
            traceback.print_exc()
            return {"error": str(e)}

    @staticmethod
    def _get_aabb(obj):
        """Returns the world-space axis-aligned bounding box (AABB) of an object."""
        if obj.type != "MESH":
            raise TypeError("Object must be a mesh")

        # Get the bounding box corners in local space
        local_bbox_corners = [mathutils.Vector(corner) for corner in obj.bound_box]

        # Convert to world coordinates
        world_bbox_corners = [
            obj.matrix_world @ corner for corner in local_bbox_corners
        ]

        # Compute axis-aligned min/max coordinates
        min_corner = mathutils.Vector(map(min, zip(*world_bbox_corners)))
        max_corner = mathutils.Vector(map(max, zip(*world_bbox_corners)))

        return [[*min_corner], [*max_corner]]

    def get_object_info(self, name):
        """Get detailed information about a specific object"""
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")

        # Basic object info
        obj_info = {
            "name": obj.name,
            "type": obj.type,
            "location": [obj.location.x, obj.location.y, obj.location.z],
            "rotation": [
                obj.rotation_euler.x,
                obj.rotation_euler.y,
                obj.rotation_euler.z,
            ],
            "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            "visible": obj.visible_get(),
            "materials": [],
        }

        if obj.type == "MESH":
            bounding_box = self._get_aabb(obj)
            obj_info["world_bounding_box"] = bounding_box

        # Add material slots
        for slot in obj.material_slots:
            if slot.material:
                obj_info["materials"].append(slot.material.name)

        # Add mesh data if applicable
        if obj.type == "MESH" and obj.data:
            mesh = obj.data
            obj_info["mesh"] = {
                "vertices": len(mesh.vertices),
                "edges": len(mesh.edges),
                "polygons": len(mesh.polygons),
            }

        return obj_info

    def execute_code(self, code):
        """Execute arbitrary Blender Python code"""
        # This is powerful but potentially dangerous - use with caution
        try:
            # Create a local namespace for execution
            namespace = {
                "bpy": bpy,
                "create_modified_cube": create_modified_cube,
                "create_voronoi_rock": create_voronoi_rock,
                "create_parametric_gear": create_parametric_gear,
                "create_pipe_joint": create_pipe_joint,
                "create_simple_tree": create_simple_tree,
                "create_chain_link": create_chain_link
            }

            # Capture stdout during execution, and return it as result
            capture_buffer = io.StringIO()
            with redirect_stdout(capture_buffer):
                exec(code, namespace)

            captured_output = capture_buffer.getvalue()
            return {"executed": True, "result": captured_output}
        except Exception as e:
            raise Exception(f"Code execution error: {str(e)}")

    def get_polyhaven_categories(self, asset_type):
        """Get categories for a specific asset type from Polyhaven"""
        try:
            if asset_type not in ["hdris", "textures", "models", "all"]:
                return {
                    "error": f"Invalid asset type: {asset_type}. Must be one of: hdris, textures, models, all"
                }

            response = requests.get(
                f"https://api.polyhaven.com/categories/{asset_type}"
            )
            if response.status_code == 200:
                return {"categories": response.json()}
            else:
                return {
                    "error": f"API request failed with status code {response.status_code}"
                }
        except Exception as e:
            return {"error": str(e)}

    def search_polyhaven_assets(self, asset_type=None, categories=None):
        """Search for assets from Polyhaven with optional filtering"""
        try:
            url = "https://api.polyhaven.com/assets"
            params = {}

            if asset_type and asset_type != "all":
                if asset_type not in ["hdris", "textures", "models"]:
                    return {
                        "error": f"Invalid asset type: {asset_type}. Must be one of: hdris, textures, models, all"
                    }
                params["type"] = asset_type

            if categories:
                params["categories"] = categories

            response = requests.get(url, params=params)
            if response.status_code == 200:
                # Limit the response size to avoid overwhelming Blender
                assets = response.json()
                # Return only the first 20 assets to keep response size manageable
                limited_assets = {}
                for i, (key, value) in enumerate(assets.items()):
                    if i >= 20:  # Limit to 20 assets
                        break
                    limited_assets[key] = value

                return {
                    "assets": limited_assets,
                    "total_count": len(assets),
                    "returned_count": len(limited_assets),
                }
            else:
                return {
                    "error": f"API request failed with status code {response.status_code}"
                }
        except Exception as e:
            return {"error": str(e)}

    def download_polyhaven_asset(
        self, asset_id, asset_type, resolution="1k", file_format=None
    ):
        try:
            # First get the files information
            files_response = requests.get(f"https://api.polyhaven.com/files/{asset_id}")
            if files_response.status_code != 200:
                return {
                    "error": f"Failed to get asset files: {files_response.status_code}"
                }

            files_data = files_response.json()

            # Handle different asset types
            if asset_type == "hdris":
                # For HDRIs, download the .hdr or .exr file
                if not file_format:
                    file_format = "hdr"  # Default format for HDRIs

                if (
                    "hdri" in files_data
                    and resolution in files_data["hdri"]
                    and file_format in files_data["hdri"][resolution]
                ):
                    file_info = files_data["hdri"][resolution][file_format]
                    file_url = file_info["url"]

                    # For HDRIs, we need to save to a temporary file first
                    # since Blender can't properly load HDR data directly from memory
                    with tempfile.NamedTemporaryFile(
                        suffix=f".{file_format}", delete=False
                    ) as tmp_file:
                        # Download the file
                        response = requests.get(file_url)
                        if response.status_code != 200:
                            return {
                                "error": f"Failed to download HDRI: {response.status_code}"
                            }

                        tmp_file.write(response.content)
                        tmp_path = tmp_file.name

                    try:
                        # Create a new world if none exists
                        if not bpy.data.worlds:
                            bpy.data.worlds.new("World")

                        world = bpy.data.worlds[0]
                        world.use_nodes = True
                        node_tree = world.node_tree

                        # Clear existing nodes
                        for node in node_tree.nodes:
                            node_tree.nodes.remove(node)

                        # Create nodes
                        tex_coord = node_tree.nodes.new(type="ShaderNodeTexCoord")
                        tex_coord.location = (-800, 0)

                        mapping = node_tree.nodes.new(type="ShaderNodeMapping")
                        mapping.location = (-600, 0)

                        # Load the image from the temporary file
                        env_tex = node_tree.nodes.new(type="ShaderNodeTexEnvironment")
                        env_tex.location = (-400, 0)
                        env_tex.image = bpy.data.images.load(tmp_path)

                        # Use a color space that exists in all Blender versions
                        if file_format.lower() == "exr":
                            # Try to use Linear color space for EXR files
                            try:
                                env_tex.image.colorspace_settings.name = "Linear"
                            except:
                                # Fallback to Non-Color if Linear isn't available
                                env_tex.image.colorspace_settings.name = "Non-Color"
                        else:  # hdr
                            # For HDR files, try these options in order
                            for color_space in [
                                "Linear",
                                "Linear Rec.709",
                                "Non-Color",
                            ]:
                                try:
                                    env_tex.image.colorspace_settings.name = color_space
                                    break  # Stop if we successfully set a color space
                                except:
                                    continue

                        background = node_tree.nodes.new(type="ShaderNodeBackground")
                        background.location = (-200, 0)

                        output = node_tree.nodes.new(type="ShaderNodeOutputWorld")
                        output.location = (0, 0)

                        # Connect nodes
                        node_tree.links.new(
                            tex_coord.outputs["Generated"], mapping.inputs["Vector"]
                        )
                        node_tree.links.new(
                            mapping.outputs["Vector"], env_tex.inputs["Vector"]
                        )
                        node_tree.links.new(
                            env_tex.outputs["Color"], background.inputs["Color"]
                        )
                        node_tree.links.new(
                            background.outputs["Background"], output.inputs["Surface"]
                        )

                        # Set as active world
                        bpy.context.scene.world = world

                        # Clean up temporary file
                        try:
                            tempfile._cleanup()  # This will clean up all temporary files
                        except:
                            pass

                        return {
                            "success": True,
                            "message": f"HDRI {asset_id} imported successfully",
                            "image_name": env_tex.image.name,
                        }
                    except Exception as e:
                        return {"error": f"Failed to set up HDRI in Blender: {str(e)}"}
                else:
                    return {
                        "error": f"Requested resolution or format not available for this HDRI"
                    }

            elif asset_type == "textures":
                if not file_format:
                    file_format = "jpg"  # Default format for textures

                downloaded_maps = {}

                try:
                    for map_type in files_data:
                        if map_type not in ["blend", "gltf"]:  # Skip non-texture files
                            if (
                                resolution in files_data[map_type]
                                and file_format in files_data[map_type][resolution]
                            ):
                                file_info = files_data[map_type][resolution][
                                    file_format
                                ]
                                file_url = file_info["url"]

                                # Use NamedTemporaryFile like we do for HDRIs
                                with tempfile.NamedTemporaryFile(
                                    suffix=f".{file_format}", delete=False
                                ) as tmp_file:
                                    # Download the file
                                    response = requests.get(file_url)
                                    if response.status_code == 200:
                                        tmp_file.write(response.content)
                                        tmp_path = tmp_file.name

                                        # Load image from temporary file
                                        image = bpy.data.images.load(tmp_path)
                                        image.name = (
                                            f"{asset_id}_{map_type}.{file_format}"
                                        )

                                        # Pack the image into .blend file
                                        image.pack()

                                        # Set color space based on map type
                                        if map_type in ["color", "diffuse", "albedo"]:
                                            try:
                                                image.colorspace_settings.name = "sRGB"
                                            except:
                                                pass
                                        else:
                                            try:
                                                image.colorspace_settings.name = (
                                                    "Non-Color"
                                                )
                                            except:
                                                pass

                                        downloaded_maps[map_type] = image

                                        # Clean up temporary file
                                        try:
                                            os.unlink(tmp_path)
                                        except:
                                            pass

                    if not downloaded_maps:
                        return {
                            "error": f"No texture maps found for the requested resolution and format"
                        }

                    # Create a new material with the downloaded textures
                    mat = bpy.data.materials.new(name=asset_id)
                    mat.use_nodes = True
                    nodes = mat.node_tree.nodes
                    links = mat.node_tree.links

                    # Clear default nodes
                    for node in nodes:
                        nodes.remove(node)

                    # Create output node
                    output = nodes.new(type="ShaderNodeOutputMaterial")
                    output.location = (300, 0)

                    # Create principled BSDF node
                    principled = nodes.new(type="ShaderNodeBsdfPrincipled")
                    principled.location = (0, 0)
                    links.new(principled.outputs[0], output.inputs[0])

                    # Add texture nodes based on available maps
                    tex_coord = nodes.new(type="ShaderNodeTexCoord")
                    tex_coord.location = (-800, 0)

                    mapping = nodes.new(type="ShaderNodeMapping")
                    mapping.location = (-600, 0)
                    mapping.vector_type = (
                        "TEXTURE"  # Changed from default 'POINT' to 'TEXTURE'
                    )
                    links.new(tex_coord.outputs["UV"], mapping.inputs["Vector"])

                    # Position offset for texture nodes
                    x_pos = -400
                    y_pos = 300

                    # Connect different texture maps
                    for map_type, image in downloaded_maps.items():
                        tex_node = nodes.new(type="ShaderNodeTexImage")
                        tex_node.location = (x_pos, y_pos)
                        tex_node.image = image

                        # Set color space based on map type
                        if map_type.lower() in ["color", "diffuse", "albedo"]:
                            try:
                                tex_node.image.colorspace_settings.name = "sRGB"
                            except:
                                pass  # Use default if sRGB not available
                        else:
                            try:
                                tex_node.image.colorspace_settings.name = "Non-Color"
                            except:
                                pass  # Use default if Non-Color not available

                        links.new(mapping.outputs["Vector"], tex_node.inputs["Vector"])

                        # Connect to appropriate input on Principled BSDF
                        if map_type.lower() in ["color", "diffuse", "albedo"]:
                            links.new(
                                tex_node.outputs["Color"],
                                principled.inputs["Base Color"],
                            )
                        elif map_type.lower() in ["roughness", "rough"]:
                            links.new(
                                tex_node.outputs["Color"],
                                principled.inputs["Roughness"],
                            )
                        elif map_type.lower() in ["metallic", "metalness", "metal"]:
                            links.new(
                                tex_node.outputs["Color"], principled.inputs["Metallic"]
                            )
                        elif map_type.lower() in ["normal", "nor"]:
                            # Add normal map node
                            normal_map = nodes.new(type="ShaderNodeNormalMap")
                            normal_map.location = (x_pos + 200, y_pos)
                            links.new(
                                tex_node.outputs["Color"], normal_map.inputs["Color"]
                            )
                            links.new(
                                normal_map.outputs["Normal"],
                                principled.inputs["Normal"],
                            )
                        elif map_type in ["displacement", "disp", "height"]:
                            # Add displacement node
                            disp_node = nodes.new(type="ShaderNodeDisplacement")
                            disp_node.location = (x_pos + 200, y_pos - 200)
                            links.new(
                                tex_node.outputs["Color"], disp_node.inputs["Height"]
                            )
                            links.new(
                                disp_node.outputs["Displacement"],
                                output.inputs["Displacement"],
                            )

                        y_pos -= 250

                    return {
                        "success": True,
                        "message": f"Texture {asset_id} imported as material",
                        "material": mat.name,
                        "maps": list(downloaded_maps.keys()),
                    }

                except Exception as e:
                    return {"error": f"Failed to process textures: {str(e)}"}

            elif asset_type == "models":
                # For models, prefer glTF format if available
                if not file_format:
                    file_format = "gltf"  # Default format for models

                if file_format in files_data and resolution in files_data[file_format]:
                    file_info = files_data[file_format][resolution][file_format]
                    file_url = file_info["url"]

                    # Create a temporary directory to store the model and its dependencies
                    temp_dir = tempfile.mkdtemp()
                    main_file_path = ""

                    try:
                        # Download the main model file
                        main_file_name = file_url.split("/")[-1]
                        main_file_path = os.path.join(temp_dir, main_file_name)

                        response = requests.get(file_url)
                        if response.status_code != 200:
                            return {
                                "error": f"Failed to download model: {response.status_code}"
                            }

                        with open(main_file_path, "wb") as f:
                            f.write(response.content)

                        # Check for included files and download them
                        if "include" in file_info and file_info["include"]:
                            for include_path, include_info in file_info[
                                "include"
                            ].items():
                                # Get the URL for the included file - this is the fix
                                include_url = include_info["url"]

                                # Create the directory structure for the included file
                                include_file_path = os.path.join(temp_dir, include_path)
                                os.makedirs(
                                    os.path.dirname(include_file_path), exist_ok=True
                                )

                                # Download the included file
                                include_response = requests.get(include_url)
                                if include_response.status_code == 200:
                                    with open(include_file_path, "wb") as f:
                                        f.write(include_response.content)
                                else:
                                    print(
                                        f"Failed to download included file: {include_path}"
                                    )

                        # Import the model into Blender
                        if file_format == "gltf" or file_format == "glb":
                            bpy.ops.import_scene.gltf(filepath=main_file_path)
                        elif file_format == "fbx":
                            bpy.ops.import_scene.fbx(filepath=main_file_path)
                        elif file_format == "obj":
                            bpy.ops.import_scene.obj(filepath=main_file_path)
                        elif file_format == "blend":
                            # For blend files, we need to append or link
                            with bpy.data.libraries.load(
                                main_file_path, link=False
                            ) as (data_from, data_to):
                                data_to.objects = data_from.objects

                            # Link the objects to the scene
                            for obj in data_to.objects:
                                if obj is not None:
                                    bpy.context.collection.objects.link(obj)
                        else:
                            return {"error": f"Unsupported model format: {file_format}"}

                        # Get the names of imported objects
                        imported_objects = [
                            obj.name for obj in bpy.context.selected_objects
                        ]

                        return {
                            "success": True,
                            "message": f"Model {asset_id} imported successfully",
                            "imported_objects": imported_objects,
                        }
                    except Exception as e:
                        return {"error": f"Failed to import model: {str(e)}"}
                    finally:
                        # Clean up temporary directory
                        try:
                            shutil.rmtree(temp_dir)
                        except:
                            print(f"Failed to clean up temporary directory: {temp_dir}")
                else:
                    return {
                        "error": f"Requested format or resolution not available for this model"
                    }

            else:
                return {"error": f"Unsupported asset type: {asset_type}"}

        except Exception as e:
            return {"error": f"Failed to download asset: {str(e)}"}

    def set_texture(self, object_name, texture_id):
        """Apply a previously downloaded Polyhaven texture to an object by creating a new material"""
        try:
            # Get the object
            obj = bpy.data.objects.get(object_name)
            if not obj:
                return {"error": f"Object not found: {object_name}"}

            # Make sure object can accept materials
            if not hasattr(obj, "data") or not hasattr(obj.data, "materials"):
                return {"error": f"Object {object_name} cannot accept materials"}

            # Find all images related to this texture and ensure they're properly loaded
            texture_images = {}
            for img in bpy.data.images:
                if img.name.startswith(texture_id + "_"):
                    # Extract the map type from the image name
                    map_type = img.name.split("_")[-1].split(".")[0]

                    # Force a reload of the image
                    img.reload()

                    # Ensure proper color space
                    if map_type.lower() in ["color", "diffuse", "albedo"]:
                        try:
                            img.colorspace_settings.name = "sRGB"
                        except:
                            pass
                    else:
                        try:
                            img.colorspace_settings.name = "Non-Color"
                        except:
                            pass

                    # Ensure the image is packed
                    if not img.packed_file:
                        img.pack()

                    texture_images[map_type] = img
                    print(f"Loaded texture map: {map_type} - {img.name}")

                    # Debug info
                    print(f"Image size: {img.size[0]}x{img.size[1]}")
                    print(f"Color space: {img.colorspace_settings.name}")
                    print(f"File format: {img.file_format}")
                    print(f"Is packed: {bool(img.packed_file)}")

            if not texture_images:
                return {
                    "error": f"No texture images found for: {texture_id}. Please download the texture first."
                }

            # Create a new material
            new_mat_name = f"{texture_id}_material_{object_name}"

            # Remove any existing material with this name to avoid conflicts
            existing_mat = bpy.data.materials.get(new_mat_name)
            if existing_mat:
                bpy.data.materials.remove(existing_mat)

            new_mat = bpy.data.materials.new(name=new_mat_name)
            new_mat.use_nodes = True

            # Set up the material nodes
            nodes = new_mat.node_tree.nodes
            links = new_mat.node_tree.links

            # Clear default nodes
            nodes.clear()

            # Create output node
            output = nodes.new(type="ShaderNodeOutputMaterial")
            output.location = (600, 0)

            # Create principled BSDF node
            principled = nodes.new(type="ShaderNodeBsdfPrincipled")
            principled.location = (300, 0)
            links.new(principled.outputs[0], output.inputs[0])

            # Add texture nodes based on available maps
            tex_coord = nodes.new(type="ShaderNodeTexCoord")
            tex_coord.location = (-800, 0)

            mapping = nodes.new(type="ShaderNodeMapping")
            mapping.location = (-600, 0)
            mapping.vector_type = "TEXTURE"  # Changed from default 'POINT' to 'TEXTURE'
            links.new(tex_coord.outputs["UV"], mapping.inputs["Vector"])

            # Position offset for texture nodes
            x_pos = -400
            y_pos = 300

            # Connect different texture maps
            for map_type, image in texture_images.items():
                tex_node = nodes.new(type="ShaderNodeTexImage")
                tex_node.location = (x_pos, y_pos)
                tex_node.image = image

                # Set color space based on map type
                if map_type.lower() in ["color", "diffuse", "albedo"]:
                    try:
                        tex_node.image.colorspace_settings.name = "sRGB"
                    except:
                        pass  # Use default if sRGB not available
                else:
                    try:
                        tex_node.image.colorspace_settings.name = "Non-Color"
                    except:
                        pass  # Use default if Non-Color not available

                links.new(mapping.outputs["Vector"], tex_node.inputs["Vector"])

                # Connect to appropriate input on Principled BSDF
                if map_type.lower() in ["color", "diffuse", "albedo"]:
                    links.new(
                        tex_node.outputs["Color"], principled.inputs["Base Color"]
                    )
                elif map_type.lower() in ["roughness", "rough"]:
                    links.new(tex_node.outputs["Color"], principled.inputs["Roughness"])
                elif map_type.lower() in ["metallic", "metalness", "metal"]:
                    links.new(tex_node.outputs["Color"], principled.inputs["Metallic"])
                elif map_type.lower() in ["normal", "nor", "dx", "gl"]:
                    # Add normal map node
                    normal_map = nodes.new(type="ShaderNodeNormalMap")
                    normal_map.location = (x_pos + 200, y_pos)
                    links.new(tex_node.outputs["Color"], normal_map.inputs["Color"])
                    links.new(normal_map.outputs["Normal"], principled.inputs["Normal"])
                elif map_type.lower() in ["displacement", "disp", "height"]:
                    # Add displacement node
                    disp_node = nodes.new(type="ShaderNodeDisplacement")
                    disp_node.location = (x_pos + 200, y_pos - 200)
                    disp_node.inputs["Scale"].default_value = (
                        0.1  # Reduce displacement strength
                    )
                    links.new(tex_node.outputs["Color"], disp_node.inputs["Height"])
                    links.new(
                        disp_node.outputs["Displacement"], output.inputs["Displacement"]
                    )

                y_pos -= 250

            # Second pass: Connect nodes with proper handling for special cases
            texture_nodes = {}

            # First find all texture nodes and store them by map type
            for node in nodes:
                if node.type == "TEX_IMAGE" and node.image:
                    for map_type, image in texture_images.items():
                        if node.image == image:
                            texture_nodes[map_type] = node
                            break

            # Now connect everything using the nodes instead of images
            # Handle base color (diffuse)
            for map_name in ["color", "diffuse", "albedo"]:
                if map_name in texture_nodes:
                    links.new(
                        texture_nodes[map_name].outputs["Color"],
                        principled.inputs["Base Color"],
                    )
                    print(f"Connected {map_name} to Base Color")
                    break

            # Handle roughness
            for map_name in ["roughness", "rough"]:
                if map_name in texture_nodes:
                    links.new(
                        texture_nodes[map_name].outputs["Color"],
                        principled.inputs["Roughness"],
                    )
                    print(f"Connected {map_name} to Roughness")
                    break

            # Handle metallic
            for map_name in ["metallic", "metalness", "metal"]:
                if map_name in texture_nodes:
                    links.new(
                        texture_nodes[map_name].outputs["Color"],
                        principled.inputs["Metallic"],
                    )
                    print(f"Connected {map_name} to Metallic")
                    break

            # Handle normal maps
            for map_name in ["gl", "dx", "nor"]:
                if map_name in texture_nodes:
                    normal_map_node = nodes.new(type="ShaderNodeNormalMap")
                    normal_map_node.location = (100, 100)
                    links.new(
                        texture_nodes[map_name].outputs["Color"],
                        normal_map_node.inputs["Color"],
                    )
                    links.new(
                        normal_map_node.outputs["Normal"], principled.inputs["Normal"]
                    )
                    print(f"Connected {map_name} to Normal")
                    break

            # Handle displacement
            for map_name in ["displacement", "disp", "height"]:
                if map_name in texture_nodes:
                    disp_node = nodes.new(type="ShaderNodeDisplacement")
                    disp_node.location = (300, -200)
                    disp_node.inputs["Scale"].default_value = (
                        0.1  # Reduce displacement strength
                    )
                    links.new(
                        texture_nodes[map_name].outputs["Color"],
                        disp_node.inputs["Height"],
                    )
                    links.new(
                        disp_node.outputs["Displacement"], output.inputs["Displacement"]
                    )
                    print(f"Connected {map_name} to Displacement")
                    break

            # Handle ARM texture (Ambient Occlusion, Roughness, Metallic)
            if "arm" in texture_nodes:
                separate_rgb = nodes.new(type="ShaderNodeSeparateRGB")
                separate_rgb.location = (-200, -100)
                links.new(
                    texture_nodes["arm"].outputs["Color"], separate_rgb.inputs["Image"]
                )

                # Connect Roughness (G) if no dedicated roughness map
                if not any(
                    map_name in texture_nodes for map_name in ["roughness", "rough"]
                ):
                    links.new(separate_rgb.outputs["G"], principled.inputs["Roughness"])
                    print("Connected ARM.G to Roughness")

                # Connect Metallic (B) if no dedicated metallic map
                if not any(
                    map_name in texture_nodes
                    for map_name in ["metallic", "metalness", "metal"]
                ):
                    links.new(separate_rgb.outputs["B"], principled.inputs["Metallic"])
                    print("Connected ARM.B to Metallic")

                # For AO (R channel), multiply with base color if we have one
                base_color_node = None
                for map_name in ["color", "diffuse", "albedo"]:
                    if map_name in texture_nodes:
                        base_color_node = texture_nodes[map_name]
                        break

                if base_color_node:
                    mix_node = nodes.new(type="ShaderNodeMixRGB")
                    mix_node.location = (100, 200)
                    mix_node.blend_type = "MULTIPLY"
                    mix_node.inputs["Fac"].default_value = 0.8  # 80% influence

                    # Disconnect direct connection to base color
                    for link in base_color_node.outputs["Color"].links:
                        if link.to_socket == principled.inputs["Base Color"]:
                            links.remove(link)

                    # Connect through the mix node
                    links.new(base_color_node.outputs["Color"], mix_node.inputs[1])
                    links.new(separate_rgb.outputs["R"], mix_node.inputs[2])
                    links.new(
                        mix_node.outputs["Color"], principled.inputs["Base Color"]
                    )
                    print("Connected ARM.R to AO mix with Base Color")

            # Handle AO (Ambient Occlusion) if separate
            if "ao" in texture_nodes:
                base_color_node = None
                for map_name in ["color", "diffuse", "albedo"]:
                    if map_name in texture_nodes:
                        base_color_node = texture_nodes[map_name]
                        break

                if base_color_node:
                    mix_node = nodes.new(type="ShaderNodeMixRGB")
                    mix_node.location = (100, 200)
                    mix_node.blend_type = "MULTIPLY"
                    mix_node.inputs["Fac"].default_value = 0.8  # 80% influence

                    # Disconnect direct connection to base color
                    for link in base_color_node.outputs["Color"].links:
                        if link.to_socket == principled.inputs["Base Color"]:
                            links.remove(link)

                    # Connect through the mix node
                    links.new(base_color_node.outputs["Color"], mix_node.inputs[1])
                    links.new(texture_nodes["ao"].outputs["Color"], mix_node.inputs[2])
                    links.new(
                        mix_node.outputs["Color"], principled.inputs["Base Color"]
                    )
                    print("Connected AO to mix with Base Color")

            # CRITICAL: Make sure to clear all existing materials from the object
            while len(obj.data.materials) > 0:
                obj.data.materials.pop(index=0)

            # Assign the new material to the object
            obj.data.materials.append(new_mat)

            # CRITICAL: Make the object active and select it
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)

            # CRITICAL: Force Blender to update the material
            bpy.context.view_layer.update()

            # Get the list of texture maps
            texture_maps = list(texture_images.keys())

            # Get info about texture nodes for debugging
            material_info = {
                "name": new_mat.name,
                "has_nodes": new_mat.use_nodes,
                "node_count": len(new_mat.node_tree.nodes),
                "texture_nodes": [],
            }

            for node in new_mat.node_tree.nodes:
                if node.type == "TEX_IMAGE" and node.image:
                    connections = []
                    for output in node.outputs:
                        for link in output.links:
                            connections.append(
                                f"{output.name} → {link.to_node.name}.{link.to_socket.name}"
                            )

                    material_info["texture_nodes"].append(
                        {
                            "name": node.name,
                            "image": node.image.name,
                            "colorspace": node.image.colorspace_settings.name,
                            "connections": connections,
                        }
                    )

            return {
                "success": True,
                "message": f"Created new material and applied texture {texture_id} to {object_name}",
                "material": new_mat.name,
                "maps": texture_maps,
                "material_info": material_info,
            }

        except Exception as e:
            print(f"Error in set_texture: {str(e)}")
            traceback.print_exc()
            return {"error": f"Failed to apply texture: {str(e)}"}

    def get_polyhaven_status(self):
        """Get the current status of PolyHaven integration"""
        enabled = bpy.context.scene.blendermcp_use_polyhaven
        if enabled:
            return {
                "enabled": True,
                "message": "PolyHaven integration is enabled and ready to use.",
            }
        else:
            return {
                "enabled": False,
                "message": """PolyHaven integration is currently disabled. To enable it:
                            1. In the 3D Viewport, find the BlenderMCP panel in the sidebar (press N if hidden)
                            2. Check the 'Use assets from Poly Haven' checkbox
                            3. Restart the connection to Claude""",
            }

    # region Hyper3D
    def get_hyper3d_status(self):
        """Get the current status of Hyper3D Rodin integration"""
        enabled = bpy.context.scene.blendermcp_use_hyper3d
        if enabled:
            if not bpy.context.scene.blendermcp_hyper3d_api_key:
                return {
                    "enabled": False,
                    "message": """Hyper3D Rodin integration is currently enabled, but API key is not given. To enable it:
                                1. In the 3D Viewport, find the BlenderMCP panel in the sidebar (press N if hidden)
                                2. Keep the 'Use Hyper3D Rodin 3D model generation' checkbox checked
                                3. Choose the right plaform and fill in the API Key
                                4. Restart the connection to Claude""",
                }
            mode = bpy.context.scene.blendermcp_hyper3d_mode
            message = (
                f"Hyper3D Rodin integration is enabled and ready to use. Mode: {mode}. "
                + f"Key type: {'private' if bpy.context.scene.blendermcp_hyper3d_api_key != RODIN_FREE_TRIAL_KEY else 'free_trial'}"
            )
            return {"enabled": True, "message": message}
        else:
            return {
                "enabled": False,
                "message": """Hyper3D Rodin integration is currently disabled. To enable it:
                            1. In the 3D Viewport, find the BlenderMCP panel in the sidebar (press N if hidden)
                            2. Check the 'Use Hyper3D Rodin 3D model generation' checkbox
                            3. Restart the connection to Claude""",
            }

    def create_rodin_job(self, tier: str = None, mesh_mode: str = None, *args, **kwargs):
        # Note: *args is kept for backward compatibility if direct calls were made with positional args before text_prompt.
        # However, new params like text_prompt, images, bbox_condition should be passed as kwargs.
        # tier and mesh_mode are new optional params.

        # Prepare a dictionary of parameters to pass, excluding None values for tier/mesh_mode if not provided
        # This ensures that if they are None, they are not explicitly passed, allowing underlying functions
        # to use their default Scene property fallbacks.
        params_to_pass = kwargs.copy()
        if tier is not None:
            params_to_pass['tier'] = tier
        if mesh_mode is not None:
            params_to_pass['mesh_mode'] = mesh_mode

        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.create_rodin_job_main_site(*args, **params_to_pass)
            case "FAL_AI":
                # fal_ai create_rodin_job_fal_ai doesn't use mesh_mode in its signature,
                # but it's fine to pass it here; it will be ignored if not in **kwargs of the target.
                return self.create_rodin_job_fal_ai(*args, **params_to_pass)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def create_rodin_job_main_site(
        self,
        text_prompt: str = None,
        images: list[tuple[str, str]] = None,
        bbox_condition=None,
        tier: str = None,
        mesh_mode: str = None,
    ):
        try:
            if images is None:
                images = []
            """
            Call Rodin API (Main Site) to create a generation job.
            The 'tier' and 'mesh_mode' can be overridden by direct parameters from an MCP tool call,
            otherwise they default to the values set in Blender's scene properties.
            Valid values for tier/mesh_mode are API-specific and may require user experimentation
            (e.g., tier: "Sketch", "Detailed"; mesh_mode: "Raw", "HighPoly").
            """

            # Resolve tier and mesh_mode: use parameters if provided, else fallback to scene properties
            resolved_tier = tier if tier is not None else bpy.context.scene.mcp_hyper3d_tier
            resolved_mesh_mode = mesh_mode if mesh_mode is not None else bpy.context.scene.mcp_hyper3d_mesh_mode

            files = [
                *[
                    ("images", (f"{i:04d}{img_suffix}", img))
                    for i, (img_suffix, img) in enumerate(images)
                ],
                ("tier", (None, resolved_tier)),
                ("mesh_mode", (None, resolved_mesh_mode)),
            ]
            if text_prompt:
                files.append(("prompt", (None, text_prompt)))
            if bbox_condition:
                files.append(("bbox_condition", (None, json.dumps(bbox_condition))))
            response = requests.post(
                "https://hyperhuman.deemos.com/api/v2/rodin",
                headers={
                    "Authorization": f"Bearer {bpy.context.scene.blendermcp_hyper3d_api_key}",
                },
                files=files,
            )
            data = response.json()
            return data
        except Exception as e:
            return {"error": str(e)}

    def create_rodin_job_fal_ai(
        self,
        text_prompt: str = None,
        images: list[tuple[str, str]] = None,
        bbox_condition=None,
        tier: str = None,
        # mesh_mode is not used by fal_ai variant currently
    ):
        try:
            # Resolve tier: use parameter if provided, else fallback to scene property
            # The 'tier' can be overridden by a direct parameter from an MCP tool call.
            # Valid values are API-specific (e.g., "Sketch", "Detailed").
            resolved_tier = tier if tier is not None else bpy.context.scene.mcp_hyper3d_tier
            req_data = {
                "tier": resolved_tier,
            }
            if images:
                req_data["input_image_urls"] = images
            if text_prompt:
                req_data["prompt"] = text_prompt
            if bbox_condition:
                req_data["bbox_condition"] = bbox_condition
            response = requests.post(
                "https://queue.fal.run/fal-ai/hyper3d/rodin",
                headers={
                    "Authorization": f"Key {bpy.context.scene.blendermcp_hyper3d_api_key}",
                    "Content-Type": "application/json",
                },
                json=req_data,
            )
            data = response.json()
            return data
        except Exception as e:
            return {"error": str(e)}

    def poll_rodin_job_status(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.poll_rodin_job_status_main_site(*args, **kwargs)
            case "FAL_AI":
                return self.poll_rodin_job_status_fal_ai(*args, **kwargs)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def poll_rodin_job_status_main_site(self, subscription_key: str):
        """Call the job status API to get the job status"""
        response = requests.post(
            "https://hyperhuman.deemos.com/api/v2/status",
            headers={
                "Authorization": f"Bearer {bpy.context.scene.blendermcp_hyper3d_api_key}",
            },
            json={
                "subscription_key": subscription_key,
            },
        )
        data = response.json()
        return {"status_list": [i["status"] for i in data["jobs"]]}

    def poll_rodin_job_status_fal_ai(self, request_id: str):
        """Call the job status API to get the job status"""
        response = requests.get(
            f"https://queue.fal.run/fal-ai/hyper3d/requests/{request_id}/status",
            headers={
                "Authorization": f"KEY {bpy.context.scene.blendermcp_hyper3d_api_key}",
            },
        )
        data = response.json()
        return data

    @staticmethod
    def _clean_imported_glb(filepath, mesh_name=None):
        # Get the set of existing objects before import
        existing_objects = set(bpy.data.objects)

        # Import the GLB file
        bpy.ops.import_scene.gltf(filepath=filepath)

        # Ensure the context is updated
        bpy.context.view_layer.update()

        # Get all imported objects
        imported_objects = list(set(bpy.data.objects) - existing_objects)
        # imported_objects = [obj for obj in bpy.context.view_layer.objects if obj.select_get()]

        if not imported_objects:
            print("Error: No objects were imported.")
            return

        # Identify the mesh object
        mesh_obj = None

        if len(imported_objects) == 1 and imported_objects[0].type == "MESH":
            mesh_obj = imported_objects[0]
            print("Single mesh imported, no cleanup needed.")
        else:
            if len(imported_objects) == 2:
                empty_objs = [i for i in imported_objects if i.type == "EMPTY"]
                if len(empty_objs) != 1:
                    print(
                        "Error: Expected an empty node with one mesh child or a single mesh object."
                    )
                    return
                parent_obj = empty_objs.pop()
                if len(parent_obj.children) == 1:
                    potential_mesh = parent_obj.children[0]
                    if potential_mesh.type == "MESH":
                        print(
                            "GLB structure confirmed: Empty node with one mesh child."
                        )

                        # Unparent the mesh from the empty node
                        potential_mesh.parent = None

                        # Remove the empty node
                        bpy.data.objects.remove(parent_obj)
                        print("Removed empty node, keeping only the mesh.")

                        mesh_obj = potential_mesh
                    else:
                        print("Error: Child is not a mesh object.")
                        return
                else:
                    print(
                        "Error: Expected an empty node with one mesh child or a single mesh object."
                    )
                    return
            else:
                print(
                    "Error: Expected an empty node with one mesh child or a single mesh object."
                )
                return

        # Rename the mesh if needed
        try:
            if mesh_obj and mesh_obj.name is not None and mesh_name:
                mesh_obj.name = mesh_name
                if mesh_obj.data.name is not None:
                    mesh_obj.data.name = mesh_name
                print(f"Mesh renamed to: {mesh_name}")
        except Exception as e:
            print("Having issue with renaming, give up renaming.")

        return mesh_obj

    def import_generated_asset(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.import_generated_asset_main_site(*args, **kwargs)
            case "FAL_AI":
                return self.import_generated_asset_fal_ai(*args, **kwargs)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def import_generated_asset_main_site(self, task_uuid: str, name: str):
        """Fetch the generated asset, import into blender"""
        response = requests.post(
            "https://hyperhuman.deemos.com/api/v2/download",
            headers={
                "Authorization": f"Bearer {bpy.context.scene.blendermcp_hyper3d_api_key}",
            },
            json={"task_uuid": task_uuid},
        )
        data_ = response.json()
        temp_file = None
        for i in data_["list"]:
            if i["name"].endswith(".glb"):
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    prefix=task_uuid,
                    suffix=".glb",
                )

                try:
                    # Download the content
                    response = requests.get(i["url"], stream=True)
                    response.raise_for_status()  # Raise an exception for HTTP errors

                    # Write the content to the temporary file
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)

                    # Close the file
                    temp_file.close()

                except Exception as e:
                    # Clean up the file if there's an error
                    temp_file.close()
                    os.unlink(temp_file.name)
                    return {"succeed": False, "error": str(e)}

                break
        else:
            return {
                "succeed": False,
                "error": "Generation failed. Please first make sure that all jobs of the task are done and then try again later.",
            }

        try:
            obj = self._clean_imported_glb(filepath=temp_file.name, mesh_name=name)
            result = {
                "name": obj.name,
                "type": obj.type,
                "location": [obj.location.x, obj.location.y, obj.location.z],
                "rotation": [
                    obj.rotation_euler.x,
                    obj.rotation_euler.y,
                    obj.rotation_euler.z,
                ],
                "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            }

            if obj.type == "MESH":
                bounding_box = self._get_aabb(obj)
                result["world_bounding_box"] = bounding_box

            return {"succeed": True, **result}
        except Exception as e:
            return {"succeed": False, "error": str(e)}

    def import_generated_asset_fal_ai(self, request_id: str, name: str):
        """Fetch the generated asset, import into blender"""
        response = requests.get(
            f"https://queue.fal.run/fal-ai/hyper3d/requests/{request_id}",
            headers={
                "Authorization": f"Key {bpy.context.scene.blendermcp_hyper3d_api_key}",
            },
        )
        data_ = response.json()
        temp_file = None

        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            prefix=request_id,
            suffix=".glb",
        )

        try:
            # Download the content
            response = requests.get(data_["model_mesh"]["url"], stream=True)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Write the content to the temporary file
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)

            # Close the file
            temp_file.close()

        except Exception as e:
            # Clean up the file if there's an error
            temp_file.close()
            os.unlink(temp_file.name)
            return {"succeed": False, "error": str(e)}

        try:
            obj = self._clean_imported_glb(filepath=temp_file.name, mesh_name=name)
            result = {
                "name": obj.name,
                "type": obj.type,
                "location": [obj.location.x, obj.location.y, obj.location.z],
                "rotation": [
                    obj.rotation_euler.x,
                    obj.rotation_euler.y,
                    obj.rotation_euler.z,
                ],
                "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            }

            if obj.type == "MESH":
                bounding_box = self._get_aabb(obj)
                result["world_bounding_box"] = bounding_box

            return {"succeed": True, **result}
        except Exception as e:
            return {"succeed": False, "error": str(e)}

    def import_model_from_path(self, path: str):

        if not os.path.exists(path):
            raise FileNotFoundError(f"File does not exist: {path}")

        ext = os.path.splitext(path)[1].lower()
        supported = [".obj", ".fbx", ".glb", ".gltf", ".blend"]
        if ext not in supported:
            raise ValueError(f"Unsupported file extension: {ext}")

        # Import based on file type
        if ext == ".obj":
            bpy.ops.import_scene.obj(filepath=path)
        elif ext == ".fbx":
            bpy.ops.import_scene.fbx(filepath=path)
        elif ext in [".glb", ".gltf"]:
            bpy.ops.import_scene.gltf(filepath=path)
        elif ext == ".blend":
            with bpy.data.libraries.load(path, link=False) as (data_from, data_to):
                data_to.objects = data_from.objects

            for obj in data_to.objects:
                if obj is not None:
                    bpy.context.collection.objects.link(obj)

        return {"imported_file": path, "type": ext}

    def get_mesh_details(self, name: str):
        """
        Retrieves details for a specified mesh object.

        Args:
            name (str): The name of the mesh object to inspect.

        Returns:
            dict: A dictionary containing the mesh's name, vertex count,
                  face count, and a list of modifier names.
                  Returns an error dictionary if the object is not found or not a mesh.
        """
        obj = bpy.data.objects.get(name)
        if not obj:
            return {"error": f"Object not found: {name}"}

        if obj.type != 'MESH':
            return {"error": f"Object '{name}' is not a mesh (type: {obj.type})"}

        mesh = obj.data
        num_vertices = len(mesh.vertices)
        num_faces = len(mesh.polygons)
        modifiers_list = [mod.name for mod in obj.modifiers]

        return {
            "name": obj.name,
            "vertices": num_vertices,
            "faces": num_faces,
            "modifiers": modifiers_list
        }

    # endregion


# Blender UI Panel
class BLENDERMCP_PT_Panel(bpy.types.Panel):
    bl_label = "Blender MCP"
    bl_idname = "BLENDERMCP_PT_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderMCP"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "blendermcp_port")
        layout.prop(
            scene, "blendermcp_use_polyhaven", text="Use assets from Poly Haven"
        )

        layout.prop(
            scene,
            "blendermcp_use_hyper3d",
            text="Use Hyper3D Rodin 3D model generation",
        )
        if scene.blendermcp_use_hyper3d:
            layout.prop(scene, "blendermcp_hyper3d_mode", text="Rodin Mode")
            layout.prop(scene, "blendermcp_hyper3d_api_key", text="API Key")
            layout.prop(scene, "mcp_hyper3d_tier")
            layout.prop(scene, "mcp_hyper3d_mesh_mode")
            layout.operator(
                "blendermcp.set_hyper3d_free_trial_api_key",
                text="Set Free Trial API Key",
            )

        layout.prop(context.scene, "mcp_llm_backend", text="LLM Backend")

        if scene.mcp_llm_backend == "claude":
            layout.prop(scene, "mcp_claude_model_name", text="Claude Model")
        elif scene.mcp_llm_backend == "ollama":
            layout.prop(scene, "mcp_ollama_model_name", text="Ollama Model")

        layout.prop(scene, "mcp_screenshot_history_limit")

        if not scene.blendermcp_server_running:
            layout.operator("blendermcp.start_server", text="Connect to MCP server")
        else:
            layout.operator("blendermcp.stop_server", text="Disconnect from MCP server")
            layout.label(text=f"Running on port {scene.blendermcp_port}")


def render_and_save_image():
    """
    Renders the current 3D viewport view and saves it as a PNG image.

    This function handles:
    - Generating a unique, timestamped filename for the screenshot.
    - Saving the screenshot to the directory specified by SCREENSHOT_DIR_PATH.
    - Managing a history of screenshots: older screenshots are deleted if the
      total number exceeds the limit defined by the 'Screenshot History Limit'
      setting in the BlenderMCP addon panel.
    - Returns the full string path to the newly saved screenshot, which is then
      typically sent to the LLM for analysis.
    """

    # Get history limit from scene properties
    history_limit = bpy.context.scene.mcp_screenshot_history_limit
    # If limit is 0 or less, default to keeping at least 1 screenshot
    if history_limit < 1:
        history_limit = 1

    new_image_path_obj = get_screenshot_filepath()
    new_image_path_str = str(new_image_path_obj)

    bpy.context.scene.render.filepath = new_image_path_str
    bpy.ops.render.opengl(write_still=True)

    # Manage history
    try:
        # Ensure the directory exists before listing
        _ensure_screenshot_dir_exists()

        # Get all .png files in the directory
        screenshots = list(SCREENSHOT_DIR_PATH.glob("*.png"))

        # Sort by name (which corresponds to timestamp)
        screenshots.sort(key=lambda p: p.name)

        # If history limit exceeded, remove oldest ones
        if len(screenshots) > history_limit:
            num_to_delete = len(screenshots) - history_limit
            for i in range(num_to_delete):
                try:
                    os.remove(screenshots[i])
                    print(f"Removed old screenshot: {screenshots[i]}")
                except OSError as e:
                    print(f"Error removing screenshot {screenshots[i]}: {e}")

    except Exception as e:
        print(f"Error managing screenshot history: {e}")

    return new_image_path_str


def extract_scene_summary():
    summary = []
    for obj in bpy.data.objects:
        summary.append(
            f"{obj.name}: {obj.type}, Location: {obj.location}, Visible: {obj.visible_get()}"
        )
    return "\n".join(summary)


class MCP_OT_AskLLMAboutScene(bpy.types.Operator):
    bl_idname = "mcp.ask_llm_about_scene"
    bl_label = "Ask LLM About Scene"

    def execute(self, context):
        from .llm_handler import query_llm

        image_path = render_and_save_image()
        metadata = extract_scene_summary()
        backend = context.scene.mcp_llm_backend

        if backend == "ollama":
            ollama_model_name = context.scene.mcp_ollama_model_name
            response = query_llm(backend=backend, image_path=image_path, metadata=metadata, ollama_model_name=ollama_model_name)
        else:
            response = query_llm(backend=backend, image_path=image_path, metadata=metadata)

        self.report({"INFO"}, response[:400])
        print("LLM Response:", response)
        return {"FINISHED"}


# Operator to set Hyper3D API Key
class BLENDERMCP_OT_SetFreeTrialHyper3DAPIKey(bpy.types.Operator):
    bl_idname = "blendermcp.set_hyper3d_free_trial_api_key"
    bl_label = "Set Free Trial API Key"

    def execute(self, context):
        context.scene.blendermcp_hyper3d_api_key = RODIN_FREE_TRIAL_KEY
        context.scene.blendermcp_hyper3d_mode = "MAIN_SITE"
        self.report({"INFO"}, "API Key set successfully!")
        return {"FINISHED"}


# Operator to start the server
class BLENDERMCP_OT_StartServer(bpy.types.Operator):
    bl_idname = "blendermcp.start_server"
    bl_label = "Connect to Claude"
    bl_description = "Start the BlenderMCP server to connect with Claude"

    def execute(self, context):
        scene = context.scene

        # Create a new server instance
        if (
            not hasattr(bpy.types, "blendermcp_server")
            or not bpy.types.blendermcp_server
        ):
            bpy.types.blendermcp_server = BlenderMCPServer(port=scene.blendermcp_port)

        # Start the server
        bpy.types.blendermcp_server.start()
        scene.blendermcp_server_running = True

        return {"FINISHED"}


# Operator to stop the server
class BLENDERMCP_OT_StopServer(bpy.types.Operator):
    bl_idname = "blendermcp.stop_server"
    bl_label = "Stop the connection to Claude"
    bl_description = "Stop the connection to Claude"

    def execute(self, context):
        scene = context.scene

        # Stop the server if it exists
        if hasattr(bpy.types, "blendermcp_server") and bpy.types.blendermcp_server:
            bpy.types.blendermcp_server.stop()
            del bpy.types.blendermcp_server

        scene.blendermcp_server_running = False

        return {"FINISHED"}


def unregister_backend_setting():
    del bpy.types.Scene.mcp_llm_backend


# Registration functions
def register():
    bpy.types.Scene.blendermcp_port = IntProperty(
        name="Port",
        description="Port for the BlenderMCP server",
        default=9876,
        min=1024,
        max=65535,
    )

    bpy.types.Scene.mcp_llm_backend = EnumProperty(
        name="LLM Backend",
        description="Choose LLM backend",
        items=[
            ("claude", "Claude", "Use Claude API"),
            ("ollama", "Ollama", "Use Ollama locally"),
        ],
        default="ollama",
    )

    bpy.types.Scene.mcp_claude_model_name = bpy.props.StringProperty(
        name="Claude Model",
        description="Name of Claude model to use (e.g., claude-3-opus-20240229)",
        default="claude-3-opus-20240229",
    )

    bpy.types.Scene.mcp_ollama_model_name = bpy.props.StringProperty(
        name="Ollama Model",
        description="Name of Ollama model to use (e.g., llama3, stablelm-zephyr)",
        default="gemma3:4b",
    )

    bpy.types.Scene.mcp_screenshot_history_limit = bpy.props.IntProperty(
        name="Screenshot History Limit",
        description="Maximum number of screenshots to keep. Set to 0 to keep only 1.",
        default=10,
        min=0
    )

    bpy.types.Scene.blendermcp_server_running = bpy.props.BoolProperty(
        name="Server Running", default=False
    )

    bpy.types.Scene.blendermcp_use_polyhaven = bpy.props.BoolProperty(
        name="Use Poly Haven",
        description="Enable Poly Haven asset integration",
        default=False,
    )

    bpy.types.Scene.blendermcp_use_hyper3d = bpy.props.BoolProperty(
        name="Use Hyper3D Rodin",
        description="Enable Hyper3D Rodin generatino integration",
        default=False,
    )

    bpy.types.Scene.blendermcp_hyper3d_mode = bpy.props.EnumProperty(
        name="Rodin Mode",
        description="Choose the platform used to call Rodin APIs",
        items=[
            ("MAIN_SITE", "hyper3d.ai", "hyper3d.ai"),
            ("FAL_AI", "fal.ai", "fal.ai"),
        ],
        default="MAIN_SITE",
    )

    bpy.types.Scene.blendermcp_hyper3d_api_key = bpy.props.StringProperty(
        name="Hyper3D API Key",
        subtype="PASSWORD",
        description="API Key provided by Hyper3D",
        default="",
    )

    bpy.types.Scene.mcp_hyper3d_tier = bpy.props.StringProperty(
        name="Hyper3D Tier",
        description="Generation tier for Hyper3D (e.g., Sketch, Detailed). API specific.",
        default="Sketch"
    )
    bpy.types.Scene.mcp_hyper3d_mesh_mode = bpy.props.StringProperty(
        name="Hyper3D Mesh Mode",
        description="Mesh mode for Hyper3D (e.g., Raw, HighPoly). API specific.",
        default="Raw"
    )

    bpy.utils.register_class(BLENDERMCP_PT_Panel)
    bpy.utils.register_class(BLENDERMCP_OT_SetFreeTrialHyper3DAPIKey)
    bpy.utils.register_class(BLENDERMCP_OT_StartServer)
    bpy.utils.register_class(BLENDERMCP_OT_StopServer)

    print("BlenderMCP addon registered")


def unregister():
    # Stop the server if it's running
    if hasattr(bpy.types, "blendermcp_server") and bpy.types.blendermcp_server:
        bpy.types.blendermcp_server.stop()
        del bpy.types.blendermcp_server

    bpy.utils.unregister_class(BLENDERMCP_PT_Panel)
    bpy.utils.unregister_class(BLENDERMCP_OT_SetFreeTrialHyper3DAPIKey)
    bpy.utils.unregister_class(BLENDERMCP_OT_StartServer)
    bpy.utils.unregister_class(BLENDERMCP_OT_StopServer)

    del bpy.types.Scene.blendermcp_port
    del bpy.types.Scene.blendermcp_server_running
    del bpy.types.Scene.blendermcp_use_polyhaven
    del bpy.types.Scene.blendermcp_use_hyper3d
    del bpy.types.Scene.blendermcp_hyper3d_mode
    del bpy.types.Scene.blendermcp_hyper3d_api_key
    del bpy.types.Scene.mcp_hyper3d_tier
    del bpy.types.Scene.mcp_hyper3d_mesh_mode

    del bpy.types.Scene.mcp_llm_backend
    del bpy.types.Scene.mcp_claude_model_name
    del bpy.types.Scene.mcp_ollama_model_name
    del bpy.types.Scene.mcp_screenshot_history_limit

    print("BlenderMCP addon unregistered")


if __name__ == "__main__":
    register()
