"""generate_3d drives every provider through one submit/poll/import flow.

A fake addon replays each provider's real reply shapes, so these pin the
shapes the flow depends on: Premium and fal request ids, Rodin main-site
subscription keys, and Tencent-style Hunyuan responses.
"""

import asyncio

import pytest

from blender_mcp import generation
from blender_mcp.generation import GenerationError, Job, choose_provider


class FakeAddon:
    def __init__(self, replies):
        # command -> reply, or a list of replies consumed in order
        self.replies = replies
        self.calls = []

    def __call__(self, command, params):
        self.calls.append((command, params))
        reply = self.replies[command]
        if isinstance(reply, list):
            return reply.pop(0) if len(reply) > 1 else reply[0]
        return reply


def _run(send, job, wait=100):
    async def no_sleep(_):
        pass

    ticks = iter(range(0, 10_000, 5))
    return asyncio.run(generation.wait_and_import(send, job, wait, sleep=no_sleep, clock=lambda: next(ticks)))


# -------------------------------------------------------------- provider choice

def test_auto_prefers_premium_generators():
    assert choose_provider("auto", ["hyper3d", "tripo"], {}) == ("tripo", True)
    assert choose_provider("auto", ["hunyuan3d"], {"hyper3d": True}) == ("hunyuan3d", True)


def test_auto_falls_back_to_own_keys():
    assert choose_provider("auto", [], {"hunyuan3d": False, "hyper3d": True}) == ("hyper3d", False)


def test_nothing_enabled_points_at_setup():
    with pytest.raises(GenerationError, match="No 3D generator"):
        choose_provider("auto", [], {"hunyuan3d": False, "hyper3d": False})


def test_tripo_needs_premium():
    with pytest.raises(GenerationError, match="Premium"):
        choose_provider("tripo", [], {"hunyuan3d": True})


def test_explicit_provider_must_be_on_in_premium():
    with pytest.raises(GenerationError, match="not switched on"):
        choose_provider("hyper3d", ["tripo"], {})


# ------------------------------------------------------------------ flows

def test_tripo_submit_poll_import():
    send = FakeAddon({
        "create_tripo_job": {"request_id": "r1", "status": "IN_QUEUE"},
        "poll_tripo_job_status": [{"status": "IN_PROGRESS"}, {"status": "COMPLETED"}],
        "import_generated_asset_tripo": {"succeed": True},
    })
    job = generation.submit(send, "tripo", "Chest", "a chest", None, "high", None, True)
    assert job.handle == "tripo:rid:r1"
    assert send.calls[0] == ("create_tripo_job", {"text_prompt": "a chest", "image": None, "quality": "high"})
    assert _run(send, job) == (True, "Chest")
    assert send.calls[-1] == ("import_generated_asset_tripo", {"request_id": "r1", "name": "Chest"})


def test_premium_error_codes_are_relayed_not_retried():
    send = FakeAddon({"create_tripo_job": {"code": "QUOTA_EXHAUSTED", "message": "You've used all generations."}})
    with pytest.raises(GenerationError, match="used all generations.*don't retry"):
        generation.submit(send, "tripo", "X", "x", None, None, None, True)


def test_hunyuan_polls_tencent_shapes_and_imports_the_glb():
    send = FakeAddon({
        "create_hunyuan_job": {"Response": {"JobId": "42"}},
        "poll_hunyuan_job_status": [
            {"Response": {"Status": "RUN"}},
            {"Response": {"Status": "DONE", "ResultFile3Ds": [
                {"Type": "OBJ", "Url": "https://x/model.zip"}, {"Type": "GLB", "Url": "https://x/model.glb"}]}},
        ],
        "import_generated_asset_hunyuan": {"succeed": True},
    })
    job = generation.submit(send, "hunyuan3d", "Lamp", "a lamp", None, "high", None, supports_quality=False)
    assert job.handle == "hunyuan3d:job:job_42"
    assert "quality" not in send.calls[0][1]  # older addons reject unknown arguments
    assert _run(send, job) == (True, "Lamp")
    assert send.calls[-1] == ("import_generated_asset_hunyuan", {"name": "Lamp", "zip_file_url": "https://x/model.glb"})


def test_hunyuan_failure_says_why():
    send = FakeAddon({"poll_hunyuan_job_status": {"Response": {"Status": "FAIL", "ErrorMessage": "bad prompt"}}})
    with pytest.raises(GenerationError, match="bad prompt"):
        _run(send, Job("hunyuan3d", "job", "job_1", "X"))


def test_rodin_main_site_uses_subscription_key_then_task_uuid():
    send = FakeAddon({
        "create_rodin_job": {"submit_time": True, "uuid": "u1", "jobs": {"subscription_key": "s1"}},
        "poll_rodin_job_status": [{"status_list": ["Done", "Generating"]}, {"status_list": ["Done", "Done"]}],
        "import_generated_asset": {"succeed": True},
    })
    job = generation.submit(send, "hyper3d", "Car", "a car", None, None, [2.0, 1.0, 1.0], True)
    assert job.handle == "hyper3d:main:u1|s1"
    assert send.calls[0][1]["bbox_condition"] == [100, 50, 50]
    assert _run(send, job) == (True, "Car")
    assert ("poll_rodin_job_status", {"subscription_key": "s1"}) in send.calls
    assert send.calls[-1] == ("import_generated_asset", {"task_uuid": "u1", "name": "Car"})


def test_rodin_fal_and_premium_use_request_id():
    send = FakeAddon({
        "create_rodin_job": {"request_id": "q1"},
        "poll_rodin_job_status": {"status": "COMPLETED"},
        "import_generated_asset": {"succeed": True},
    })
    job = generation.submit(send, "hyper3d", "Car", None, "https://img/car.png", None, None, True)
    assert send.calls[0][1]["images"] == ["https://img/car.png"]
    assert send.calls[0][1]["text_prompt"] is None
    assert _run(send, job) == (True, "Car")
    assert send.calls[-1] == ("import_generated_asset", {"request_id": "q1", "name": "Car"})


def test_running_out_of_time_returns_a_resumable_handle():
    send = FakeAddon({"poll_tripo_job_status": {"status": "IN_PROGRESS"}})
    job = Job("tripo", "rid", "r9", "Robot")
    imported, detail = _run(send, job, wait=20)
    assert not imported and detail == "IN_PROGRESS"
    assert Job.parse(job.handle, "Robot") == job


def test_failed_import_is_an_error():
    send = FakeAddon({
        "poll_tripo_job_status": {"status": "COMPLETED"},
        "import_generated_asset_tripo": {"succeed": False, "error": "download failed"},
    })
    with pytest.raises(GenerationError, match="download failed"):
        _run(send, Job("tripo", "rid", "r1", "X"))


def test_bad_handles_are_rejected():
    for handle in ("", "tripo", "meshy:rid:1", "tripo:rid:"):
        with pytest.raises(GenerationError):
            Job.parse(handle, "X")


def test_default_name_comes_from_the_prompt():
    assert generation.default_name("a weathered wooden treasure chest") == "AWeatheredWooden"
    assert generation.default_name(None) == "Generated"
