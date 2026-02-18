import bpy
from pathlib import Path

def screenshot_view3d_save(save_path: str, max_size: int = 800, format: str = "png", area_index: int = 0):
    """
    Capture and save a Blender viewport screenshot (crop top TOOL_HEADER area +
    scale proportionally by max_size + disable/restore Overlay and Gizmo + clear cache).

    Inputs:
      - save_path: output file path (supports Blender // relative path)
      - max_size : max width or height of output image (keep aspect ratio)
      - format   : "png" / "jpg" / "jpeg" / "tif" / "tiff" / "bmp" / "exr" ...
      - area_index: which VIEW_3D area to use when multiple exist (default 0)
    """

    # ---------------------------
    # 0) Path handling
    # ---------------------------
    if max_size is None or int(max_size) <= 0:
        raise ValueError("max_size must be a positive integer.")
    max_size = int(max_size)

    save_path_abs = Path(bpy.path.abspath(save_path))
    save_path_abs.parent.mkdir(parents=True, exist_ok=True)

    fmt = (format or "png").strip().lower()
    if save_path_abs.suffix == "":
        save_path_abs = save_path_abs.with_suffix(f".{fmt}")

    # Temporary output (Blender writes raw screenshot first)
    tmp_path = save_path_abs.with_name(save_path_abs.stem + "__tmp_raw.png")

    # ---------------------------
    # 1) Find VIEW_3D area
    # ---------------------------
    window = bpy.context.window
    screen = window.screen

    view3d_areas = [a for a in screen.areas if a.type == "VIEW_3D"]
    if not view3d_areas:
        raise RuntimeError("No area with type='VIEW_3D' found in current screen. Ensure a 3D viewport is open.")
    if area_index < 0 or area_index >= len(view3d_areas):
        raise IndexError(f"area_index={area_index} out of range, VIEW_3D count={len(view3d_areas)}")

    area = view3d_areas[area_index]

    # ---------------------------
    # 2) Find WINDOW and TOOL_HEADER regions
    # ---------------------------
    region_window = next((r for r in area.regions if r.type == "WINDOW"), None)
    region_tool_header = next((r for r in area.regions if r.type == "TOOL_HEADER"), None)
    if region_window is None or region_tool_header is None:
        raise RuntimeError("VIEW_3D area is missing WINDOW region or TOOL_HEADER region.")

    # Get area space_data (VIEW_3D SpaceView3D)
    space = area.spaces.active
    if space is None or space.type != "VIEW_3D":
        raise RuntimeError("area.spaces.active is not VIEW_3D space, cannot operate overlay/gizmo.")

    # ---------------------------
    # 3) Save overlay/gizmo states, disable before capture, restore after capture
    # ---------------------------
    # Overlay
    has_overlay = hasattr(space, "overlay") and hasattr(space.overlay, "show_overlays")
    old_show_overlays = space.overlay.show_overlays if has_overlay else None

    # Gizmo (field name may differ across versions)
    old_show_gizmo = None
    gizmo_attr = None
    for candidate in ("show_gizmo", "show_gizmo_context", "show_gizmo_navigate", "show_gizmo_tool"):
        if hasattr(space, candidate):
            gizmo_attr = candidate
            old_show_gizmo = getattr(space, candidate)
            break
    
    old_show_toolbar = getattr(space, "show_region_toolbar", None)   # left toolbar (Tools)
    old_show_sidebar = getattr(space, "show_region_ui", None)        # right sidebar (N panel)

    try:
        if has_overlay:
            space.overlay.show_overlays = False
        if gizmo_attr is not None:
            setattr(space, gizmo_attr, False)
        if old_show_toolbar is not None:
            space.show_region_toolbar = False
        if old_show_sidebar is not None:
            space.show_region_ui = False
        area.tag_redraw()
        # ---------------------------
        # 4) Save WINDOW image first (via screenshot_area), then process in Blender:
        #    - crop top area matching TOOL_HEADER height
        #    - proportional scaling by max_size
        #    - save to save_path using requested format
        # ---------------------------

        # 4.1 Let Blender write a raw screenshot first
        # Note: screenshot_area effectively captures the area;
        # we still use region=WINDOW to satisfy operator polling requirements.
        with bpy.context.temp_override(window=window, screen=screen, area=area, region=region_window):
            ret = bpy.ops.screen.screenshot_area(filepath=str(tmp_path), check_existing=False)
        if "FINISHED" not in ret:
            raise RuntimeError(f"screenshot_area did not finish successfully, return: {ret}")

        # 4.2 Load temporary screenshot into Blender (processing input)
        src_img = bpy.data.images.load(str(tmp_path))
        src_w, src_h = src_img.size  # pixel dimensions
        src_pixels = list(src_img.pixels)  # RGBA, origin=bottom-left

        # 4.3 Crop: remove top TOOL_HEADER height
        # TOOL_HEADER is at top, remove the highest tool_h pixel rows
        tool_h = int(region_tool_header.height*2) if region_tool_header.height else 0
        tool_h = max(0, min(tool_h, src_h))

        # Height after crop
        crop_w = src_w
        crop_h = src_h - tool_h
        if crop_h <= 0:
            # Extreme case (tool_h>=src_h): skip cropping
            crop_h = src_h
            tool_h = 0

        # Compute retained pixel region: y in [0, crop_h-1]
        # Since origin is bottom-left, larger y means closer to top
        cropped_pixels = [0.0] * (crop_w * crop_h * 4)
        for y in range(crop_h):
            src_row_start = (y * src_w) * 4
            src_row_end   = ((y + 1) * src_w) * 4
            dst_row_start = (y * crop_w) * 4
            cropped_pixels[dst_row_start:dst_row_start + crop_w * 4] = src_pixels[src_row_start:src_row_end]

        # 4.4 Create cropped image and write pixels
        crop_img = bpy.data.images.new(name="__crop_tmp__", width=crop_w, height=crop_h, alpha=True)
        crop_img.pixels = cropped_pixels

        # 4.5 Scale by max_size while keeping aspect ratio (max(width,height)=max_size)
        out_w, out_h = crop_w, crop_h
        m = max(out_w, out_h)
        if m > max_size:
            scale = max_size / float(m)
            out_w = max(1, int(round(out_w * scale)))
            out_h = max(1, int(round(out_h * scale)))
            crop_img.scale(out_w, out_h)

        # 4.6 Save as requested format
        # Blender file_format enums: PNG/JPEG/TIFF/BMP/OPEN_EXR...
        fmt_map = {
            "png": "PNG",
            "jpg": "JPEG",
            "jpeg": "JPEG",
            "tif": "TIFF",
            "tiff": "TIFF",
            "bmp": "BMP",
            "exr": "OPEN_EXR",
            "openexr": "OPEN_EXR",
            "tga": "TARGA",
            "hdr": "HDR",
        }
        file_format = fmt_map.get(fmt, "PNG")  # fallback to PNG if unrecognized

        crop_img.filepath_raw = str(save_path_abs)
        crop_img.file_format = file_format
        crop_img.save()

    finally:
        # ---------------------------
        # 3) Restore original overlay/gizmo states
        # ---------------------------
        try:
            if has_overlay and old_show_overlays is not None:
                space.overlay.show_overlays = old_show_overlays
            if gizmo_attr is not None and old_show_gizmo is not None:
                setattr(space, gizmo_attr, old_show_gizmo)
            if old_show_toolbar is not None:
                space.show_region_toolbar = old_show_toolbar
            if old_show_sidebar is not None:
                space.show_region_ui = old_show_sidebar
        except Exception:
            # Do not block on restore failure; UI state may remain changed
            pass

        # ---------------------------
        # 5) Clear Blender internal cache (remove loaded/created images)
        # ---------------------------
        for name in ("src_img", "crop_img"):
            if name in locals():
                try:
                    bpy.data.images.remove(locals()[name])
                except Exception:
                    pass

        # Delete temporary disk file
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

    print(f"[OK] saved: {save_path_abs}  (max_size={max_size}, format={fmt})")


# =========================
# Example invocation (edit path as needed)
# =========================
if __name__ == "__main__":
    screenshot_view3d_save(
        save_path="//view3d_clean.png",  # Blender relative path is supported
        max_size=1024,
        format="png",
    )
