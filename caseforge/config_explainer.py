from pathlib import Path


EXPLANATIONS = {
    "SOLVER": {
        "simple": "Tells SU2 what type of physics problem to solve.",
        "detail": "For our nozzle starter case, EULER means inviscid compressible flow. Inviscid means we ignore viscosity/friction first to keep the case simpler.",
    },
    "MATH_PROBLEM": {
        "simple": "Tells SU2 whether this is a normal simulation or an optimization/adjoint problem.",
        "detail": "DIRECT means we are solving the normal flow field directly.",
    },
    "RESTART_SOL": {
        "simple": "Tells SU2 whether to start fresh or continue from an old solution.",
        "detail": "NO means start from the beginning. YES means read a previous restart file.",
    },
    "KIND_TURB_MODEL": {
        "simple": "Tells SU2 which turbulence model to use.",
        "detail": "NONE means no turbulence model. This is okay for an Euler starter case.",
    },
    "GAMMA_VALUE": {
        "simple": "Ratio of specific heats for the gas.",
        "detail": "For air and nitrogen, gamma is commonly around 1.4. It affects compressible-flow behavior.",
    },
    "GAS_CONSTANT": {
        "simple": "Gas constant used by the ideal gas equation.",
        "detail": "For nitrogen, this is around 296.8 J/kg/K. SU2 uses it to connect pressure, density, and temperature.",
    },
    "FREESTREAM_PRESSURE": {
        "simple": "Reference pressure around the flow.",
        "detail": "For this nozzle case, we use outlet/ambient pressure as the reference pressure.",
    },
    "FREESTREAM_TEMPERATURE": {
        "simple": "Reference temperature for the flow.",
        "detail": "This gives SU2 a temperature scale for compressible-flow calculations.",
    },
    "MESH_FILENAME": {
        "simple": "Tells SU2 which mesh file to read.",
        "detail": "The mesh file contains the small cells/control volumes where SU2 solves the flow equations.",
    },
    "MESH_FORMAT": {
        "simple": "Tells SU2 the mesh file format.",
        "detail": "SU2 means the mesh is written in SU2's native mesh format.",
    },
    "INLET_TYPE": {
        "simple": "Tells SU2 what kind of inlet boundary condition is being used.",
        "detail": "TOTAL_CONDITIONS means we give total pressure and total temperature at the inlet.",
    },
    "MARKER_INLET": {
        "simple": "Defines where gas enters the domain.",
        "detail": "The first word inside the bracket must match the inlet boundary name inside the mesh file.",
    },
    "MARKER_OUTLET": {
        "simple": "Defines where gas exits the domain.",
        "detail": "For this case, we give outlet static pressure.",
    },
    "MARKER_EULER": {
        "simple": "Defines inviscid solid walls.",
        "detail": "Euler wall means slip wall. Flow cannot pass through the wall, but wall friction is ignored.",
    },
    "MARKER_SYM": {
        "simple": "Defines a symmetry boundary.",
        "detail": "For 2D axisymmetric nozzle cases, this often represents the center axis.",
    },
    "MARKER_PLOTTING": {
        "simple": "Tells SU2 which boundary to use for plotting surface-related data.",
        "detail": "We use outlet so we can monitor exit-related behavior.",
    },
    "MARKER_MONITORING": {
        "simple": "Tells SU2 which boundary to monitor for force or flow quantities.",
        "detail": "This helps SU2 track useful values during the run.",
    },
    "NUM_METHOD_GRAD": {
        "simple": "Chooses how SU2 estimates gradients between cells.",
        "detail": "Gradients help SU2 understand how pressure, velocity, and temperature change across the mesh.",
    },
    "CFL_NUMBER": {
        "simple": "Controls how aggressively the solver marches toward a solution.",
        "detail": "Lower CFL is safer but slower. Higher CFL is faster but can become unstable.",
    },
    "CFL_ADAPT": {
        "simple": "Tells SU2 whether it can automatically change CFL during the run.",
        "detail": "NO means keep CFL fixed.",
    },
    "CONV_NUM_METHOD_FLOW": {
        "simple": "Chooses the numerical method for convective fluxes.",
        "detail": "ROE is a common method for compressible flow, especially where shocks or strong pressure changes may appear.",
    },
    "MUSCL_FLOW": {
        "simple": "Improves spatial accuracy of the flow solution.",
        "detail": "YES means SU2 uses a higher-order reconstruction method.",
    },
    "SLOPE_LIMITER_FLOW": {
        "simple": "Prevents numerical oscillations near sharp changes.",
        "detail": "Limiters are useful in compressible flow where shocks or rapid changes can occur.",
    },
    "TIME_DISCRE_FLOW": {
        "simple": "Chooses how SU2 advances the solution numerically.",
        "detail": "EULER_IMPLICIT is commonly used for steady simulations because it can be stable for larger steps.",
    },
    "LINEAR_SOLVER": {
        "simple": "Solver used for internal algebra equations.",
        "detail": "CFD creates many equations. The linear solver helps solve those equations efficiently.",
    },
    "LINEAR_SOLVER_PREC": {
        "simple": "Preconditioner for the linear solver.",
        "detail": "A preconditioner helps the linear solver converge faster.",
    },
    "LINEAR_SOLVER_ERROR": {
        "simple": "Accuracy target for the internal linear solver.",
        "detail": "Smaller value means more accurate internal solve, but it may take more time.",
    },
    "LINEAR_SOLVER_ITER": {
        "simple": "Maximum internal iterations for the linear solver.",
        "detail": "This limits how much work the linear solver does each main CFD step.",
    },
    "EXT_ITER": {
        "simple": "Number of main CFD iterations.",
        "detail": "More iterations give the solution more time to converge.",
    },
    "CONV_RESIDUAL_MINVAL": {
        "simple": "Target residual level for convergence.",
        "detail": "Residuals are like error signals. Lower residual means the solution is becoming more stable.",
    },
    "SCREEN_OUTPUT": {
        "simple": "Controls what SU2 prints on the terminal screen.",
        "detail": "Useful for watching convergence while SU2 runs.",
    },
    "HISTORY_OUTPUT": {
        "simple": "Controls what SU2 saves in the history file.",
        "detail": "CaseForge can later read this file to monitor convergence.",
    },
    "OUTPUT_FILES": {
        "simple": "Controls which result files SU2 writes.",
        "detail": "For example, ParaView output lets you visualize Mach number, pressure, temperature, etc.",
    },
    "VOLUME_FILENAME": {
        "simple": "Name of the volume solution output file.",
        "detail": "This file contains flow-field data inside the full domain.",
    },
    "SURFACE_FILENAME": {
        "simple": "Name of the surface solution output file.",
        "detail": "This file contains data on boundaries like wall or outlet.",
    },
    "RESTART_FILENAME": {
        "simple": "Name of the restart file.",
        "detail": "Restart files allow you to continue a simulation later.",
    },
    "SOLUTION_FILENAME": {
        "simple": "Name of the solution file.",
        "detail": "This stores the computed solution data.",
    },
}


def extract_config_items(config_text: str) -> list[dict[str, str]]:
    """
    Extract SU2 config keys and values.

    Example:
    SOLVER= EULER

    becomes:
    key = SOLVER
    value = EULER
    """
    items = []
    seen_keys = set()

    for line in config_text.splitlines():
        clean_line = line.strip()

        if not clean_line:
            continue

        if clean_line.startswith("%"):
            continue

        if "=" not in clean_line:
            continue

        key, value = clean_line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if key in seen_keys:
            continue

        seen_keys.add(key)

        items.append(
            {
                "key": key,
                "value": value,
            }
        )

    return items


def explain_su2_config(config_path: str | Path) -> list[dict[str, str]]:
    """
    Explain a SU2 config file in simple words.
    """
    path = Path(config_path)

    if not path.exists():
        return [
            {
                "key": "ERROR",
                "value": str(path),
                "simple": "Config file not found.",
                "detail": "Check the file path and try again.",
            }
        ]

    config_text = path.read_text(encoding="utf-8")
    config_items = extract_config_items(config_text)

    explanations = []

    for item in config_items:
        key = item["key"]
        value = item["value"]

        explanation = EXPLANATIONS.get(
            key,
            {
                "simple": "No beginner explanation available yet.",
                "detail": "This key may be advanced, uncommon, or not yet added to CaseForge's explanation dictionary.",
            },
        )

        explanations.append(
            {
                "key": key,
                "value": value,
                "simple": explanation["simple"],
                "detail": explanation["detail"],
            }
        )

    return explanations

def write_explanation_markdown(
    explanations: list[dict[str, str]],
    output_path: str | Path,
) -> Path:
    """
    Write config explanations into a clean Markdown file.
    """
    path = Path(output_path)

    lines = [
        "# SU2 Config Explanation",
        "",
        "This file was generated by CaseForge.",
        "",
        "It explains SU2 configuration settings in beginner-friendly language.",
        "",
    ]

    for item in explanations:
        lines.append(f"## {item['key']}")
        lines.append("")
        lines.append(f"**Value:** `{item['value']}`")
        lines.append("")
        lines.append(f"**Simple meaning:** {item['simple']}")
        lines.append("")
        lines.append(f"**Detailed explanation:** {item['detail']}")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")

    return path