"""Checks for the Hunyuan3D LOCAL_API reachability probe.

get_hunyuan3d_status used to report "enabled and ready to use" whenever the
checkbox was ticked, because its only LOCAL_API guard was `if not api_url` -
unreachable code, since _get_hunyuan3d_api_url() falls back to
"http://localhost:8081" and the scene property defaults to the same string.
A ready status therefore told you nothing about whether a server existed.

addon.py imports bpy, so it cannot be imported here. The structural tests read
the source, and the behavioural tests lift the probe out of the AST and run it
in isolation against real sockets.
"""
import ast
import pathlib
import socket

ADDON = pathlib.Path(__file__).with_name("addon.py")
PROBE = "probe_hunyuan3d_local_api"


def _source():
    return ADDON.read_text()


def _load_probe():
    """Extract the probe from addon.py and exec it without importing bpy."""
    for node in ast.walk(ast.parse(_source())):
        if isinstance(node, ast.FunctionDef) and node.name == PROBE:
            node.decorator_list = []  # drop @staticmethod so it stays a plain function
            namespace = {"socket": socket, "urlparse": __import__(
                "urllib.parse", fromlist=["urlparse"]).urlparse}
            exec(compile(ast.Module(body=[node], type_ignores=[]),
                         "<probe>", "exec"), namespace)
            return namespace[PROBE]
    raise AssertionError(f"{PROBE} not found in addon.py")


# --- structural ------------------------------------------------------------

def test_addon_parses():
    ast.parse(_source())


def test_urlparse_is_imported():
    assert "from urllib.parse import urlparse" in _source(), \
        "the probe needs urlparse imported at module scope"


def test_probe_exists():
    assert f"def {PROBE}" in _source()


def test_local_api_branch_calls_the_probe():
    src = _source()
    assert f"self.{PROBE}(api_url)" in src, \
        "the LOCAL_API branch of get_hunyuan3d_status must probe reachability"


def test_probe_runs_before_the_ready_message():
    # Ordering matters: an unreachable server must short-circuit the success return.
    src = _source()
    assert src.index(f"self.{PROBE}(api_url)") < \
        src.index("Hunyuan3D integration is enabled and ready to use."), \
        "reachability must be checked before reporting ready"


# --- behavioural -----------------------------------------------------------

def test_refused_port_reports_a_reason():
    probe = _load_probe()
    # Bind then close, so the port is almost certainly free and refusing.
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    reason = probe(f"http://127.0.0.1:{port}", timeout=0.5)
    assert reason is not None, "a closed port must not look reachable"
    assert str(port) in reason, f"reason should name the port it tried: {reason!r}"


def test_listening_port_is_reachable():
    probe = _load_probe()
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]
        assert probe(f"http://127.0.0.1:{port}", timeout=0.5) is None, \
            "a listening socket must report reachable"


def test_bare_host_port_without_scheme():
    probe = _load_probe()
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]
        assert probe(f"127.0.0.1:{port}", timeout=0.5) is None, \
            "a scheme-less API URL should still be probed, not rejected"


def test_garbage_url_returns_reason_instead_of_raising():
    probe = _load_probe()
    for bad in ("", "http://", "not a url"):
        assert isinstance(probe(bad, timeout=0.5), str), \
            f"{bad!r} should yield a reason string, not raise"


def test_https_url_defaults_to_443():
    probe = _load_probe()
    # No port given: scheme must pick 443, so the reason names that port.
    reason = probe("https://127.0.0.1", timeout=0.5)
    assert reason is not None and "443" in reason, \
        f"https with no explicit port should try 443: {reason!r}"
