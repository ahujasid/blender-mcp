import bpy

def clear_scene():
    """Clears all objects from the current scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Also remove any orphaned data blocks
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.armatures:
        if block.users == 0:
            bpy.data.armatures.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)
    for block in bpy.data.textures:
        if block.users == 0:
            bpy.data.textures.remove(block)
    for block in bpy.data.images:
        if block.users == 0:
            bpy.data.images.remove(block)
    for block in bpy.data.lights:
        if block.users == 0:
            bpy.data.lights.remove(block)
    for block in bpy.data.cameras:
        if block.users == 0:
            bpy.data.cameras.remove(block)

def create_cylinder():
    """Creates a cylinder mesh."""
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32,
        radius=0.5,
        depth=3,
        location=(0, 0, 1.5) # Centered at Z=1.5 so base is at Z=0
    )
    return bpy.context.object

def create_armature():
    """Creates a simple three-bone armature."""
    bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
    armature_obj = bpy.context.object
    armature = armature_obj.data

    # Ensure unique bone names by removing any existing bones with the same names
    # (though clear_scene should prevent this)
    bone_names = ["Bone.001", "Bone.002", "Bone.003"]
    for name in bone_names:
        if name in armature.edit_bones:
            armature.edit_bones.remove(armature.edit_bones[name])

    # Bone 1
    bone1 = armature.edit_bones.new("Bone.001")
    bone1.head = (0, 0, 0.5)
    bone1.tail = (0, 0, 1.5)

    # Bone 2 (Connected to Bone 1)
    bone2 = armature.edit_bones.new("Bone.002")
    bone2.head = (0, 0, 1.5)
    bone2.tail = (0, 0, 2.5)
    bone2.parent = bone1 # Connect to Bone1

    # Bone 3 (Connected to Bone 2)
    bone3 = armature.edit_bones.new("Bone.003")
    bone3.head = (0, 0, 2.5)
    bone3.tail = (0, 0, 3.5)
    bone3.parent = bone2 # Connect to Bone2

    bpy.ops.object.mode_set(mode='OBJECT')
    return armature_obj

def main():
    """Main function to execute the script."""
    # 1. Clear the scene
    clear_scene()

    # 2. Create the cylinder
    cylinder_obj = create_cylinder()

    # 3. Create the armature
    armature_obj = create_armature()

    # 4. Parent the cylinder to the armature with automatic weights
    # Ensure cylinder is active and armature is selected
    bpy.ops.object.select_all(action='DESELECT')
    cylinder_obj.select_set(True)
    armature_obj.select_set(True)
    bpy.context.view_layer.objects.active = armature_obj # Armature should be the active object for parenting

    bpy.ops.object.parent_set(type='ARMATURE_AUTO')

    # 5. Switch to Pose Mode for the armature
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='POSE')

    # 6. Select "Bone.002" (the middle bone)
    # Ensure all bones are deselected first
    for p_bone in armature_obj.pose.bones:
        p_bone.bone.select = False

    armature_obj.pose.bones["Bone.002"].bone.select = True
    bpy.context.object.data.bones.active = armature_obj.data.bones["Bone.002"]


    # 7. Rotate "Bone.002" by 45 degrees around the X-axis
    # Note: rotation is in radians
    bpy.ops.transform.rotate(value=0.785398, # 45 degrees in radians
                             orient_axis='X',
                             orient_type='GLOBAL', # Or 'LOCAL' if preferred for bone's own axis
                             constraint_axis=[True, False, False])

    print("Script finished. Cylinder created, armature created and parented, Bone.002 rotated.")

if __name__ == "__main__":
    main()
    # To make the script runnable from Blender's text editor:
    # If you want to run this script directly from Blender's Text Editor,
    # you might need to register it if it contains operators or panels.
    # For this simple script, direct execution should work fine.
    # To ensure it runs when pasted, you can also just call main() directly.
    # For example:
    # main()
    # However, the if __name__ == "__main__": block is standard practice.
    # If running via command line: blender --background --python your_script_name.py
    # The print statement at the end will show up in the console.

    # For verification, let's also set the active object to the cylinder
    # and the mode to OBJECT to make it easier to see the result if run in Blender UI.
    # bpy.ops.object.mode_set(mode='OBJECT')
    # bpy.context.view_layer.objects.active = bpy.data.objects.get("Cylinder")
    # if bpy.context.view_layer.objects.active:
    #    bpy.context.view_layer.objects.active.select_set(True)
