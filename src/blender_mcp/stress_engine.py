"""Small, deterministic 3D truss/FEM engine used by BlenderMCP.

The engine intentionally focuses on transparent linear-elastic axial members.
It is useful for concept screening, education, load-path studies, and creating
high-quality Blender visualisations.  It is not a replacement for a validated
solid/shell solver or a licensed structural engineer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable

import numpy as np


@dataclass(frozen=True)
class Material:
    name: str
    label: str
    young_modulus: float
    yield_strength: float
    density: float
    poisson_ratio: float
    thermal_expansion: float


MATERIALS: dict[str, Material] = {
    "structural_steel": Material("structural_steel", "Structural steel", 200e9, 250e6, 7850, 0.30, 12.0e-6),
    "aluminum_6061": Material("aluminum_6061", "Aluminium 6061-T6", 69e9, 276e6, 2700, 0.33, 23.6e-6),
    "titanium_ti6al4v": Material("titanium_ti6al4v", "Ti-6Al-4V", 114e9, 880e6, 4430, 0.34, 8.6e-6),
    "copper": Material("copper", "Copper (annealed)", 110e9, 70e6, 8960, 0.34, 16.5e-6),
    "silicon": Material("silicon", "Silicon, isotropic screening value", 130e9, 7.0e9, 2330, 0.28, 2.6e-6),
    "polyimide": Material("polyimide", "Polyimide film", 2.5e9, 120e6, 1420, 0.34, 20e-6),
    "polycarbonate": Material("polycarbonate", "Polycarbonate", 2.3e9, 65e6, 1200, 0.37, 65e-6),
    "fr4": Material("fr4", "FR-4, isotropic screening value", 22e9, 310e6, 1850, 0.13, 14e-6),
    "carbon_fiber_quasi_iso": Material("carbon_fiber_quasi_iso", "CFRP, quasi-isotropic screening value", 70e9, 600e6, 1600, 0.30, 2e-6),
}


@dataclass(frozen=True)
class Element:
    node_i: int
    node_j: int
    area: float
    material: str
    modulus_factor: float = 1.0
    alpha_factor: float = 1.0


@dataclass
class StressModel:
    name: str
    title: str
    category: str
    description: str
    nodes: np.ndarray
    elements: list[Element]
    loads: np.ndarray
    fixed_dofs: set[int]
    faces: list[list[int]] = field(default_factory=list)
    delta_temperature: float = 0.0
    assumptions: list[str] = field(default_factory=list)
    parameters: dict[str, float | str] = field(default_factory=dict)


class ModelBuilder:
    def __init__(self, name: str, title: str, category: str, description: str):
        self.name = name
        self.title = title
        self.category = category
        self.description = description
        self.nodes: list[tuple[float, float, float]] = []
        self.elements: list[Element] = []
        self._element_keys: set[tuple[int, int, str]] = set()
        self._loads: dict[int, np.ndarray] = {}
        self.fixed_dofs: set[int] = set()
        self.faces: list[list[int]] = []
        self.delta_temperature = 0.0
        self.assumptions = [
            "small displacement and linear elasticity",
            "pin-jointed axial members; bending and local contact are not resolved",
            "nominal material properties; validate against test coupons and a qualified solver",
        ]
        self.parameters: dict[str, float | str] = {}

    def node(self, xyz: Iterable[float]) -> int:
        values = tuple(float(v) for v in xyz)
        if len(values) != 3:
            raise ValueError("A node requires x, y, z coordinates")
        self.nodes.append(values)
        return len(self.nodes) - 1

    def element(
        self,
        node_i: int,
        node_j: int,
        area: float,
        material: str,
        *,
        modulus_factor: float = 1.0,
        alpha_factor: float = 1.0,
    ) -> None:
        if node_i == node_j:
            return
        if area <= 0:
            raise ValueError("Element area must be positive")
        key = (min(node_i, node_j), max(node_i, node_j), material)
        if key in self._element_keys:
            return
        self._element_keys.add(key)
        self.elements.append(Element(node_i, node_j, float(area), material, float(modulus_factor), float(alpha_factor)))

    def fix(self, node: int, axes: str = "xyz") -> None:
        for axis, offset in (("x", 0), ("y", 1), ("z", 2)):
            if axis in axes:
                self.fixed_dofs.add(node * 3 + offset)

    def load(self, node: int, vector: Iterable[float]) -> None:
        value = np.asarray(tuple(vector), dtype=float)
        if value.shape != (3,):
            raise ValueError("A nodal load requires Fx, Fy, Fz")
        self._loads[node] = self._loads.get(node, np.zeros(3)) + value

    def build(self) -> StressModel:
        nodes = np.asarray(self.nodes, dtype=float)
        loads = np.zeros_like(nodes)
        for node, value in self._loads.items():
            loads[node] += value
        return StressModel(
            name=self.name,
            title=self.title,
            category=self.category,
            description=self.description,
            nodes=nodes,
            elements=list(self.elements),
            loads=loads,
            fixed_dofs=set(self.fixed_dofs),
            faces=list(self.faces),
            delta_temperature=self.delta_temperature,
            assumptions=list(self.assumptions),
            parameters=dict(self.parameters),
        )


def _material(name: str) -> Material:
    try:
        return MATERIALS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown material '{name}'. Available: {', '.join(sorted(MATERIALS))}") from exc


def solve_model(
    model: StressModel,
    *,
    load_scale: float = 1.0,
    area_scale: float = 1.0,
    material_override: str | None = None,
) -> dict:
    """Solve a linear 3D truss model and return JSON-safe result data."""
    if not model.elements or len(model.nodes) < 2:
        raise ValueError("The model needs at least two nodes and one element")
    if not model.fixed_dofs:
        raise ValueError("The model has no constraints")
    if area_scale <= 0 or load_scale < 0:
        raise ValueError("area_scale must be positive and load_scale cannot be negative")
    if material_override:
        _material(material_override)

    node_count = len(model.nodes)
    dof_count = node_count * 3
    stiffness = np.zeros((dof_count, dof_count), dtype=float)
    thermal_load = np.zeros(dof_count, dtype=float)
    lengths = np.zeros(len(model.elements), dtype=float)
    directions = np.zeros((len(model.elements), 3), dtype=float)
    effective_materials: list[Material] = []
    effective_areas = np.zeros(len(model.elements), dtype=float)
    effective_moduli = np.zeros(len(model.elements), dtype=float)

    for index, element in enumerate(model.elements):
        material = _material(material_override or element.material)
        start = model.nodes[element.node_i]
        end = model.nodes[element.node_j]
        delta = end - start
        length = float(np.linalg.norm(delta))
        if length <= 1e-12:
            raise ValueError(f"Element {index} has zero length")
        direction = delta / length
        area = element.area * area_scale
        modulus = material.young_modulus * element.modulus_factor
        local = (area * modulus / length) * np.outer(direction, direction)
        dofs_i = np.arange(element.node_i * 3, element.node_i * 3 + 3)
        dofs_j = np.arange(element.node_j * 3, element.node_j * 3 + 3)
        stiffness[np.ix_(dofs_i, dofs_i)] += local
        stiffness[np.ix_(dofs_i, dofs_j)] -= local
        stiffness[np.ix_(dofs_j, dofs_i)] -= local
        stiffness[np.ix_(dofs_j, dofs_j)] += local

        initial_strain = material.thermal_expansion * element.alpha_factor * model.delta_temperature
        thermal_force = area * modulus * initial_strain * direction
        thermal_load[dofs_i] -= thermal_force
        thermal_load[dofs_j] += thermal_force
        lengths[index] = length
        directions[index] = direction
        effective_materials.append(material)
        effective_areas[index] = area
        effective_moduli[index] = modulus

    mechanical_load = (model.loads * float(load_scale)).reshape(-1)
    total_load = mechanical_load + thermal_load
    fixed = np.asarray(sorted(model.fixed_dofs), dtype=int)
    all_dofs = np.arange(dof_count)
    free = np.setdiff1d(all_dofs, fixed, assume_unique=True)
    if not len(free):
        raise ValueError("All degrees of freedom are constrained")
    reduced = stiffness[np.ix_(free, free)]
    rhs = total_load[free]
    condition_number = float(np.linalg.cond(reduced))
    if not np.isfinite(condition_number) or condition_number > 1e14:
        raise ValueError(
            "The stiffness matrix is singular or ill-conditioned. Add bracing/constraints "
            f"or inspect disconnected nodes (condition number={condition_number:.3e})."
        )
    displacement_vector = np.zeros(dof_count, dtype=float)
    displacement_vector[free] = np.linalg.solve(reduced, rhs)
    displacement = displacement_vector.reshape((-1, 3))

    stresses = np.zeros(len(model.elements), dtype=float)
    strains = np.zeros(len(model.elements), dtype=float)
    forces = np.zeros(len(model.elements), dtype=float)
    mass = 0.0
    node_stress_sum = np.zeros(node_count, dtype=float)
    node_stress_weight = np.zeros(node_count, dtype=float)
    for index, element in enumerate(model.elements):
        relative = displacement[element.node_j] - displacement[element.node_i]
        material = effective_materials[index]
        thermal_strain = material.thermal_expansion * element.alpha_factor * model.delta_temperature
        strain = float(np.dot(relative, directions[index]) / lengths[index] - thermal_strain)
        stress = effective_moduli[index] * strain
        force = stress * effective_areas[index]
        strains[index] = strain
        stresses[index] = stress
        forces[index] = force
        weight = lengths[index]
        node_stress_sum[element.node_i] += abs(stress) * weight
        node_stress_sum[element.node_j] += abs(stress) * weight
        node_stress_weight[element.node_i] += weight
        node_stress_weight[element.node_j] += weight
        mass += material.density * effective_areas[index] * lengths[index]

    reactions_vector = stiffness @ displacement_vector - total_load
    reactions = reactions_vector.reshape((-1, 3))
    displacement_magnitude = np.linalg.norm(displacement, axis=1)
    nodal_equivalent_stress = np.divide(
        node_stress_sum,
        node_stress_weight,
        out=np.zeros_like(node_stress_sum),
        where=node_stress_weight > 0,
    )
    utilization = np.asarray([
        abs(stresses[index]) / max(effective_materials[index].yield_strength, 1.0)
        for index in range(len(model.elements))
    ])
    critical = int(np.argmax(utilization))
    max_displacement_node = int(np.argmax(displacement_magnitude))
    external_resultant = model.loads.sum(axis=0) * load_scale
    constrained_reaction = reactions.reshape(-1)[fixed]
    equilibrium_reference = max(float(np.linalg.norm(total_load)), 1.0)
    equilibrium_residual = float(np.linalg.norm((stiffness @ displacement_vector - total_load)[free]) / equilibrium_reference)
    max_utilization = float(utilization[critical])
    # Keep the transport JSON finite for a zero-load case.  1e12 is reported
    # as a practical "unbounded in this linear model" sentinel.
    safety_factor = float(1.0 / max_utilization) if max_utilization > 0 else 1e12
    total_strain_energy = float(0.5 * displacement_vector @ stiffness @ displacement_vector)

    return {
        "schema_version": "1.0",
        "solver": "linear_3d_truss_fem",
        "model": {
            "name": model.name,
            "title": model.title,
            "category": model.category,
            "description": model.description,
            "node_count": node_count,
            "element_count": len(model.elements),
            "parameters": model.parameters,
            "assumptions": model.assumptions,
            "delta_temperature_c": model.delta_temperature,
        },
        "nodes": model.nodes.tolist(),
        "elements": [[element.node_i, element.node_j] for element in model.elements],
        "faces": model.faces,
        "loads_n": (model.loads * load_scale).tolist(),
        "fixed_nodes": sorted({dof // 3 for dof in model.fixed_dofs}),
        "fixed_dofs": sorted(model.fixed_dofs),
        "displacement_m": displacement.tolist(),
        "displacement_magnitude_m": displacement_magnitude.tolist(),
        "element_stress_pa": stresses.tolist(),
        "element_strain": strains.tolist(),
        "element_force_n": forces.tolist(),
        "element_utilization": utilization.tolist(),
        "nodal_equivalent_stress_pa": nodal_equivalent_stress.tolist(),
        "reactions_n": reactions.tolist(),
        "metrics": {
            "max_displacement_m": float(displacement_magnitude[max_displacement_node]),
            "max_displacement_node": max_displacement_node,
            "max_abs_stress_pa": float(np.max(np.abs(stresses))),
            "critical_element": critical,
            "critical_element_nodes": [model.elements[critical].node_i, model.elements[critical].node_j],
            "max_utilization": max_utilization,
            "minimum_safety_factor": safety_factor,
            "mass_kg": float(mass),
            "strain_energy_j": total_strain_energy,
            "condition_number": condition_number,
            "equilibrium_residual": equilibrium_residual,
            "external_resultant_n": external_resultant.tolist(),
            "constrained_reaction_norm_n": float(np.linalg.norm(constrained_reaction)),
        },
        "units": {"length": "m", "force": "N", "stress": "Pa", "mass": "kg"},
        "quality": {
            "status": "screening_only",
            "message": "Concept-level linear truss FEM. Validate geometry, joints, contacts, mesh convergence, materials and loads in a qualified solver before engineering use.",
        },
    }


def _box_beam(
    *,
    name: str,
    title: str,
    category: str,
    description: str,
    length: float,
    width: float,
    height: float,
    stations: int,
    area: float,
    material: str,
) -> tuple[ModelBuilder, list[list[int]]]:
    builder = ModelBuilder(name, title, category, description)
    grid: list[list[int]] = []
    for station in range(stations):
        x = length * station / (stations - 1)
        grid.append([
            builder.node((x, -width / 2, -height / 2)),
            builder.node((x, width / 2, -height / 2)),
            builder.node((x, -width / 2, height / 2)),
            builder.node((x, width / 2, height / 2)),
        ])
    station_edges = ((0, 1), (1, 3), (3, 2), (2, 0), (0, 3), (1, 2))
    face_pairs = ((0, 1), (2, 3), (0, 2), (1, 3))
    for nodes in grid:
        for a, b in station_edges:
            builder.element(nodes[a], nodes[b], area, material)
    for station in range(stations - 1):
        left, right = grid[station], grid[station + 1]
        for corner in range(4):
            builder.element(left[corner], right[corner], area, material)
        for a, b in face_pairs:
            builder.element(left[a], right[b], area, material)
            builder.element(left[b], right[a], area, material)
    builder.parameters.update(length_m=length, width_m=width, height_m=height, member_area_m2=area, material=material)
    return builder, grid


def _double_layer_plate(
    *,
    name: str,
    title: str,
    category: str,
    description: str,
    length: float,
    width: float,
    thickness: float,
    nx: int,
    ny: int,
    area: float,
    top_material: str,
    bottom_material: str | None = None,
    connector_material: str | None = None,
) -> tuple[ModelBuilder, list[list[list[int]]]]:
    builder = ModelBuilder(name, title, category, description)
    bottom_material = bottom_material or top_material
    connector_material = connector_material or top_material
    layers: list[list[list[int]]] = []
    for layer, z in enumerate((-thickness / 2, thickness / 2)):
        rows: list[list[int]] = []
        for iy in range(ny):
            y = -width / 2 + width * iy / (ny - 1)
            rows.append([
                builder.node((length * ix / (nx - 1), y, z))
                for ix in range(nx)
            ])
        layers.append(rows)
        material = bottom_material if layer == 0 else top_material
        for iy in range(ny):
            for ix in range(nx - 1):
                builder.element(rows[iy][ix], rows[iy][ix + 1], area, material)
        for iy in range(ny - 1):
            for ix in range(nx):
                builder.element(rows[iy][ix], rows[iy + 1][ix], area, material)
        for iy in range(ny - 1):
            for ix in range(nx - 1):
                builder.element(rows[iy][ix], rows[iy + 1][ix + 1], area, material)
                builder.element(rows[iy + 1][ix], rows[iy][ix + 1], area, material)
    for iy in range(ny):
        for ix in range(nx):
            builder.element(layers[0][iy][ix], layers[1][iy][ix], area, connector_material)
    for iy in range(ny - 1):
        for ix in range(nx - 1):
            builder.element(layers[0][iy][ix], layers[1][iy + 1][ix + 1], area, connector_material)
            builder.element(layers[1][iy][ix], layers[0][iy + 1][ix + 1], area, connector_material)
            builder.element(layers[0][iy + 1][ix], layers[1][iy][ix + 1], area, connector_material)
            builder.element(layers[1][iy + 1][ix], layers[0][iy][ix + 1], area, connector_material)
            builder.faces.append([
                layers[1][iy][ix],
                layers[1][iy][ix + 1],
                layers[1][iy + 1][ix + 1],
                layers[1][iy + 1][ix],
            ])
    builder.parameters.update(length_m=length, width_m=width, thickness_m=thickness, member_area_m2=area)
    return builder, layers


def _cantilever(load_scale: float = 1.0) -> StressModel:
    builder, grid = _box_beam(
        name="cantilever_beam", title="Cantilever beam", category="structures",
        description="Tip-loaded 3D lattice beam for load-path and stiffness studies.",
        length=4.0, width=0.45, height=0.55, stations=9, area=7.5e-4, material="structural_steel",
    )
    for node in grid[0]:
        builder.fix(node)
    for node in grid[-1]:
        builder.load(node, (0, 0, -12_500 * load_scale))
    return builder.build()


def _simply_supported(load_scale: float = 1.0) -> StressModel:
    builder, grid = _box_beam(
        name="simply_supported_beam", title="Simply supported beam", category="structures",
        description="Distributed service load on a simply supported space-frame beam.",
        length=8.0, width=0.65, height=0.8, stations=13, area=9e-4, material="structural_steel",
    )
    builder.fix(grid[0][0], "xyz")
    for node in grid[0][1:]:
        builder.fix(node, "yz")
    for node in grid[-1]:
        builder.fix(node, "yz")
    for station in grid:
        for node in station:
            builder.load(node, (0, 0, -2_000 * load_scale))
    return builder.build()


def _truss_bridge(load_scale: float = 1.0) -> StressModel:
    builder, grid = _box_beam(
        name="truss_bridge", title="Truss bridge", category="civil",
        description="Two-lane bridge surrogate with deck gravity and traffic loading.",
        length=30.0, width=6.0, height=4.0, stations=11, area=8e-3, material="structural_steel",
    )
    for node in grid[0]:
        builder.fix(node, "xyz")
    for node in grid[-1]:
        builder.fix(node, "yz")
    for station in grid:
        for node in station[:2]:
            builder.load(node, (0, 0, -110_000 * load_scale))
    return builder.build()


def _crane_boom(load_scale: float = 1.0) -> StressModel:
    builder, grid = _box_beam(
        name="crane_boom", title="Lattice crane boom", category="heavy_equipment",
        description="Inclined crane boom with a concentrated hook load.",
        length=14.0, width=0.9, height=0.9, stations=12, area=2.5e-3, material="structural_steel",
    )
    angle = np.deg2rad(22.0)
    model = builder.build()
    x, z = model.nodes[:, 0].copy(), model.nodes[:, 2].copy()
    model.nodes[:, 0] = x * np.cos(angle) - z * np.sin(angle)
    model.nodes[:, 2] = x * np.sin(angle) + z * np.cos(angle) + 1.0
    for node in grid[0]:
        model.fixed_dofs.update((node * 3, node * 3 + 1, node * 3 + 2))
    for node in grid[-1]:
        model.loads[node, 2] -= 62_500 * load_scale
    return model


def _robot_arm(load_scale: float = 1.0) -> StressModel:
    builder, grid = _box_beam(
        name="robot_arm_reach", title="Robot arm reach", category="robotics",
        description="Lightweight CFRP arm under tool payload and process force.",
        length=2.2, width=0.22, height=0.28, stations=9, area=2.2e-4, material="carbon_fiber_quasi_iso",
    )
    for node in grid[0]:
        builder.fix(node)
    for node in grid[-1]:
        builder.load(node, (250 * load_scale, 90 * load_scale, -600 * load_scale))
    return builder.build()


def _plate_bending(
    name: str,
    title: str,
    material: str,
    length: float,
    width: float,
    thickness: float,
    force: float,
    load_scale: float,
    category: str,
    description: str,
) -> StressModel:
    builder, layers = _double_layer_plate(
        name=name, title=title, category=category, description=description,
        length=length, width=width, thickness=thickness, nx=9, ny=5,
        area=max(thickness * min(length / 8, width / 4) * 0.16, 1e-8), top_material=material,
    )
    for layer in layers:
        for node in layer[0]:
            builder.fix(node, "z")
        for node in layer[-1]:
            builder.fix(node, "z")
    builder.fix(layers[0][0][0], "xy")
    builder.fix(layers[0][-1][0], "x")
    center_x = len(layers[0][0]) // 2
    for layer in layers:
        for row in layer:
            builder.load(row[center_x], (0, 0, -force * load_scale / (2 * len(row))))
    return builder.build()


def _phone(load_scale: float = 1.0) -> StressModel:
    return _plate_bending(
        "smartphone_three_point_bend", "Smartphone three-point bend", "aluminum_6061",
        0.16, 0.075, 0.004, 800, load_scale, "consumer_electronics",
        "Conceptual chassis bending and central deflection screening.",
    )


def _pcb(load_scale: float = 1.0) -> StressModel:
    return _plate_bending(
        "pcb_board_bending", "PCB board bending", "fr4", 0.22, 0.14, 0.0016,
        90, load_scale, "electronics", "Board flexure screening around a central assembly load.",
    )


def _solar(load_scale: float = 1.0) -> StressModel:
    model = _plate_bending(
        "solar_panel_wind", "Solar panel wind load", "aluminum_6061", 2.0, 1.1, 0.045,
        3_200, load_scale, "renewable_energy", "Out-of-plane wind pressure surrogate on a framed panel.",
    )
    return model


def _foldable_oled(load_scale: float = 1.0) -> StressModel:
    builder, layers = _double_layer_plate(
        name="foldable_oled_hinge", title="Foldable OLED hinge-region bending", category="display",
        description="Flexible-stack surrogate showing strain localization near a compliant hinge.",
        length=0.16, width=0.075, thickness=0.0012, nx=13, ny=5, area=2.5e-6,
        top_material="polyimide",
    )
    center = 6
    hinge_nodes = {layer[row][ix] for layer in layers for row in range(5) for ix in (center - 1, center, center + 1)}
    adjusted: list[Element] = []
    for element in builder.elements:
        factor = 0.18 if element.node_i in hinge_nodes or element.node_j in hinge_nodes else 1.0
        adjusted.append(Element(element.node_i, element.node_j, element.area, element.material, factor, element.alpha_factor))
    builder.elements = adjusted
    for layer in layers:
        for row in layer:
            builder.fix(row[0], "xyz")
            builder.load(row[-1], (0, 0, 5e-4 * load_scale / len(layer)))
    builder.assumptions.append("The hinge is represented by reduced axial stiffness, not contact or large-deformation shell mechanics")
    return builder.build()


def _chip_warpage(load_scale: float = 1.0) -> StressModel:
    builder, layers = _double_layer_plate(
        name="chip_package_warpage", title="Chip-package thermal warpage", category="semiconductor",
        description="CTE-mismatch surrogate for silicon on an FR-4/organic substrate during cooldown.",
        length=0.04, width=0.04, thickness=0.004, nx=9, ny=9, area=8e-7,
        top_material="silicon", bottom_material="fr4", connector_material="copper",
    )
    builder.delta_temperature = -125.0 * load_scale
    mid = 4
    # A low-force metrology fixture supports the bottom perimeter in z while
    # the centre/corner guides remove in-plane rigid motion.  This avoids the
    # mechanisms of a completely free pin-jointed surrogate and keeps CTE
    # mismatch free to act in-plane.
    for iy, row in enumerate(layers[0]):
        for ix, node in enumerate(row):
            if ix in (0, len(row) - 1) or iy in (0, len(layers[0]) - 1):
                builder.fix(node, "z")
    builder.fix(layers[0][mid][mid], "xy")
    builder.fix(layers[0][0][0], "x")
    builder.fix(layers[0][0][-1], "y")
    builder.assumptions.append("The 4 mm lattice depth is an effective bending depth, not a literal package cross-section")
    builder.assumptions.append("Layer CTE mismatch is reduced to axial truss members; viscoelastic cure and solder creep are excluded")
    return builder.build()


def _tower(load_scale: float = 1.0) -> StressModel:
    builder = ModelBuilder(
        "tower_wind", "Lattice tower wind load", "energy_infrastructure",
        "Tapered four-leg tower with height-dependent lateral wind load.",
    )
    levels = 9
    rows: list[list[int]] = []
    for level in range(levels):
        z = level * 4.0
        half = 2.4 - 1.3 * level / (levels - 1)
        rows.append([builder.node((x, y, z)) for x, y in ((-half, -half), (half, -half), (-half, half), (half, half))])
    for row in rows:
        for a, b in ((0, 1), (1, 3), (3, 2), (2, 0), (0, 3), (1, 2)):
            builder.element(row[a], row[b], 3.5e-3, "structural_steel")
    for level in range(levels - 1):
        a, b = rows[level], rows[level + 1]
        for corner in range(4):
            builder.element(a[corner], b[corner], 4.5e-3, "structural_steel")
        for p, q in ((0, 1), (2, 3), (0, 2), (1, 3)):
            builder.element(a[p], b[q], 2.5e-3, "structural_steel")
            builder.element(a[q], b[p], 2.5e-3, "structural_steel")
    for node in rows[0]:
        builder.fix(node)
    for level, row in enumerate(rows[1:], start=1):
        lateral = 7_500 * (level / (levels - 1)) ** 1.4 * load_scale
        for node in row:
            builder.load(node, (lateral, 0.18 * lateral, 0))
    return builder.build()


def _pipe(load_scale: float = 1.0) -> StressModel:
    builder = ModelBuilder(
        "pipe_pressure_support", "Pressurised pipe and supports", "process_equipment",
        "Cylindrical lattice surrogate under internal pressure and gravity.",
    )
    length, radius, stations, segments = 5.0, 0.55, 9, 12
    rows: list[list[int]] = []
    for ix in range(stations):
        x = length * ix / (stations - 1)
        rows.append([
            builder.node((x, radius * np.cos(2 * np.pi * j / segments), radius * np.sin(2 * np.pi * j / segments)))
            for j in range(segments)
        ])
    area = 6e-4
    for row in rows:
        for j in range(segments):
            builder.element(row[j], row[(j + 1) % segments], area, "structural_steel")
    for ix in range(stations - 1):
        for j in range(segments):
            builder.element(rows[ix][j], rows[ix + 1][j], area, "structural_steel")
            builder.element(rows[ix][j], rows[ix + 1][(j + 1) % segments], area, "structural_steel")
    for node in rows[0]:
        builder.fix(node)
    for node in rows[-1]:
        builder.fix(node, "yz")
    pressure = 1.2e6 * load_scale
    dx = length / (stations - 1)
    patch = (2 * np.pi * radius / segments) * dx
    for ix, row in enumerate(rows):
        end_factor = 0.5 if ix in (0, stations - 1) else 1.0
        for j, node in enumerate(row):
            theta = 2 * np.pi * j / segments
            radial = pressure * patch * end_factor / 2.0
            builder.load(node, (0, radial * np.cos(theta), radial * np.sin(theta) - 160.0))
    builder.assumptions.append("Pressure is converted to equivalent radial nodal loads; shell hoop/bending stresses are approximate")
    return builder.build()


def _bicycle(load_scale: float = 1.0) -> StressModel:
    builder = ModelBuilder(
        "bicycle_frame", "Bicycle frame load path", "mobility",
        "Diamond-frame surrogate under rider, crank and handlebar loads.",
    )
    points = {
        "rear": (0.0, 0.0), "crank": (0.45, 0.35), "seat": (0.38, 1.05),
        "head_low": (1.05, 0.55), "head_high": (1.0, 1.0), "front": (1.45, 0.0),
    }
    width = 0.10
    ids: dict[tuple[str, int], int] = {}
    for side, y in enumerate((-width / 2, width / 2)):
        for key, (x, z) in points.items():
            ids[(key, side)] = builder.node((x, y, z))
    frame_edges = (
        ("rear", "crank"), ("rear", "seat"), ("crank", "seat"),
        ("crank", "head_low"), ("seat", "head_high"), ("head_low", "head_high"),
        ("head_low", "front"), ("head_high", "front"),
    )
    for side in (0, 1):
        for a, b in frame_edges:
            builder.element(ids[(a, side)], ids[(b, side)], 3e-4, "aluminum_6061")
    for key in points:
        builder.element(ids[(key, 0)], ids[(key, 1)], 2e-4, "aluminum_6061")
    for a, b in frame_edges:
        builder.element(ids[(a, 0)], ids[(b, 1)], 1.2e-4, "aluminum_6061")
        builder.element(ids[(a, 1)], ids[(b, 0)], 1.2e-4, "aluminum_6061")
    # Real frames use welded/monocoque joints rather than mathematical pins.
    # These secondary braces provide the rotational stiffness that the axial
    # surrogate would otherwise lack.
    brace_edges = (("rear", "head_low"), ("rear", "head_high"), ("crank", "head_high"), ("seat", "head_low"))
    for a, b in brace_edges:
        for side in (0, 1):
            builder.element(ids[(a, side)], ids[(b, side)], 7e-5, "aluminum_6061")
        builder.element(ids[(a, 0)], ids[(b, 1)], 6e-5, "aluminum_6061")
        builder.element(ids[(a, 1)], ids[(b, 0)], 6e-5, "aluminum_6061")
    for support in ("rear", "front"):
        for side in (0, 1):
            builder.fix(ids[(support, side)], "xyz" if support == "rear" else "yz")
    for side in (0, 1):
        builder.load(ids[("seat", side)], (0, 0, -450 * load_scale))
        builder.load(ids[("head_high", side)], (70 * load_scale, 0, -80 * load_scale))
        builder.load(ids[("crank", side)], (0, 95 * (-1 if side == 0 else 1) * load_scale, -120 * load_scale))
    return builder.build()


def _battery_drop(load_scale: float = 1.0) -> StressModel:
    builder, grid = _box_beam(
        name="battery_module_drop", title="Battery module static drop surrogate", category="energy_storage",
        description="Quasi-static 8 g inertial load path in a protected battery enclosure.",
        length=1.2, width=0.65, height=0.22, stations=7, area=8e-4, material="aluminum_6061",
    )
    for node in grid[0]:
        builder.fix(node)
    total_force = 85.0 * 9.80665 * 8.0 * load_scale
    for station in grid:
        for node in station:
            builder.load(node, (0, 0, -total_force / (len(grid) * 4)))
    builder.assumptions.append("Impact is represented by a user-scalable equivalent static acceleration; transient contact is excluded")
    return builder.build()


EXAMPLES: dict[str, tuple[str, str, str, Callable[[float], StressModel]]] = {
    "cantilever_beam": ("Cantilever beam", "structures", "Tip load / stiffness", _cantilever),
    "simply_supported_beam": ("Simply supported beam", "structures", "Distributed service load", _simply_supported),
    "truss_bridge": ("Truss bridge", "civil", "Traffic and deck load", _truss_bridge),
    "crane_boom": ("Lattice crane boom", "heavy_equipment", "Hook load", _crane_boom),
    "robot_arm_reach": ("Robot arm reach", "robotics", "Tool payload and process force", _robot_arm),
    "smartphone_three_point_bend": ("Smartphone three-point bend", "consumer_electronics", "Chassis flexure", _phone),
    "pcb_board_bending": ("PCB board bending", "electronics", "Assembly-induced board flexure", _pcb),
    "solar_panel_wind": ("Solar panel wind load", "renewable_energy", "Out-of-plane wind", _solar),
    "foldable_oled_hinge": ("Foldable OLED hinge", "display", "Hinge strain localization", _foldable_oled),
    "chip_package_warpage": ("Chip-package thermal warpage", "semiconductor", "CTE mismatch cooldown", _chip_warpage),
    "tower_wind": ("Lattice tower wind load", "energy_infrastructure", "Height-dependent wind", _tower),
    "pipe_pressure_support": ("Pressurised pipe", "process_equipment", "Internal pressure and gravity", _pipe),
    "bicycle_frame": ("Bicycle frame", "mobility", "Rider and pedal load path", _bicycle),
    "battery_module_drop": ("Battery module drop", "energy_storage", "Equivalent-static impact", _battery_drop),
}


def list_examples() -> list[dict[str, str]]:
    return [
        {"id": key, "title": value[0], "category": value[1], "study": value[2]}
        for key, value in EXAMPLES.items()
    ]


def build_example(name: str, load_scale: float = 1.0) -> StressModel:
    try:
        factory = EXAMPLES[name][3]
    except KeyError as exc:
        raise ValueError(f"Unknown example '{name}'. Available: {', '.join(EXAMPLES)}") from exc
    return factory(float(load_scale))


def run_example(
    name: str,
    *,
    load_scale: float = 1.0,
    area_scale: float = 1.0,
    material_override: str | None = None,
) -> dict:
    # The example factory owns physical load/temperature scaling.  Solver load
    # scaling remains 1.0 to avoid accidentally multiplying it twice.
    model = build_example(name, load_scale)
    return solve_model(model, area_scale=area_scale, material_override=material_override)
