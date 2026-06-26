from pathlib import Path

from caseforge.validators import extract_marker_keys, extract_marker_names


def parse_config_key_values(config_text: str) -> dict[str, str]:
    """
    Parse SU2 config lines into key-value pairs.

    Example:
    SOLVER= EULER

    becomes:
    {
        "SOLVER": "EULER"
    }
    """
    values = {}

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

        # Remove inline comments after %
        if "%" in value:
            value = value.split("%", 1)[0].strip()

        values[key] = value

    return values


def get_config_value(values: dict[str, str], key: str, default: str = "Not found") -> str:
    """
    Safely get one config value.
    """
    return values.get(key, default)


def infer_case_type(values: dict[str, str], marker_keys: list[str], marker_names: list[str]) -> str:
    """
    Guess the case type from config clues.

    This is only a smart guess, not a guaranteed truth.
    """
    solver = get_config_value(values, "SOLVER", "").upper()

    marker_key_set = set(marker_keys)
    marker_name_set = {name.lower() for name in marker_names}

    has_inlet_outlet = "MARKER_INLET" in marker_key_set and "MARKER_OUTLET" in marker_key_set
    has_farfield = (
        "MARKER_FAR" in marker_key_set
        or "MARKER_FARFIELD" in marker_key_set
        or "farfield" in marker_name_set
    )
    has_wall = (
        "MARKER_EULER" in marker_key_set
        or "MARKER_HEATFLUX" in marker_key_set
        or "MARKER_ISOTHERMAL" in marker_key_set
        or "wall" in marker_name_set
    )
    has_symmetry = "MARKER_SYM" in marker_key_set or "symmetry" in marker_name_set

    if has_inlet_outlet and has_wall:
        return "Internal flow / nozzle-like case"

    if has_farfield and has_wall and has_symmetry:
        return "External aerodynamic case with symmetry"

    if has_farfield and has_wall:
        return "External aerodynamic case"

    if "RANS" in solver and has_wall:
        return "Viscous/RANS wall-bounded case"

    if has_inlet_outlet:
        return "Internal flow case"

    return "Generic SU2 case"


def inspect_su2_config(config_path: str | Path) -> dict:
    """
    Inspect a SU2 config file and return a quick engineering summary.
    """
    path = Path(config_path)

    if not path.exists():
        return {
            "ok": False,
            "message": f"Config file not found: {path}",
        }

    config_text = path.read_text(encoding="utf-8")
    values = parse_config_key_values(config_text)

    marker_keys = extract_marker_keys(config_text)
    marker_names = extract_marker_names(config_text)

    summary = {
        "ok": True,
        "path": str(path),
        "total_keys": len(values),
        "solver": get_config_value(values, "SOLVER"),
        "math_problem": get_config_value(values, "MATH_PROBLEM"),
        "mesh_filename": get_config_value(values, "MESH_FILENAME"),
        "mesh_format": get_config_value(values, "MESH_FORMAT"),
        "iterations": get_config_value(values, "EXT_ITER"),
        "cfl": get_config_value(values, "CFL_NUMBER"),
        "output_files": get_config_value(values, "OUTPUT_FILES"),
        "marker_keys": marker_keys,
        "marker_names": marker_names,
        "likely_case_type": infer_case_type(values, marker_keys, marker_names),
    }

    return summary