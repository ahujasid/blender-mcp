import math

import pytest

from blender_mcp.stress_engine import EXAMPLES, build_example, run_example


@pytest.mark.parametrize("example", list(EXAMPLES))
def test_every_example_solves_with_small_equilibrium_residual(example):
    result = run_example(example)

    assert result["model"]["node_count"] >= 12
    assert result["model"]["element_count"] >= result["model"]["node_count"]
    assert result["metrics"]["equilibrium_residual"] < 1e-8
    assert math.isfinite(result["metrics"]["max_displacement_m"])
    assert math.isfinite(result["metrics"]["max_abs_stress_pa"])
    assert result["quality"]["status"] == "screening_only"


def test_mechanical_solution_scales_linearly_with_load():
    baseline = run_example("cantilever_beam", load_scale=1.0)
    doubled = run_example("cantilever_beam", load_scale=2.0)

    assert doubled["metrics"]["max_displacement_m"] == pytest.approx(
        2 * baseline["metrics"]["max_displacement_m"], rel=1e-10
    )
    assert doubled["metrics"]["max_abs_stress_pa"] == pytest.approx(
        2 * baseline["metrics"]["max_abs_stress_pa"], rel=1e-10
    )


def test_area_scale_changes_stiffness_stress_and_mass_consistently():
    baseline = run_example("cantilever_beam", area_scale=1.0)
    doubled = run_example("cantilever_beam", area_scale=2.0)

    assert doubled["metrics"]["max_displacement_m"] == pytest.approx(
        0.5 * baseline["metrics"]["max_displacement_m"], rel=1e-10
    )
    assert doubled["metrics"]["max_abs_stress_pa"] == pytest.approx(
        0.5 * baseline["metrics"]["max_abs_stress_pa"], rel=1e-10
    )
    assert doubled["metrics"]["mass_kg"] == pytest.approx(
        2 * baseline["metrics"]["mass_kg"], rel=1e-12
    )


def test_thermal_warpage_has_temperature_and_no_mechanical_resultant():
    result = run_example("chip_package_warpage")

    assert result["model"]["delta_temperature_c"] == -125.0
    assert result["metrics"]["max_displacement_m"] > 0
    assert result["metrics"]["external_resultant_n"] == pytest.approx([0.0, 0.0, 0.0])


def test_invalid_example_and_material_are_rejected():
    with pytest.raises(ValueError, match="Unknown example"):
        build_example("not_a_model")
    with pytest.raises(ValueError, match="Unknown material"):
        run_example("cantilever_beam", material_override="unobtainium")

