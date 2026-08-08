# API Reference

All tools are available to Claude once connected.

## get_scene_info
Returns all objects, lights, cameras, and materials in the scene.

## get_object_info
```
name: string  — object name in Blender
```

## get_viewport_screenshot
Returns an image of the current 3D viewport.

## create_object
```
type:     MESH | LIGHT | CAMERA | EMPTY | ARMATURE
name:     string
location: [x, y, z]
rotation: [x, y, z]   (radians)
scale:    [x, y, z]
```

## modify_object
Modify location, rotation, scale, or name of an existing object.

## delete_object
```
name: string
```

## set_material / create_material
Apply or create PBR materials with color, metallic, roughness, emission.

## execute_blender_code
```
code: string  — Python code to run inside Blender
```
> ⚠️ Runs arbitrary Python. Save work first.

## search_polyhaven_assets
```
query:      string
asset_type: hdri | texture | model
```

## download_polyhaven_asset
Downloads and imports a Poly Haven asset.

## search_sketchfab_models
```
query: string
```

## generate_hyper3d_model
Generate a 3D model using Hyper3D Rodin AI.
```
prompt: string
```

## generate_hunyuan3d_model
Generate a 3D model using Hunyuan3D.
```
prompt: string
```
