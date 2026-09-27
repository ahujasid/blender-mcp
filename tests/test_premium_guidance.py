"""Premium steers the agent toward generation over the model libraries."""
import types

from blender_mcp import server
from blender_mcp.premium_hint import premium_generation_guidance
from test_sketchfab_status import _load_addon


def test_no_guidance_without_premium_generators():
    assert premium_generation_guidance([]) == ""
    assert premium_generation_guidance(None) == ""
    assert premium_generation_guidance(["unknown"]) == ""


def test_guidance_names_only_the_enabled_generators():
    text = premium_generation_guidance(["tripo", "hunyuan3d"])
    assert "generate_tripo_model" in text
    assert "generate_hunyuan3d_model" in text
    assert "hyper3d" not in text.lower()


class _Blender:
    def __init__(self, reply):
        self.reply = reply

    def send_command(self, cmd, params=None):
        assert cmd == "get_addon_info"
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


def test_library_status_guidance_reads_the_addon():
    assert "generate_tripo_model" in server._premium_guidance(_Blender({"premium_generators": ["tripo"]}))
    # Older addons don't send the field; a failed lookup must not break the status reply.
    assert server._premium_guidance(_Blender({"protocol_version": 11})) == ""
    assert server._premium_guidance(_Blender(ConnectionError("gone"))) == ""


def _scene(**enabled):
    return types.SimpleNamespace(
        blendermcp_use_hyper3d=enabled.get("hyper3d", False),
        blendermcp_use_hunyuan3d=enabled.get("hunyuan3d", False),
        blendermcp_use_tripo=enabled.get("tripo", False),
    )


def test_addon_reports_enabled_generators_only_in_premium(monkeypatch):
    addon = _load_addon(monkeypatch, _scene(tripo=True, hyper3d=True))
    monkeypatch.setattr(addon, "premium_active", lambda: False)
    assert addon.premium_enabled_generators() == []
    monkeypatch.setattr(addon, "premium_active", lambda: True)
    assert addon.premium_enabled_generators() == ["hyper3d", "tripo"]


def test_library_status_skips_addons_without_get_addon_info(monkeypatch):
    old = types.SimpleNamespace(source="missing")
    monkeypatch.setattr(server, "_addon_handshake", old)

    class _Unreachable:
        def send_command(self, *a, **k):
            raise AssertionError("must not query an addon that lacks get_addon_info")

    assert server._premium_guidance(_Unreachable()) == ""
