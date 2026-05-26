from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

from .blender_connection import BlenderConnection, DEFAULT_HOST, DEFAULT_PORT


def _configure_logging(verbosity: int) -> None:
    if verbosity >= 2:
        level = logging.DEBUG
    elif verbosity == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def _pretty_print(value: object, compact: bool) -> None:
    if isinstance(value, (dict, list)):
        print(json.dumps(value, ensure_ascii=False, indent=None if compact else 2))
        return
    print(value)


def _get_host_port(args: argparse.Namespace) -> tuple[str, int]:
    host = args.host or os.getenv("BLENDER_HOST", DEFAULT_HOST)
    port = args.port or int(os.getenv("BLENDER_PORT", str(DEFAULT_PORT)))
    return host, port


def _run_command(args: argparse.Namespace, command_type: str, params: dict | None = None) -> dict:
    host, port = _get_host_port(args)
    conn = BlenderConnection(host=host, port=port)
    if not conn.connect():
        raise SystemExit(f"Failed to connect to Blender at {host}:{port}. Is the addon server running?")
    try:
        return conn.send_command(command_type, params=params or {})
    finally:
        conn.disconnect()


def _process_bbox(original_bbox: list[float] | list[int] | None) -> list[int] | None:
    if original_bbox is None:
        return None
    if all(isinstance(i, int) for i in original_bbox):
        return list(original_bbox)
    if any(float(i) <= 0 for i in original_bbox):
        raise ValueError("bbox must be > 0")
    max_val = max(float(i) for i in original_bbox)
    return [int(float(i) / max_val * 100) for i in original_bbox] if original_bbox else None


def cmd_scene(args: argparse.Namespace) -> None:
    result = _run_command(args, "get_scene_info")
    _pretty_print(result, args.compact)


def cmd_object(args: argparse.Namespace) -> None:
    result = _run_command(args, "get_object_info", {"name": args.name})
    _pretty_print(result, args.compact)


def cmd_screenshot(args: argparse.Namespace) -> None:
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fmt = (args.format or out_path.suffix.lstrip(".") or "png").lower()
    result = _run_command(
        args,
        "get_viewport_screenshot",
        {"max_size": args.max_size, "filepath": str(out_path), "format": fmt},
    )
    _pretty_print(result, args.compact)


def _read_code_arg(args: argparse.Namespace) -> str:
    if args.code and args.file:
        raise SystemExit("Use only one of --code or --file.")
    if args.file:
        path = Path(args.file).expanduser().resolve()
        return path.read_text(encoding="utf-8")
    if args.code:
        return args.code
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("Provide --code, --file, or pipe code via stdin.")


def cmd_exec(args: argparse.Namespace) -> None:
    code = _read_code_arg(args)
    result = _run_command(args, "execute_code", {"code": code})
    _pretty_print(result, args.compact)


def cmd_raw(args: argparse.Namespace) -> None:
    params = {}
    if args.params_json:
        try:
            params = json.loads(args.params_json)
        except json.JSONDecodeError as e:
            raise SystemExit(f"Invalid JSON for --params-json: {e}")
        if not isinstance(params, dict):
            raise SystemExit("--params-json must be a JSON object (dictionary).")
    result = _run_command(args, args.type, params)
    _pretty_print(result, args.compact)


def cmd_polyhaven_status(args: argparse.Namespace) -> None:
    result = _run_command(args, "get_polyhaven_status")
    _pretty_print(result, args.compact)


def cmd_polyhaven_categories(args: argparse.Namespace) -> None:
    result = _run_command(args, "get_polyhaven_categories", {"asset_type": args.asset_type})
    _pretty_print(result, args.compact)


def cmd_polyhaven_search(args: argparse.Namespace) -> None:
    result = _run_command(
        args,
        "search_polyhaven_assets",
        {"asset_type": args.asset_type, "categories": args.categories},
    )
    _pretty_print(result, args.compact)


def cmd_polyhaven_download(args: argparse.Namespace) -> None:
    result = _run_command(
        args,
        "download_polyhaven_asset",
        {
            "asset_id": args.asset_id,
            "asset_type": args.asset_type,
            "resolution": args.resolution,
            "file_format": args.file_format,
        },
    )
    _pretty_print(result, args.compact)


def cmd_polyhaven_set_texture(args: argparse.Namespace) -> None:
    result = _run_command(
        args,
        "set_texture",
        {"object_name": args.object_name, "texture_id": args.texture_id},
    )
    _pretty_print(result, args.compact)


def cmd_sketchfab_status(args: argparse.Namespace) -> None:
    result = _run_command(args, "get_sketchfab_status")
    _pretty_print(result, args.compact)


def cmd_sketchfab_search(args: argparse.Namespace) -> None:
    result = _run_command(
        args,
        "search_sketchfab_models",
        {
            "query": args.query,
            "categories": args.categories,
            "count": args.count,
            "downloadable": args.downloadable,
        },
    )
    _pretty_print(result, args.compact)


def cmd_sketchfab_preview(args: argparse.Namespace) -> None:
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result = _run_command(args, "get_sketchfab_model_preview", {"uid": args.uid})
    if "image_data" not in result:
        _pretty_print(result, args.compact)
        return
    data = base64.b64decode(result["image_data"])
    out_path.write_bytes(data)
    _pretty_print({**result, "saved_to": str(out_path)}, args.compact)


def cmd_sketchfab_download(args: argparse.Namespace) -> None:
    result = _run_command(
        args,
        "download_sketchfab_model",
        {"uid": args.uid, "normalize_size": True, "target_size": args.target_size},
    )
    _pretty_print(result, args.compact)


def cmd_hyper3d_status(args: argparse.Namespace) -> None:
    result = _run_command(args, "get_hyper3d_status")
    _pretty_print(result, args.compact)


def cmd_hyper3d_generate_text(args: argparse.Namespace) -> None:
    bbox = _process_bbox(args.bbox) if args.bbox else None
    result = _run_command(
        args,
        "create_rodin_job",
        {"text_prompt": args.text_prompt, "images": None, "bbox_condition": bbox},
    )
    _pretty_print(result, args.compact)


def _validate_urls(urls: list[str]) -> list[str]:
    out: list[str] = []
    for u in urls:
        parsed = urlparse(u)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL: {u}")
        out.append(u)
    return out


def cmd_hyper3d_generate_images(args: argparse.Namespace) -> None:
    if args.image_path and args.image_url:
        raise SystemExit("Use only one of --image-path or --image-url.")
    if not args.image_path and not args.image_url:
        raise SystemExit("Provide at least one --image-path or --image-url.")

    bbox = _process_bbox(args.bbox) if args.bbox else None

    images: list = []
    if args.image_path:
        for p in args.image_path:
            path = Path(p).expanduser().resolve()
            if not path.exists():
                raise SystemExit(f"Image not found: {path}")
            images.append((path.suffix, base64.b64encode(path.read_bytes()).decode("ascii")))
    else:
        images = _validate_urls(args.image_url)

    result = _run_command(
        args,
        "create_rodin_job",
        {"text_prompt": None, "images": images, "bbox_condition": bbox},
    )
    _pretty_print(result, args.compact)


def cmd_hyper3d_poll(args: argparse.Namespace) -> None:
    if bool(args.subscription_key) == bool(args.request_id):
        raise SystemExit("Provide exactly one of --subscription-key or --request-id.")
    params = {"subscription_key": args.subscription_key} if args.subscription_key else {"request_id": args.request_id}
    result = _run_command(args, "poll_rodin_job_status", params)
    _pretty_print(result, args.compact)


def cmd_hyper3d_import(args: argparse.Namespace) -> None:
    if bool(args.task_uuid) == bool(args.request_id):
        raise SystemExit("Provide exactly one of --task-uuid or --request-id.")
    params = {"name": args.name, "task_uuid": args.task_uuid} if args.task_uuid else {"name": args.name, "request_id": args.request_id}
    result = _run_command(args, "import_generated_asset", params)
    _pretty_print(result, args.compact)


def cmd_hunyuan_status(args: argparse.Namespace) -> None:
    result = _run_command(args, "get_hunyuan3d_status")
    _pretty_print(result, args.compact)


def cmd_hunyuan_generate(args: argparse.Namespace) -> None:
    if not args.text_prompt and not args.image:
        raise SystemExit("Provide at least one of --text-prompt or --image.")
    result = _run_command(args, "create_hunyuan_job", {"text_prompt": args.text_prompt, "image": args.image})
    _pretty_print(result, args.compact)


def cmd_hunyuan_poll(args: argparse.Namespace) -> None:
    result = _run_command(args, "poll_hunyuan_job_status", {"job_id": args.job_id})
    _pretty_print(result, args.compact)


def cmd_hunyuan_import(args: argparse.Namespace) -> None:
    result = _run_command(args, "import_generated_asset_hunyuan", {"name": args.name, "zip_file_url": args.zip_file_url})
    _pretty_print(result, args.compact)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="blender-cli",
        description="Command-line client for the BlenderMCP addon socket server (default localhost:9876).",
    )
    parser.add_argument("--host", help="Blender addon host (or BLENDER_HOST).")
    parser.add_argument("--port", type=int, help="Blender addon port (or BLENDER_PORT).")
    parser.add_argument("--compact", action="store_true", help="Compact JSON output (no indentation).")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase logging verbosity.")

    sub = parser.add_subparsers(dest="command", required=True)

    p_scene = sub.add_parser("scene", help="Print current Blender scene info.")
    p_scene.set_defaults(func=cmd_scene)

    p_object = sub.add_parser("object", help="Print info for a named object.")
    p_object.add_argument("name")
    p_object.set_defaults(func=cmd_object)

    p_ss = sub.add_parser("screenshot", help="Save a viewport screenshot to a file.")
    p_ss.add_argument("out", help="Output path (e.g. /tmp/shot.png).")
    p_ss.add_argument("--max-size", type=int, default=800)
    p_ss.add_argument("--format", help="png/jpg/etc (defaults from filename extension).")
    p_ss.set_defaults(func=cmd_screenshot)

    p_exec = sub.add_parser("exec", help="Execute Blender Python code.")
    p_exec.add_argument("--code", help="Inline Python code.")
    p_exec.add_argument("--file", help="Path to a .py file to run.")
    p_exec.set_defaults(func=cmd_exec)

    p_raw = sub.add_parser("raw", help="Send a raw command type + JSON params to Blender.")
    p_raw.add_argument("type", help="Command type (e.g. get_scene_info).")
    p_raw.add_argument("--params-json", help="JSON object string for params.")
    p_raw.set_defaults(func=cmd_raw)

    # PolyHaven
    p_poly = sub.add_parser("polyhaven", help="PolyHaven integration commands.")
    poly_sub = p_poly.add_subparsers(dest="poly_cmd", required=True)

    p_poly_status = poly_sub.add_parser("status")
    p_poly_status.set_defaults(func=cmd_polyhaven_status)

    p_poly_cat = poly_sub.add_parser("categories")
    p_poly_cat.add_argument("--asset-type", default="hdris", choices=["hdris", "textures", "models", "all"])
    p_poly_cat.set_defaults(func=cmd_polyhaven_categories)

    p_poly_search = poly_sub.add_parser("search")
    p_poly_search.add_argument("--asset-type", default="hdris", choices=["hdris", "textures", "models", "all"])
    p_poly_search.add_argument("--categories", help="Comma-separated categories.")
    p_poly_search.set_defaults(func=cmd_polyhaven_search)

    p_poly_dl = poly_sub.add_parser("download")
    p_poly_dl.add_argument("asset_id")
    p_poly_dl.add_argument("--asset-type", required=True, choices=["hdris", "textures", "models"])
    p_poly_dl.add_argument("--resolution", default="1k")
    p_poly_dl.add_argument("--file-format")
    p_poly_dl.set_defaults(func=cmd_polyhaven_download)

    p_poly_set = poly_sub.add_parser("set-texture")
    p_poly_set.add_argument("object_name")
    p_poly_set.add_argument("texture_id")
    p_poly_set.set_defaults(func=cmd_polyhaven_set_texture)

    # Sketchfab
    p_sk = sub.add_parser("sketchfab", help="Sketchfab integration commands.")
    sk_sub = p_sk.add_subparsers(dest="sk_cmd", required=True)

    p_sk_status = sk_sub.add_parser("status")
    p_sk_status.set_defaults(func=cmd_sketchfab_status)

    p_sk_search = sk_sub.add_parser("search")
    p_sk_search.add_argument("query")
    p_sk_search.add_argument("--categories")
    p_sk_search.add_argument("--count", type=int, default=20)
    p_sk_search.add_argument("--downloadable", action=argparse.BooleanOptionalAction, default=True)
    p_sk_search.set_defaults(func=cmd_sketchfab_search)

    p_sk_prev = sk_sub.add_parser("preview")
    p_sk_prev.add_argument("uid")
    p_sk_prev.add_argument("--out", required=True)
    p_sk_prev.set_defaults(func=cmd_sketchfab_preview)

    p_sk_dl = sk_sub.add_parser("download")
    p_sk_dl.add_argument("uid")
    p_sk_dl.add_argument("--target-size", type=float, required=True)
    p_sk_dl.set_defaults(func=cmd_sketchfab_download)

    # Hyper3D
    p_h3d = sub.add_parser("hyper3d", help="Hyper3D Rodin integration commands.")
    h3d_sub = p_h3d.add_subparsers(dest="h3d_cmd", required=True)

    p_h3d_status = h3d_sub.add_parser("status")
    p_h3d_status.set_defaults(func=cmd_hyper3d_status)

    p_h3d_txt = h3d_sub.add_parser("generate-text")
    p_h3d_txt.add_argument("text_prompt")
    p_h3d_txt.add_argument("--bbox", nargs=3, type=float, metavar=("L", "W", "H"))
    p_h3d_txt.set_defaults(func=cmd_hyper3d_generate_text)

    p_h3d_img = h3d_sub.add_parser("generate-images")
    p_h3d_img.add_argument("--image-path", action="append", help="Local image path (repeatable).")
    p_h3d_img.add_argument("--image-url", action="append", help="Remote image URL (repeatable).")
    p_h3d_img.add_argument("--bbox", nargs=3, type=float, metavar=("L", "W", "H"))
    p_h3d_img.set_defaults(func=cmd_hyper3d_generate_images)

    p_h3d_poll = h3d_sub.add_parser("poll")
    p_h3d_poll.add_argument("--subscription-key")
    p_h3d_poll.add_argument("--request-id")
    p_h3d_poll.set_defaults(func=cmd_hyper3d_poll)

    p_h3d_imp = h3d_sub.add_parser("import")
    p_h3d_imp.add_argument("name")
    p_h3d_imp.add_argument("--task-uuid")
    p_h3d_imp.add_argument("--request-id")
    p_h3d_imp.set_defaults(func=cmd_hyper3d_import)

    # Hunyuan3D
    p_hy = sub.add_parser("hunyuan3d", help="Hunyuan3D integration commands.")
    hy_sub = p_hy.add_subparsers(dest="hy_cmd", required=True)

    p_hy_status = hy_sub.add_parser("status")
    p_hy_status.set_defaults(func=cmd_hunyuan_status)

    p_hy_gen = hy_sub.add_parser("generate")
    p_hy_gen.add_argument("--text-prompt")
    p_hy_gen.add_argument("--image", help="Local path or remote URL depending on addon mode.")
    p_hy_gen.set_defaults(func=cmd_hunyuan_generate)

    p_hy_poll = hy_sub.add_parser("poll")
    p_hy_poll.add_argument("job_id")
    p_hy_poll.set_defaults(func=cmd_hunyuan_poll)

    p_hy_imp = hy_sub.add_parser("import")
    p_hy_imp.add_argument("name")
    p_hy_imp.add_argument("zip_file_url")
    p_hy_imp.set_defaults(func=cmd_hunyuan_import)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.verbose)
    args.func(args)


if __name__ == "__main__":
    main()

