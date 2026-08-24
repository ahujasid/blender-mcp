"""Byte-size guards for trajectory rows.

The trajectory_steps_size_guard DB constraint caps four jsonb columns per row
(action 32768, observation 98304, state_before/state_after 393216 bytes).
The original leak: `selected` was the one snapshot list _fit_snapshot could
not shrink, so select-all in a scene big enough to need the 2000-object cap
pushed both state columns past their limit on every step. These tests pin the
selected cap and the byte-accurate pre-insert guard that backstops it.
"""

from __future__ import annotations

from blender_mcp.trajectory import (
    DB_FIELD_BYTE_CAPS,
    MAX_SNAPSHOT_SELECTED,
    SNAPSHOT_BYTE_BUDGET,
    _SNAPSHOT_VIA_EXECUTE_CODE,
    _enforce_db_size_guard,
    _fit_snapshot,
    _utf8_size,
)
from conftest import ROOT_ADDON


def _snapshot(num_objects: int = 0, num_selected: int = 0) -> dict:
    return {
        "name": "Scene",
        "object_count": num_objects,
        "objects_listed": num_objects,
        "objects_truncated": False,
        "selected": [f"Object.{i:05d}" for i in range(num_selected)],
        "objects": [
            {
                "name": f"Object.{i:05d}",
                "type": "MESH",
                "location": [1.0, 2.0, 3.0],
                "rotation": [0.0, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0],
                "visible": True,
                "materials": ["Material"],
            }
            for i in range(num_objects)
        ],
        "snapshot_source": "native",
    }


def test_fit_snapshot_caps_selected():
    fitted = _fit_snapshot(_snapshot(num_selected=20_000))
    assert len(fitted["selected"]) == MAX_SNAPSHOT_SELECTED
    assert fitted["selected_count"] == 20_000
    assert fitted["selected_truncated"] is True
    # Sorted, so before/after snapshots keep the same subset.
    assert fitted["selected"] == sorted(fitted["selected"])


def test_fit_snapshot_select_all_large_scene_fits_budget():
    fitted = _fit_snapshot(_snapshot(num_objects=2000, num_selected=20_000))
    assert _utf8_size(fitted) <= SNAPSHOT_BYTE_BUDGET


def test_fit_snapshot_leaves_small_snapshots_alone():
    snapshot = _snapshot(num_objects=3, num_selected=2)
    assert _fit_snapshot(snapshot) is snapshot


def test_guard_trims_oversized_state_fields():
    row = {
        "state_before": _snapshot(num_objects=2000, num_selected=50_000),
        "state_after": _snapshot(num_objects=2000, num_selected=50_000),
    }
    _enforce_db_size_guard(row)
    for field in ("state_before", "state_after"):
        assert _utf8_size(row[field]) <= DB_FIELD_BYTE_CAPS[field]
        assert "size_guard_dropped" not in row[field]


def test_guard_trims_observe_payload():
    # Character caps upstream miss multi-byte inflation: 40k CJK chars are
    # 120KB of UTF-8, past the 96KB observation column cap.
    row = {
        "observation": {
            "kind": "observe",
            "modalities": ["scene_info"],
            "agent_observations": [{"summary": "x" * 2000}] * 8,
            "payload": "あ" * 40_000,
        }
    }
    _enforce_db_size_guard(row)
    assert _utf8_size(row["observation"]) <= DB_FIELD_BYTE_CAPS["observation"]
    assert row["observation"]["kind"] == "observe"


def test_guard_trims_oversized_action_params():
    row = {
        "action": {
            "semantic": "GENERATE_3D",
            "tool_name": "generate_hyper3d_model_via_text",
            "params": {"text_prompt": "p" * 100_000},
            "raw_code": None,
        }
    }
    _enforce_db_size_guard(row)
    assert _utf8_size(row["action"]) <= DB_FIELD_BYTE_CAPS["action"]
    assert row["action"]["tool_name"] == "generate_hyper3d_model_via_text"


def test_guard_stubs_unshrinkable_field():
    row = {"state_before": {"name": "x" * 500_000, "snapshot_source": "native"}}
    _enforce_db_size_guard(row)
    assert row["state_before"]["size_guard_dropped"] is True
    assert row["state_before"]["original_bytes"] > 500_000
    assert row["state_before"]["snapshot_source"] == "native"
    assert _utf8_size(row["state_before"]) < 1000


def test_guard_ignores_rows_without_guarded_fields():
    row = {"feedback": "accept", "goal_text": "g" * 5000}
    before = dict(row)
    _enforce_db_size_guard(row)
    assert row == before


def test_fallback_snapshot_template_caps_selected():
    assert "__MAX_SELECTED__" not in _SNAPSHOT_VIA_EXECUTE_CODE
    assert f"selected_count > {MAX_SNAPSHOT_SELECTED}" in _SNAPSHOT_VIA_EXECUTE_CODE


def test_addon_snapshot_caps_selected():
    source = ROOT_ADDON.read_text()
    assert "MAX_SNAPSHOT_SELECTED = 200" in source
    assert "selected = sorted(selected)[:MAX_SNAPSHOT_SELECTED]" in source
