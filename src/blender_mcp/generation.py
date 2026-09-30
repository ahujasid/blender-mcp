"""One generate/poll/import flow across Tripo, Hunyuan3D and Hyper3D Rodin.

Each provider used to be three or four tools with different id shapes. Here a
generation is a single call: submit, poll until done or out of time, import.
If time runs out the caller gets a job handle ("<provider>:<kind>:<id>") and
passes it back to resume, so no client timeout ever strands a paid generation.

The addon still does the provider work (and the Premium routing), through the
commands it has always had, so this needs no addon update.
"""

import asyncio
import base64
import logging
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable
from urllib.parse import urlparse

logger = logging.getLogger("BlenderMCPServer")

PROVIDERS = ("tripo", "hunyuan3d", "hyper3d")

# Auto-pick order. Premium generators come first because the user is paying
# for them and they run the stronger models; among those Tripo is Premium-only.
PREMIUM_ORDER = ("tripo", "hunyuan3d", "hyper3d")
OWN_KEY_ORDER = ("hunyuan3d", "hyper3d")

POLL_INTERVAL_S = 5.0

TRIPO_UNAVAILABLE = ("Tripo is only available with MCP for Blender Premium. If Premium is on, update the Blender "
                     "addon: run `uvx mcp-for-blender install-addon`, then restart Blender.")

Send = Callable[[str, dict], Any]
Progress = Callable[[float, float], Awaitable[None]]


class GenerationError(Exception):
    """A failure to relay to the user as written, without retrying."""


@dataclass
class Job:
    provider: str
    kind: str   # tripo: "rid"; hyper3d: "fal" | "main"; hunyuan3d: "job"
    ident: str  # request id, job id, or "<task_uuid>|<subscription_key>"
    name: str

    @property
    def handle(self) -> str:
        return f"{self.provider}:{self.kind}:{self.ident}"

    @classmethod
    def parse(cls, handle: str, name: str) -> "Job":
        provider, kind, ident = (handle.split(":", 2) + ["", ""])[:3]
        if provider not in PROVIDERS or not kind or not ident:
            raise GenerationError(f"Not a generation job handle: {handle!r}")
        return cls(provider, kind, ident, name)


def _relay(result: Any) -> None:
    """Raise with the provider's own words if the reply is a failure."""
    if not isinstance(result, dict):
        if isinstance(result, str) and result.lower().startswith("error"):
            raise GenerationError(result)
        return
    if result.get("code"):
        raise GenerationError(f"{result.get('message') or result['code']} (code {result['code']}; "
                              "tell the user as written and don't retry automatically)")
    if result.get("error"):
        raise GenerationError(str(result["error"]))


def default_name(prompt: str | None) -> str:
    words = re.findall(r"[A-Za-z0-9]+", prompt or "")[:3]
    return "".join(w.capitalize() for w in words) or "Generated"


def choose_provider(requested: str, premium: list[str], own_key_enabled: dict[str, bool]) -> tuple[str, bool]:
    """(provider, is_premium) for a request. `requested` is a provider or "auto"."""
    requested = (requested or "auto").lower()
    if requested != "auto":
        if requested not in PROVIDERS:
            raise GenerationError(f"Unknown provider {requested!r}. Use one of: auto, {', '.join(PROVIDERS)}")
        if premium:
            if requested not in premium:
                raise GenerationError(f"{requested} is not switched on in MCP for Blender Premium. "
                                      f"On: {', '.join(premium)}. Tick it in the Blender sidebar.")
            return requested, True
        if requested == "tripo":
            # Also what an addon from before Premium looks like, so say how to update.
            raise GenerationError(TRIPO_UNAVAILABLE)
        if not own_key_enabled.get(requested):
            raise GenerationError(f"{requested} is not enabled. Turn it on and add an API key in the "
                                  "MCP for Blender sidebar in Blender (press N in the 3D Viewport).")
        return requested, False
    for name in PREMIUM_ORDER:
        if name in premium:
            return name, True
    for name in OWN_KEY_ORDER:
        if own_key_enabled.get(name):
            return name, False
    raise GenerationError(
        "No 3D generator is enabled. In Blender's MCP for Blender sidebar, turn on Hunyuan3D or Hyper3D "
        "Rodin with an API key, or use MCP for Blender Premium (no keys needed): "
        "https://mcp-for-blender.com/premium"
    )


def _rodin_images(image: str) -> list:
    if urlparse(image).scheme in ("http", "https"):
        return [image]
    if not os.path.exists(image):
        raise GenerationError(f"Image not found: {image}. Give an absolute file path or an http(s) URL.")
    with open(image, "rb") as f:
        return [(Path(image).suffix, base64.b64encode(f.read()).decode("ascii"))]


def process_bbox(bbox: list | None) -> list[int] | None:
    if bbox is None:
        return None
    if len(bbox) != 3 or any(v <= 0 for v in bbox):
        raise GenerationError("bbox_condition must be three positive numbers [length, width, height]")
    if all(isinstance(v, int) for v in bbox):
        return list(bbox)
    return [int(float(v) / max(bbox) * 100) for v in bbox]


def submit(send: Send, provider: str, name: str, prompt: str | None, image: str | None,
           quality: str | None, bbox_condition: list | None, supports_quality: bool) -> Job | str:
    """Start a generation. Returns a Job, or a finished message for providers
    that generate synchronously (Hunyuan3D LOCAL_API)."""
    if provider == "tripo":
        params = {"text_prompt": prompt, "image": image}
        if quality:
            params["quality"] = quality
        result = send("create_tripo_job", params)
        _relay(result)
        if not result.get("request_id"):
            raise GenerationError(f"Tripo returned no request id: {result}")
        return Job("tripo", "rid", result["request_id"], name)

    if provider == "hunyuan3d":
        params = {"text_prompt": prompt, "image": image}
        if quality and supports_quality:
            params["quality"] = quality
        result = send("create_hunyuan_job", params)
        _relay(result)
        response = result.get("Response", {}) if isinstance(result, dict) else {}
        if response.get("Error"):
            raise GenerationError(str(response["Error"].get("Message") or response["Error"]))
        if "JobId" in response:
            return Job("hunyuan3d", "job", f"job_{response['JobId']}", name)
        if isinstance(result, dict) and result.get("status") == "DONE":
            return "Generated and imported by the local Hunyuan3D server. Find it with get_scene_info."
        raise GenerationError(f"Hunyuan3D returned no job: {result}")

    images = _rodin_images(image) if image else None
    result = send("create_rodin_job", {
        "text_prompt": prompt if not image else None,
        "images": images,
        "bbox_condition": process_bbox(bbox_condition),
    })
    _relay(result)
    if result.get("submit_time") and result.get("uuid"):
        return Job("hyper3d", "main", f"{result['uuid']}|{result['jobs']['subscription_key']}", name)
    if result.get("request_id"):
        return Job("hyper3d", "fal", result["request_id"], name)
    raise GenerationError(f"Hyper3D returned no job: {result}")


def poll(send: Send, job: Job) -> tuple[str, Any]:
    """("running" | "done" | "failed", detail) for one status check."""
    if job.provider == "tripo" or (job.provider == "hyper3d" and job.kind == "fal"):
        command = "poll_tripo_job_status" if job.provider == "tripo" else "poll_rodin_job_status"
        result = send(command, {"request_id": job.ident})
        _relay(result)
        status = str(result.get("status", "")).upper()
        if status == "COMPLETED":
            return "done", None
        if status in ("IN_QUEUE", "IN_PROGRESS", ""):
            return "running", status or "IN_QUEUE"
        return "failed", result.get("error") or status

    if job.provider == "hyper3d":
        result = send("poll_rodin_job_status", {"subscription_key": job.ident.split("|", 1)[1]})
        _relay(result)
        statuses = result.get("status_list") or []
        if statuses and all(s == "Done" for s in statuses):
            return "done", None
        if any(s in ("Failed", "Canceled") for s in statuses):
            return "failed", ", ".join(statuses)
        return "running", ", ".join(statuses) or "Waiting"

    result = send("poll_hunyuan_job_status", {"job_id": job.ident})
    _relay(result)
    response = result.get("Response", {}) if isinstance(result, dict) else {}
    status = response.get("Status", "")
    if status == "DONE":
        files = response.get("ResultFile3Ds") or []
        glb = next((f.get("Url") for f in files if str(f.get("Type", "")).upper() == "GLB"), None)
        url = glb or next((f.get("Url") for f in files if f.get("Url")), None)
        if not url:
            return "failed", "finished without a model file"
        return "done", url
    if status == "FAIL" or response.get("Error"):
        return "failed", response.get("ErrorMessage") or response.get("Error") or "generation failed"
    return "running", status or "WAIT"


def import_result(send: Send, job: Job, detail: Any) -> Any:
    if job.provider == "tripo":
        result = send("import_generated_asset_tripo", {"request_id": job.ident, "name": job.name})
    elif job.provider == "hyper3d" and job.kind == "fal":
        result = send("import_generated_asset", {"request_id": job.ident, "name": job.name})
    elif job.provider == "hyper3d":
        result = send("import_generated_asset", {"task_uuid": job.ident.split("|", 1)[0], "name": job.name})
    else:
        result = send("import_generated_asset_hunyuan", {"name": job.name, "zip_file_url": detail})
    _relay(result)
    if isinstance(result, dict) and result.get("succeed") is False:
        raise GenerationError(result.get("error") or result.get("message") or "Import failed")
    return result


async def wait_and_import(send: Send, job: Job, wait_seconds: float,
                          progress: Progress | None = None,
                          sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
                          clock: Callable[[], float] = time.monotonic) -> tuple[bool, str]:
    """Poll until done or `wait_seconds` pass. (imported, message)."""
    start = clock()
    while True:
        state, detail = poll(send, job)
        if state == "done":
            import_result(send, job, detail)
            return True, job.name
        if state == "failed":
            raise GenerationError(f"Generation failed: {detail}. This attempt was not imported.")
        elapsed = clock() - start
        if elapsed + POLL_INTERVAL_S > wait_seconds:
            return False, str(detail)
        if progress:
            try:
                await progress(elapsed, wait_seconds)
            except Exception:
                pass
        await sleep(POLL_INTERVAL_S)
