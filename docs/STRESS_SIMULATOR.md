# Blender MCP 3D Stress Simulator

## 목적과 최신 기준

이 모듈은 자연어 지시로 구조 모델을 계산하고 Blender 장면에 응력·변형·하중·구속조건을 함께 표시하는 개념검토용 3D 해석 도구다. 기반 코드는 2026-08-16의 [upstream BlenderMCP 커밋](https://github.com/ahujasid/blender-mcp/commit/c69b90153616f2d767fe2e825d3310efbf6fcab5)에 동기화했으며, 권장 실행 환경은 2026-07-14 공개된 [Blender 5.2 LTS](https://developer.blender.org/docs/release_notes/5.2/)다. 장면 생성은 공식 [Blender Python API](https://docs.blender.org/api/current/index.html)를 사용한다.

현재 버전은 숨겨진 물리 애니메이션이 아니라 명시적인 선형 3D truss/FEM 계산을 수행한다. 다만 solid/shell/contact/plasticity solver가 아니므로 설계 인증, 파손 판정 또는 안전 관련 최종 의사결정에는 사용할 수 없다.

## 계산 모델

각 부재의 방향벡터를 $\mathbf{n}$, 길이를 $L$, 단면적을 $A$, 탄성계수를 $E$라 하면 3D truss element의 강성은 다음과 같다.

$$
\mathbf{k}_e = \frac{AE}{L}
\begin{bmatrix}
\mathbf{n}\mathbf{n}^{T} & -\mathbf{n}\mathbf{n}^{T} \\
-\mathbf{n}\mathbf{n}^{T} & \mathbf{n}\mathbf{n}^{T}
\end{bmatrix}
$$

전체 강성행렬을 조립하고 구속 자유도를 제거해 다음 식을 푼다.

$$
\mathbf{K}_{ff}\mathbf{u}_f = \mathbf{F}_f + \mathbf{F}_{th,f}
$$

열변형이 있는 경우 초기 변형률과 등가 절점력은 다음과 같다.

$$
\varepsilon_{th}=\alpha\Delta T,\qquad
\mathbf{F}_{th,e}=AE\alpha\Delta T[-\mathbf{n},\mathbf{n}]^T
$$

부재의 축방향 변형률, 응력, 축력은 다음과 같이 복원한다.

$$
\varepsilon_e=\frac{(\mathbf{u}_j-\mathbf{u}_i)\cdot\mathbf{n}}{L}-\alpha\Delta T,
\quad \sigma_e=E\varepsilon_e,
\quad N_e=A\sigma_e
$$

결과에는 최대 변위, 최대 절대응력, 임계부재, 항복강도 기반 최소 안전율, 질량, 변형에너지, 반력, 강성행렬 조건수와 자유 자유도의 평형잔차가 포함된다. 기본 예제의 평형잔차는 자동시험에서 $10^{-8}$ 미만이어야 한다.

## 내장 예제 14종

| ID | 분야 | 주요 검토 항목 | 모델링 핵심 |
|---|---|---|---|
| `cantilever_beam` | 구조 | 끝단하중, 강성 | 3D box lattice, 고정단 |
| `simply_supported_beam` | 구조 | 등분포 사용하중 | pin/roller 근사 |
| `truss_bridge` | 토목 | 상판·교통하중 | 양측 지지, 공간 truss |
| `crane_boom` | 중장비 | hook 집중하중 | 22° 경사 lattice boom |
| `robot_arm_reach` | 로봇 | payload·공정력·질량 | CFRP screening 물성 |
| `tower_wind` | 에너지 인프라 | 높이별 풍하중 | tapered four-leg tower |
| `pipe_pressure_support` | 공정설비 | 내압·자중·지지 | 원통 lattice와 등가 방사하중 |
| `bicycle_frame` | 모빌리티 | rider·pedal·handle 하중경로 | 양측 diamond frame |
| `battery_module_drop` | 배터리 | 8 g 등가정적 충격 | enclosure lattice |
| `smartphone_three_point_bend` | 전자제품 | 중앙굽힘·chassis 변위 | 이중층 plate surrogate |
| `pcb_board_bending` | 전장 | 조립하중·board flexure | FR-4 이중층 lattice |
| `solar_panel_wind` | 신재생 | 면외 풍하중 | framed panel surrogate |
| `foldable_oled_hinge` | 디스플레이 | hinge strain localization | 중앙부 강성 저감 PI lattice |
| `chip_package_warpage` | 반도체 | Si/기판 CTE mismatch | 열하중·지그 z-guide |

기본 물성은 구조용 강, Al 6061-T6, Ti-6Al-4V, 구리, 실리콘, PI, PC, FR-4, quasi-isotropic CFRP 9종이다. 모두 대표값이므로 실제 lot, 온도, 방향성, strain rate와 공정 이력에 맞춘 보정이 필요하다.

## 사용법

Blender add-on과 MCP server를 설치·연결한 다음 MCP client에서 다음 순서로 실행한다.

1. `list_stress_simulation_examples`로 예제와 물성을 확인한다.
2. `run_stress_simulation`에 `example`, `load_scale`, `area_scale`을 준다.
3. `visualize=true`이면 Blender에 `StressSim::<example>` collection이 생성된다.
4. `sweep_stress_parameter`로 하중 또는 단면적 DOE를 수행한다.

예시 요청:

```text
run_stress_simulation으로 cantilever_beam을 load_scale=1.5로 계산하고 자동 변형배율로 시각화하라.
```

```text
sweep_stress_parameter에서 truss_bridge의 area_scale을 [0.6, 0.8, 1.0, 1.2, 1.5]로 비교하라.
```

```text
robot_arm_reach를 aluminum_6061, structural_steel, carbon_fiber_quasi_iso로 각각 계산하고 질량-변위 Pareto 표를 만들어라.
```

## Blender 결과 장면

- 12단계 blue–cyan–green–yellow–red 응력/이용률 색상
- 실제 해석 절점에 변위를 더한 변형 형상
- 얇은 dark line의 미변형 기준 형상
- 고정 절점 cube marker
- magenta 하중 vector
- 최대응력, 최대변위, 최소안전율, 표시 변형배율 KPI text
- plate 계열의 면 geometry와 truss member overlay

`deformation_scale=0`은 모델 bounding-box 대각선의 약 12%가 되도록 자동 확대한다. 표시 배율은 결과 collection custom property와 KPI text에 기록된다. 화면상 변형 크기를 실제 변형으로 오해하지 않아야 한다.

## 활용 예

- OLED: fold hinge 강성비, 지지위치, 하중 크기에 따른 strain localization 비교
- 반도체: package CTE 조합과 냉각 온도차에 따른 warpage 경향 비교
- 품질: 현상 재현용 load-path 설명 장면, 고객 보고용 before/after rendering
- 교육: 하중–변위 선형성, 단면적–응력 역비례, 구속조건의 영향 실습
- 설계 탐색: 재료 변경에 따른 질량·변위·안전율 trade-off
- DOE: 하중 또는 단면적 20수준 sweep 결과를 표·chart로 변환
- Digital twin 초기모델: 센서 변위와 계산 변위를 맞추기 위한 modulus/section calibration
- 3D 콘텐츠: 응력 색상과 변형 animation을 이용한 기술 세미나·VR 설명 자료

## 해석 한계와 승급 경로

현재 모델은 axial truss이므로 다음 현상을 직접 계산하지 않는다.

- shell/solid의 굽힘응력과 두께방향 응력
- 접촉, 마찰, 볼트 preload, weld hotspot
- plasticity, buckling, fracture, fatigue, creep, viscoelasticity
- large deformation과 실제 fold contact
- anisotropic silicon/CFRP/PI와 적층 복합재
- transient impact, modal response와 열-구조 연성

실제품 의사결정에는 다음 승급 절차를 권장한다.

1. 실측 geometry와 material coupon data로 입력을 보정한다.
2. mesh convergence와 경계조건 sensitivity를 수행한다.
3. CalculiX, Code_Aster, FEniCSx, Abaqus, Ansys 등 검증된 solid/shell solver와 교차검증한다.
4. strain gauge, DIC, warpage, 3-point bend 등 실험 결과와 오차를 정량화한다.
5. solver version, mesh, 접촉, 물성, load case와 승인자를 보고서에 고정한다.

## 개발·검증

```bash
uv sync
uv run pytest tests/test_stress_engine.py -q
uv run pytest -q
```

자동시험은 14개 예제의 계산 성공, 유한값, 평형잔차, 하중 2배 시 응력·변위 2배, 단면적 2배 시 응력·변위 1/2 및 질량 2배, 열 warpage의 비영 변위를 확인한다.

