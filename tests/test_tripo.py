"""Tripo generation stays behind the sidebar switch and never echoes the API key."""
import importlib.util
import sys
import types

from conftest import ROOT_ADDON as ADDON


def _install_bpy_stubs(monkeypatch, scene):
    bpy = types.ModuleType("bpy")
    bpy.context = types.SimpleNamespace(
        scene=scene,
        preferences=types.SimpleNamespace(addons={}),
        view_layer=types.SimpleNamespace(update=lambda: None),
    )
    bpy.types = types.SimpleNamespace(
        AddonPreferences=object,
        Operator=object,
        Panel=object,
        Scene=type("Scene", (), {}),
    )
    bpy.ops = types.SimpleNamespace(
        import_scene=types.SimpleNamespace(gltf=lambda **_kwargs: None),
    )
    bpy.data = types.SimpleNamespace(objects=[])

    props = types.ModuleType("bpy.props")
    for name in ("BoolProperty", "EnumProperty", "FloatProperty", "IntProperty", "StringProperty"):
        setattr(props, name, lambda **_kwargs: None)
    bpy.props = props

    handlers = types.ModuleType("bpy.app.handlers")
    handlers.persistent = lambda fn: fn
    handlers.undo_post = []
    handlers.redo_post = []
    handlers.depsgraph_update_post = []

    app = types.ModuleType("bpy.app")
    app.version = (4, 2, 0)
    app.version_string = "4.2.0"
    app.background = False
    app.handlers = handlers
    app.timers = types.SimpleNamespace(
        is_registered=lambda *_a, **_k: False,
        register=lambda *_a, **_k: None,
        unregister=lambda *_a, **_k: None,
    )
    bpy.app = app

    monkeypatch.setitem(sys.modules, "bpy", bpy)
    monkeypatch.setitem(sys.modules, "bpy.props", props)
    monkeypatch.setitem(sys.modules, "bpy.app", app)
    monkeypatch.setitem(sys.modules, "bpy.app.handlers", handlers)
    monkeypatch.setitem(sys.modules, "mathutils", types.ModuleType("mathutils"))

    requests = types.ModuleType("requests")
    requests.utils = types.SimpleNamespace(default_headers=dict)
    requests.exceptions = types.SimpleNamespace(Timeout=TimeoutError)
    monkeypatch.setitem(sys.modules, "requests", requests)
    return bpy


def _load_addon(monkeypatch, **scene_attrs):
    scene = types.SimpleNamespace(
        blendermcp_use_tripo=False,
        blendermcp_tripo_model="H3.1",
        blendermcp_tripo_api_key="",
        blendermcp_use_polyhaven=False,
        blendermcp_use_hyper3d=False,
        blendermcp_use_hunyuan3d=False,
        blendermcp_use_sketchfab=False,
        blendermcp_use_polypizza=False,
    )
    for key, value in scene_attrs.items():
        setattr(scene, key, value)
    bpy = _install_bpy_stubs(monkeypatch, scene)
    spec = importlib.util.spec_from_file_location("blender_mcp_addon_tripo_test", ADDON)
    addon = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(addon)
    return addon, bpy, scene


class _JsonResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.ok = 200 <= status_code < 300

    def json(self):
        return self._payload


def _capture_posts(addon):
    posts = []

    def post(url, headers=None, json=None, files=None, **_kwargs):
        posts.append({"url": url, "headers": headers or {}, "json": json, "files": files})
        if url.endswith("/files"):
            return _JsonResponse({"code": 0, "data": {"file_token": "file_abc"}})
        return _JsonResponse({"code": 0, "data": {"task_id": "task_abc"}})

    addon.requests.post = post
    return posts


def test_tripo_status_reports_sidebar_state(monkeypatch):
    addon, _bpy, scene = _load_addon(monkeypatch)
    server = addon.BlenderMCPServer()

    disabled = server.get_tripo_status()
    assert disabled["enabled"] is False
    assert "AI Model Generation" in disabled["message"]
    assert "Tripo AI" in disabled["message"]

    scene.blendermcp_use_tripo = True
    missing_key = server.get_tripo_status()
    assert missing_key["enabled"] is False
    assert "API key" in missing_key["message"]
    assert "Tripo AI" in missing_key["message"]

    scene.blendermcp_tripo_api_key = "super-secret-tripo"
    scene.blendermcp_tripo_model = "P2.0"
    ready = server.get_tripo_status()
    assert ready["enabled"] is True
    assert ready["model"] == "P2.0"
    assert "H3.1" in ready["message"]
    assert "P2.0" in ready["message"]
    assert "super-secret-tripo" not in ready["message"]


def test_tripo_text_job_uses_sidebar_model(monkeypatch):
    addon, _bpy, scene = _load_addon(
        monkeypatch,
        blendermcp_use_tripo=True,
        blendermcp_tripo_api_key="super-secret-tripo",
        blendermcp_tripo_model="P2.0",
    )
    posts = _capture_posts(addon)
    server = addon.BlenderMCPServer()

    result = server.create_tripo_job(text_prompt="a ceramic teapot")

    assert result["task_id"] == "task_abc"
    assert result["model"] == "P2.0"
    assert len(posts) == 1
    assert posts[0]["url"].endswith("/generation/text-to-model")
    assert posts[0]["json"]["model"] == addon.TRIPO_MODELS["P2.0"]
    assert posts[0]["json"]["prompt"] == "a ceramic teapot"
    assert posts[0]["json"]["texture"] is True
    assert posts[0]["json"]["pbr"] is True
    assert posts[0]["headers"]["Authorization"] == "Bearer super-secret-tripo"
    assert "super-secret-tripo" not in str(result)


def test_tripo_model_argument_overrides_sidebar(monkeypatch):
    addon, _bpy, _scene = _load_addon(
        monkeypatch,
        blendermcp_use_tripo=True,
        blendermcp_tripo_api_key="super-secret-tripo",
        blendermcp_tripo_model="H3.1",
    )
    posts = _capture_posts(addon)
    server = addon.BlenderMCPServer()

    result = server.create_tripo_job(text_prompt="a chair", model="P2.0")

    assert result["model"] == "P2.0"
    assert posts[0]["json"]["model"] == addon.TRIPO_MODELS["P2.0"]


def test_tripo_rejects_unknown_model_without_calling_api(monkeypatch):
    addon, _bpy, _scene = _load_addon(
        monkeypatch,
        blendermcp_use_tripo=True,
        blendermcp_tripo_api_key="super-secret-tripo",
    )
    posts = _capture_posts(addon)
    server = addon.BlenderMCPServer()

    result = server.create_tripo_job(text_prompt="a chair", model="v9-nope")

    assert "error" in result
    assert "H3.1" in result["error"]
    assert "P2.0" in result["error"]
    assert posts == []


def test_tripo_image_url_skips_upload(monkeypatch):
    addon, _bpy, _scene = _load_addon(
        monkeypatch,
        blendermcp_use_tripo=True,
        blendermcp_tripo_api_key="super-secret-tripo",
    )
    posts = _capture_posts(addon)
    server = addon.BlenderMCPServer()

    result = server.create_tripo_job(image="https://example.com/teapot.png")

    assert result["task_id"] == "task_abc"
    assert len(posts) == 1
    assert posts[0]["url"].endswith("/generation/image-to-model")
    assert posts[0]["json"]["input"] == "https://example.com/teapot.png"
    assert posts[0]["json"]["model"] == addon.TRIPO_MODELS["H3.1"]


def test_tripo_local_image_uploads_then_submits(monkeypatch, tmp_path):
    image = tmp_path / "ref.png"
    image.write_bytes(b"\x89PNG\r\n")
    addon, _bpy, _scene = _load_addon(
        monkeypatch,
        blendermcp_use_tripo=True,
        blendermcp_tripo_api_key="super-secret-tripo",
    )
    posts = _capture_posts(addon)
    server = addon.BlenderMCPServer()

    result = server.create_tripo_job(image=str(image))

    assert result["task_id"] == "task_abc"
    assert posts[0]["url"].endswith("/files")
    assert "file" in posts[0]["files"]
    assert posts[1]["url"].endswith("/generation/image-to-model")
    assert posts[1]["json"]["input"] == "file_abc"


def test_tripo_rejects_text_and_image_together(monkeypatch):
    addon, _bpy, _scene = _load_addon(
        monkeypatch,
        blendermcp_use_tripo=True,
        blendermcp_tripo_api_key="super-secret-tripo",
    )
    posts = _capture_posts(addon)
    server = addon.BlenderMCPServer()

    result = server.create_tripo_job(text_prompt="a teapot", image="https://example.com/a.png")

    assert "error" in result
    assert posts == []


def test_tripo_poll_returns_model_url_and_quotes_task_id(monkeypatch):
    addon, _bpy, _scene = _load_addon(
        monkeypatch,
        blendermcp_tripo_api_key="super-secret-tripo",
    )
    seen = {}

    def get(url, headers=None, **_kwargs):
        seen["url"] = url
        seen["headers"] = headers
        return _JsonResponse({
            "code": 0,
            "data": {
                "task_id": "task/abc",
                "status": "success",
                "progress": 100,
                "output": {"pbr_model": "https://cdn.example/model.glb"},
            },
        })

    addon.requests.get = get
    server = addon.BlenderMCPServer()

    result = server.poll_tripo_job_status(task_id="task/abc")

    assert result["status"] == "success"
    assert result["model_url"] == "https://cdn.example/model.glb"
    assert seen["url"].endswith("/tasks/task%2Fabc")
    assert "super-secret-tripo" not in str(result)


def test_tripo_import_rejects_non_http_url(monkeypatch):
    addon, _bpy, _scene = _load_addon(monkeypatch)
    server = addon.BlenderMCPServer()

    result = server.import_generated_asset_tripo(name="Teapot", model_url="/tmp/model.glb")

    assert result["succeed"] is False


def test_tripo_import_downloads_glb(monkeypatch):
    addon, _bpy, _scene = _load_addon(monkeypatch)
    server = addon.BlenderMCPServer()
    downloaded = {}

    class _Stream:
        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size=8192):
            yield b"glb-bytes"

    addon.requests.get = lambda url, stream=False: _Stream()

    def fake_clean(filepath, mesh_name=None):
        with open(filepath, "rb") as handle:
            downloaded["bytes"] = handle.read()
        downloaded["name"] = mesh_name
        return types.SimpleNamespace(
            name=mesh_name,
            type="MESH",
            location=types.SimpleNamespace(x=1, y=2, z=3),
            rotation_euler=types.SimpleNamespace(x=0, y=0, z=0),
            scale=types.SimpleNamespace(x=1, y=1, z=1),
        )

    server._clean_imported_glb = fake_clean
    server._get_aabb = lambda _obj: [[0, 0, 0], [1, 1, 1]]

    result = server.import_generated_asset_tripo(
        name="Teapot",
        model_url="https://cdn.example/model.glb",
    )

    assert result["succeed"] is True
    assert result["name"] == "Teapot"
    assert result["world_bounding_box"] == [[0, 0, 0], [1, 1, 1]]
    assert downloaded["bytes"] == b"glb-bytes"


def test_tripo_commands_stay_unregistered_until_enabled(monkeypatch):
    addon, _bpy, scene = _load_addon(monkeypatch, blendermcp_tripo_api_key="super-secret-tripo")
    server = addon.BlenderMCPServer()

    blocked = server._execute_command_internal({
        "type": "create_tripo_job",
        "params": {"text_prompt": "a teapot"},
    })
    assert blocked["status"] == "error"
    assert "Unknown command type" in blocked["message"]

    scene.blendermcp_use_tripo = True
    posts = _capture_posts(addon)
    allowed = server._execute_command_internal({
        "type": "create_tripo_job",
        "params": {"text_prompt": "a teapot"},
    })
    assert allowed["status"] == "success"
    assert allowed["result"]["task_id"] == "task_abc"
    assert posts
