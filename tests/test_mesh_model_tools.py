"""Regression coverage for the mesh_*/model_* geometry-editing addon handlers."""
import importlib.util
import math
import sys
import types

import pytest

from conftest import ROOT_ADDON as ADDON


class _FakeVector:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x, self.y, self.z = x, y, z

    def copy(self):
        return _FakeVector(self.x, self.y, self.z)

    def __iter__(self):
        return iter((self.x, self.y, self.z))

    def __eq__(self, other):
        return tuple(self) == tuple(other)


class _FakeMeshData:
    def __init__(self, n_verts=8, n_edges=12, n_polys=6):
        self.vertices = [object() for _ in range(n_verts)]
        self.edges = [object() for _ in range(n_edges)]
        self.polygons = [object() for _ in range(n_polys)]
        self.remesh_voxel_size = 0.1


class _FakeModifier:
    def __init__(self, name, type):
        self.name = name
        self.type = type


class _FakeModifiers(list):
    def new(self, name, type):
        mod = _FakeModifier(name, type)
        self.append(mod)
        return mod

    def get(self, name):
        return next((m for m in self if m.name == name), None)


class _FakeObject:
    def __init__(self, name, obj_type):
        self.name = name
        self.type = obj_type
        self.location = _FakeVector()
        self.rotation_euler = _FakeVector()
        self.scale = _FakeVector(1.0, 1.0, 1.0)
        self.data = _FakeMeshData() if obj_type == "MESH" else None
        self.modifiers = _FakeModifiers()
        self.material_slots = []
        self._custom = {}
        self.selected = False

    def select_set(self, value):
        self.selected = value

    def visible_get(self):
        return True

    def __setitem__(self, key, value):
        self._custom[key] = value

    def __getitem__(self, key):
        return self._custom[key]


class _FakeObjectsCollection(dict):
    def get(self, name, default=None):
        return dict.get(self, name, default)

    def new(self, name, data):
        obj = _FakeObject(name, "MESH" if data is not None else "EMPTY")
        self[obj.name] = obj
        return obj

    def remove(self, obj, do_unlink=True):
        self.pop(obj.name, None)


class _FakeBMElem:
    def __init__(self):
        self.select = False


class _FakeBMElemSeq(list):
    def ensure_lookup_table(self):
        pass


class _FakeBMesh:
    def __init__(self, mesh_data):
        self.verts = _FakeBMElemSeq(_FakeBMElem() for _ in mesh_data.vertices)
        self.edges = _FakeBMElemSeq(_FakeBMElem() for _ in mesh_data.edges)
        self.faces = _FakeBMElemSeq(_FakeBMElem() for _ in mesh_data.polygons)

    def select_flush(self, _value):
        pass


def _load_addon(monkeypatch):
    scene = types.SimpleNamespace(
        blendermcp_use_polyhaven=False,
        blendermcp_use_hyper3d=False,
        blendermcp_use_hunyuan3d=False,
        blendermcp_use_sketchfab=False,
    )

    objects = _FakeObjectsCollection()
    primitive_counter = {"n": 0}

    def _make_primitive_op(prefix, obj_type="MESH"):
        def op(**kwargs):
            primitive_counter["n"] += 1
            name = f"{prefix}.{primitive_counter['n']:03d}"
            obj = _FakeObject(name, obj_type)
            location = kwargs.get("location", (0, 0, 0))
            rotation = kwargs.get("rotation", (0, 0, 0))
            obj.location = _FakeVector(*location)
            obj.rotation_euler = _FakeVector(*rotation)
            objects[name] = obj
            bpy.context.view_layer.objects.active = obj
            bpy.context.active_object = obj
            return {"FINISHED"}
        return op

    def _noop(**_kwargs):
        return {"FINISHED"}

    def _mode_set(mode):
        pass

    def _modifier_apply(modifier):
        obj = bpy.context.view_layer.objects.active
        mod = obj.modifiers.get(modifier)
        if mod is not None:
            obj.modifiers.remove(mod)

    def _select_all(action="SELECT"):
        pass

    bpy = types.ModuleType("bpy")
    bpy.data = types.SimpleNamespace(objects=objects, textures=types.SimpleNamespace(
        new=lambda name, type: types.SimpleNamespace(name=name, type=type, noise_scale=0.0)
    ))
    bpy.context = types.SimpleNamespace(
        scene=scene,
        view_layer=types.SimpleNamespace(objects=types.SimpleNamespace(active=None)),
        active_object=None,
        collection=types.SimpleNamespace(objects=types.SimpleNamespace(link=lambda _obj: None)),
    )
    bpy.types = types.SimpleNamespace(
        AddonPreferences=object,
        Operator=object,
        Panel=object,
        Scene=type("Scene", (), {}),
    )
    bpy.ops = types.SimpleNamespace(
        mesh=types.SimpleNamespace(
            primitive_cube_add=_make_primitive_op("Cube"),
            primitive_uv_sphere_add=_make_primitive_op("Sphere"),
            primitive_cylinder_add=_make_primitive_op("Cylinder"),
            primitive_cone_add=_make_primitive_op("Cone"),
            primitive_torus_add=_make_primitive_op("Torus"),
            primitive_plane_add=_make_primitive_op("Plane"),
            extrude_region_move=_noop,
            inset_faces=_noop,
            bevel=_noop,
            bridge_edge_loops=_noop,
            subdivide=_noop,
            symmetrize=_noop,
        ),
        curve=types.SimpleNamespace(
            primitive_bezier_curve_add=_make_primitive_op("BezierCurve", obj_type="CURVE"),
        ),
        object=types.SimpleNamespace(
            select_all=_select_all,
            mode_set=_mode_set,
            modifier_apply=_modifier_apply,
            shade_smooth=_noop,
            voxel_remesh=_noop,
        ),
    )

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

    bmesh = types.ModuleType("bmesh")
    bmesh.from_edit_mesh = lambda mesh_data: _FakeBMesh(mesh_data)
    bmesh.update_edit_mesh = lambda _mesh_data: None

    monkeypatch.setitem(sys.modules, "bpy", bpy)
    monkeypatch.setitem(sys.modules, "bpy.props", props)
    monkeypatch.setitem(sys.modules, "bpy.app", app)
    monkeypatch.setitem(sys.modules, "bpy.app.handlers", handlers)
    monkeypatch.setitem(sys.modules, "mathutils", types.ModuleType("mathutils"))
    monkeypatch.setitem(sys.modules, "bmesh", bmesh)

    requests = types.ModuleType("requests")
    requests.utils = types.SimpleNamespace(default_headers=dict)
    requests.exceptions = types.SimpleNamespace(Timeout=TimeoutError)
    monkeypatch.setitem(sys.modules, "requests", requests)

    spec = importlib.util.spec_from_file_location("blender_mcp_addon_mesh_model_test", ADDON)
    addon = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(addon)
    return addon, bpy


def _new_mesh_object(bpy, name):
    obj = bpy.data.objects.new(name, object())
    return obj


def _new_empty_object(bpy, name):
    obj = bpy.data.objects.new(name, None)
    return obj


@pytest.mark.parametrize("primitive_type,expected_obj_type", [
    ("CUBE", "MESH"),
    ("SPHERE", "MESH"),
    ("CYLINDER", "MESH"),
    ("CONE", "MESH"),
    ("TORUS", "MESH"),
    ("PLANE", "MESH"),
    ("CURVE", "CURVE"),
    ("cube", "MESH"),
])
def test_create_primitive_dispatches_to_the_right_op(monkeypatch, primitive_type, expected_obj_type):
    addon, _bpy = _load_addon(monkeypatch)
    server = addon.BlenderMCPServer()

    result = server.create_primitive(primitive_type=primitive_type, name=f"obj_{primitive_type}")

    assert result["name"] == f"obj_{primitive_type}"
    assert result["type"] == expected_obj_type


def test_create_primitive_rejects_unknown_type(monkeypatch):
    addon, _bpy = _load_addon(monkeypatch)
    server = addon.BlenderMCPServer()

    with pytest.raises(ValueError, match="Unknown primitive_type"):
        server.create_primitive(primitive_type="DODECAHEDRON")


MESH_HANDLER_CALLS = [
    ("mesh_extrude", {}),
    ("mesh_inset", {}),
    ("mesh_bevel", {}),
    ("mesh_bridge", {"edge_indices": [0, 1]}),
    ("mesh_subdivide", {}),
    ("mesh_remesh", {}),
    ("mesh_solidify", {}),
    ("model_refine", {}),
    ("model_detail", {}),
    ("model_symmetrize", {}),
    ("model_mirror", {}),
    ("model_array", {}),
    ("model_radial_array", {}),
]


@pytest.mark.parametrize("handler_name,extra_kwargs", MESH_HANDLER_CALLS)
def test_mesh_handlers_reject_missing_object(monkeypatch, handler_name, extra_kwargs):
    addon, _bpy = _load_addon(monkeypatch)
    server = addon.BlenderMCPServer()

    with pytest.raises(ValueError, match="Object not found"):
        getattr(server, handler_name)(object_name="does_not_exist", **extra_kwargs)


@pytest.mark.parametrize("handler_name,extra_kwargs", MESH_HANDLER_CALLS)
def test_mesh_handlers_reject_non_mesh_object(monkeypatch, handler_name, extra_kwargs):
    addon, bpy = _load_addon(monkeypatch)
    server = addon.BlenderMCPServer()
    _new_empty_object(bpy, "empty_obj")

    with pytest.raises(ValueError, match="is not a mesh"):
        getattr(server, handler_name)(object_name="empty_obj", **extra_kwargs)


def test_mesh_boolean_rejects_invalid_operation(monkeypatch):
    addon, bpy = _load_addon(monkeypatch)
    server = addon.BlenderMCPServer()
    _new_mesh_object(bpy, "target")
    _new_mesh_object(bpy, "cutter")

    with pytest.raises(ValueError, match="Invalid operation"):
        server.mesh_boolean(object_name="target", cutter_object_name="cutter", operation="XOR")


def test_mesh_boolean_deletes_cutter_by_default(monkeypatch):
    addon, bpy = _load_addon(monkeypatch)
    server = addon.BlenderMCPServer()
    _new_mesh_object(bpy, "target")
    _new_mesh_object(bpy, "cutter")

    result = server.mesh_boolean(object_name="target", cutter_object_name="cutter")

    assert result["name"] == "target"
    assert bpy.data.objects.get("cutter") is None


def test_mesh_boolean_keeps_cutter_when_requested(monkeypatch):
    addon, bpy = _load_addon(monkeypatch)
    server = addon.BlenderMCPServer()
    _new_mesh_object(bpy, "target2")
    _new_mesh_object(bpy, "cutter2")

    server.mesh_boolean(object_name="target2", cutter_object_name="cutter2", keep_target=True)

    assert bpy.data.objects.get("cutter2") is not None


def test_model_match_reference_copies_only_flagged_components(monkeypatch):
    addon, bpy = _load_addon(monkeypatch)
    server = addon.BlenderMCPServer()
    obj = _new_mesh_object(bpy, "A")
    obj.location = _FakeVector(1, 2, 3)
    obj.rotation_euler = _FakeVector(0, 0, 0)
    obj.scale = _FakeVector(1, 1, 1)
    ref = _new_mesh_object(bpy, "B")
    ref.location = _FakeVector(4, 5, 6)
    ref.rotation_euler = _FakeVector(0.1, 0.2, 0.3)
    ref.scale = _FakeVector(2, 2, 2)

    result = server.model_match_reference(
        object_name="A", reference_object_name="B",
        match_location=True, match_rotation=False, match_scale=True,
    )

    assert result["location"] == [4, 5, 6]
    assert obj.rotation_euler == _FakeVector(0, 0, 0)
    assert result["scale"] == [2, 2, 2]


def test_model_radial_array_creates_and_rotates_helper_empty(monkeypatch):
    addon, bpy = _load_addon(monkeypatch)
    server = addon.BlenderMCPServer()
    _new_mesh_object(bpy, "R")

    result = server.model_radial_array(object_name="R", count=4, axis="Z", apply=False)

    assert result["applied"] is False
    empty = bpy.data.objects.get("R_radial_pivot")
    assert empty is not None
    assert empty.rotation_euler.z == pytest.approx(2 * math.pi / 4)
    obj = bpy.data.objects.get("R")
    array_mod = obj.modifiers.get("Array")
    assert array_mod is not None


def test_model_radial_array_cleans_up_helper_empty_when_applied(monkeypatch):
    addon, bpy = _load_addon(monkeypatch)
    server = addon.BlenderMCPServer()
    _new_mesh_object(bpy, "R2")

    server.model_radial_array(object_name="R2", count=6, axis="Z", apply=True)

    assert bpy.data.objects.get("R2_radial_pivot") is None
