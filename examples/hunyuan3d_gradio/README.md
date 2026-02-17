# Hunyuan3D Gradio Remote Test Suite

This folder contains lightweight smoke-test scripts for a remote Hunyuan3D Gradio service.

<details>
<summary><strong>Table of Contents (Click to Expand)</strong></summary>

- [Why Gradio Remote Instead of Paid API Credits](#why-gradio-remote-instead-of-paid-api-credits)
- [Files](#files)
- [Default Test Profile (Low-Cost)](#default-test-profile-low-cost)
- [Prerequisites](#prerequisites)
- [Run](#run)
- [Optional Environment Variables](#optional-environment-variables)
- [About Script 05](#about-script-05)
- [Functional Test Report (Merged)](#functional-test-report-merged)
  - [Scope](#report-scope)
  - [Test Setup](#report-test-setup)
  - [1) 01_test_lambda.py](#report-test-01)
  - [2) 02_test_shape_generation.py](#report-test-02)
  - [3) 03_test_generation_all.py](#report-test-03)
  - [4) 04_test_modes.py](#report-test-04)
  - [5) 05_test_export_click.py](#report-test-05)
  - [Overall Conclusion](#report-overall-conclusion)
  - [Recommendations](#report-recommendations)

</details>

## Why Gradio Remote Instead of Paid API Credits

For prompt-driven development and repeated validation, running against a remote Gradio server is more cost-effective than paid API credits.

- Paid API call: minimum `15 credits = 1.5 RMB` per call
- Self-hosted server billing:
  - Compute: `3.3 RMB/hour`
  - Stops billing when instance is shut down/destroyed
  - Disk: minimum 160GB, extra `0.02 RMB/hour`

In practice, for iterative testing (many trial runs), server-hour billing is usually cheaper.

## Files

- `api_common.py`: shared endpoint and input path config
- `01_test_lambda.py`: checks helper endpoints (`/lambda`, `/lambda_2`, `/lambda_3`, `/lambda_4`)
- `02_test_shape_generation.py`: checks `/shape_generation`
- `03_test_generation_all.py`: checks `/generation_all`
- `04_test_modes.py`: checks mode-switch endpoints
- `05_test_export_click.py`: checks `/on_export_click` (post-processing/export utility)
- `run_all.py`: runs all scripts in order

## Default Test Profile (Low-Cost)

- `steps=10`
- `octree_resolution=64`
- `num_chunks=2000`

This is intentionally tuned for smoke tests, not quality benchmarking.

## Prerequisites

```bash
pip install gradio_client
```

## Run

```bash
cd examples/hunyuan3d_gradio
python run_all.py
```

## Optional Environment Variables

- `HUNYUAN_GRADIO_URL`: override default Gradio endpoint
- `HUNYUAN_TEST_GLB`: input mesh path for `05_test_export_click.py`

Example:

```bash
export HUNYUAN_GRADIO_URL="http://0.0.0.0:6889/"
export HUNYUAN_TEST_GLB="/path/to/white_mesh.glb"
python 05_test_export_click.py
```

> Cloud Service link
<https://buy.cloud.tencent.com/hai>
After launch the gradio server, filling the HUNYUAN_GRADIO_URL.

## About Script 05

`05_test_export_click.py` is useful to verify export workflow behavior, but it is less important than scripts `02` and `03` for core generation capability validation.

## Functional Test Report (Merged)

<a id="report-scope"></a>
### Scope

The test scripts were executed in this order:

1. `01_test_lambda.py`
2. `02_test_shape_generation.py`
3. `03_test_generation_all.py`
4. `04_test_modes.py`
5. `05_test_export_click.py`

<a id="report-test-setup"></a>
### Test Setup

- Client: `gradio_client.Client`
- Default input image: `whitewolf.png`
- Low-cost test settings for generation endpoints:
  - `steps=10`
  - `octree_resolution=64`
  - `num_chunks=2000`
  - Other values kept close to endpoint defaults

<a id="report-test-01"></a>
### 1) `01_test_lambda.py`

#### Purpose

Validate lightweight control/helper endpoints:

- `/lambda`
- `/lambda_2`
- `/lambda_3`
- `/lambda_4`

#### Inputs

- `/lambda`: no parameters
- `/lambda_2`: no parameters
- `/lambda_3`: no parameters
- `/lambda_4`: no parameters

#### Expected Output Types (from API tutorial)

- `/lambda`: 1 element
- `/lambda_2`: 1 element
- `/lambda_3`: tuple of 3 elements
- `/lambda_4`: 1 element

#### Observed Output

- `/lambda` -> `()`
- `/lambda_2` -> `()`
- `/lambda_3` -> `({'visible': True, 'value': True, '__type__': 'update'}, {'interactive': False, '__type__': 'update'}, {'interactive': False, '__type__': 'update'})`
- `/lambda_4` -> `()`

#### Notes

- `/lambda_3` returned meaningful UI update payloads.
- The empty tuples from `/lambda`, `/lambda_2`, and `/lambda_4` are acceptable for internal UI callbacks, but they have limited direct value for backend automation.

<a id="report-test-02"></a>
### 2) `02_test_shape_generation.py`

#### Purpose

Validate single-stage mesh generation via `/shape_generation` using a single image input.

#### Input Parameters

- `image=handle_file("whitewolf.png")`
- `mv_image_front=None`
- `mv_image_back=None`
- `mv_image_left=None`
- `mv_image_right=None`
- `steps=10`
- `guidance_scale=5`
- `seed=1234`
- `octree_resolution=64`
- `check_box_rembg=True`
- `num_chunks=2000`
- `randomize_seed=False`
- `api_name="/shape_generation"`

#### Expected Output Signature

Tuple of 4 elements:

1. generated file path
2. HTML preview
3. mesh stats JSON
4. seed

#### Observed Output

- `file_out`: `/tmp/gradio/.../white_mesh.glb`
- `mesh_stats` highlights:
  - faces: `20342`
  - vertices: `10231`
  - time:
    - remove background: `~0.188s`
    - shape generation: `~33.41s`
    - total: `~34.94s`
- `seed_out`: `1234`
- `html_out`: valid iframe preview snippet

#### Result

Pass. Endpoint produced a valid mesh and structured metadata under low-cost settings.

<a id="report-test-03"></a>
### 3) `03_test_generation_all.py`

#### Purpose

Validate full pipeline (`/generation_all`) including shape + texture and export artifacts.

#### Input Parameters

- Same image/multi-view fields as test #2
- `steps=10`
- `guidance_scale=5`
- `seed=1234`
- `octree_resolution=64`
- `check_box_rembg=True`
- `num_chunks=2000`
- `randomize_seed=False`
- `api_name="/generation_all"`

#### Expected Output Signature

Tuple of 5 elements:

1. first file path
2. second file path
3. HTML preview
4. mesh stats JSON
5. seed

#### Observed Output

- `file_out_1`: `/tmp/gradio/.../white_mesh.obj`
- `file_out_2`: `/tmp/gradio/.../textured_mesh.glb`
- `mesh_stats` highlights:
  - faces: `20342`
  - vertices: `10231`
  - time:
    - shape generation: `~7.27s`
    - texture generation: `~56.30s`
    - OBJ->GLB conversion: `~1.31s`
    - total: `~66.41s`
- `seed_out`: `1234`
- `html_out`: valid iframe preview snippet

#### Result

Pass. Full generation with texture succeeded and returned expected artifacts.

<a id="report-test-04"></a>
### 4) `04_test_modes.py`

#### Purpose

Validate mode-control endpoints used to update default generation/decode behavior.

#### Input Parameters

- `/on_gen_mode_change`: `value="Turbo"` (allowed: `Turbo/Fast/Standard`)
- `/on_decode_mode_change`: `value="High"` (allowed: `Low/Standard/High`)

#### Expected Output Types

- Both endpoints return one numeric update value.

#### Observed Output

- `/on_gen_mode_change` -> `{'value': 5, '__type__': 'update'}`
- `/on_decode_mode_change` -> `{'value': 196, '__type__': 'update'}`

#### Result

Pass. Mode controls responded with valid update payloads and plausible numeric values.

<a id="report-test-05"></a>
### 5) `05_test_export_click.py`

#### Purpose

Validate export endpoint `/on_export_click` using an existing local GLB (`white_mesh.glb`).

#### Input Parameters

- `file_out=handle_file("white_mesh.glb")`
- `file_out2=handle_file("white_mesh.glb")`
- `file_type="glb"` (allowed: `glb/obj/ply/stl`)
- `reduce_face=True`
- `export_texture=False`
- `target_face_num=5000`
- `api_name="/on_export_click"`

#### Expected Output Signature

Tuple of 2 elements:

1. HTML output
2. downloadable file path

#### Observed Output

- `download_file`: `/tmp/gradio/.../white_mesh.glb`
- `html_out`: valid iframe preview snippet

#### Result

Pass. Endpoint returned export artifacts as expected.

#### Practical Value Note

This endpoint is less important than `/shape_generation` and `/generation_all` for core capability validation. It mainly verifies post-processing/export behavior for existing files rather than generation quality itself.

<a id="report-overall-conclusion"></a>
### Overall Conclusion

The tested Gradio endpoints are functional under low-cost settings.

- Core generation endpoints (`/shape_generation`, `/generation_all`) passed and returned valid artifacts plus metadata.
- Control endpoints (`/on_gen_mode_change`, `/on_decode_mode_change`) responded correctly.
- Export endpoint (`/on_export_click`) works as a post-processing utility, but is secondary for core model validation.

<a id="report-recommendations"></a>
### Recommendations

1. Keep this low-cost profile (`steps=10`, `octree_resolution=64`, `num_chunks=2000`) for smoke tests and CI-like checks.
2. Add one medium-quality profile (e.g., `steps=20`, higher octree/chunks) for periodic quality regression checks.
3. For production-facing validation, prioritize success/failure criteria on `/shape_generation` and `/generation_all` before UI helper endpoints.
