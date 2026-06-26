from pathlib import Path
import re


GENERIC_REQUIRED_SU2_KEYS = [
    "SOLVER",
    "MATH_PROBLEM",
    "MESH_FILENAME",
    "MESH_FORMAT",
    "EXT_ITER",
    "OUTPUT_FILES",
]


NOZZLE_RECOMMENDED_KEYS = [
    "MARKER_INLET",
    "MARKER_OUTLET",
    "MARKER_EULER",
    "MARKER_SYM",
]


def has_su2_key(config_text: str, key: str) -> bool:
    """
    Check if a SU2 config key exists.

    Example:
    SOLVER= EULER
    """
    pattern = rf"^\s*{re.escape(key)}\s*="
    return re.search(pattern, config_text, re.MULTILINE) is not None


def get_number_value(config_text: str, key: str):
    """
    Try to read a number from a SU2 config line.

    Example:
    EXT_ITER= 1000
    """
    pattern = rf"^\s*{re.escape(key)}\s*=\s*([-+]?\d*\.?\d+)"
    match = re.search(pattern, config_text, re.MULTILINE)

    if not match:
        return None

    try:
        return float(match.group(1))
    except ValueError:
        return None


def extract_marker_keys(config_text: str) -> list[str]:
    """
    Find all SU2 marker-related keys.

    Example:
    MARKER_EULER
    MARKER_FAR
    MARKER_INLET
    """
    marker_keys = []

    for line in config_text.splitlines():
        clean_line = line.strip()

        if not clean_line or clean_line.startswith("%"):
            continue

        if "=" not in clean_line:
            continue

        key = clean_line.split("=", 1)[0].strip()

        if key.startswith("MARKER_"):
            marker_keys.append(key)

    return sorted(set(marker_keys))


def extract_marker_names(config_text: str) -> list[str]:
    """
    Extract approximate boundary marker names from MARKER lines.

    Example:
    MARKER_EULER= ( wall )
    returns:
    wall
    """
    marker_names = []

    for line in config_text.splitlines():
        clean_line = line.strip()

        if not clean_line or clean_line.startswith("%"):
            continue

        if not clean_line.startswith("MARKER_"):
            continue

        if "=" not in clean_line:
            continue

        value = clean_line.split("=", 1)[1].strip()

        # Remove brackets
        value = value.replace("(", "").replace(")", "")

        # Split by comma
        parts = [part.strip() for part in value.split(",") if part.strip()]

        if parts:
            marker_names.append(parts[0])

    return sorted(set(marker_names))


def validate_su2_config(config_path: str | Path, case_type: str = "generic") -> list[dict[str, str]]:
    """
    Validate a SU2 config file.

    case_type:
    - generic: works for most SU2 configs
    - nozzle: adds nozzle-specific checks
    """
    path = Path(config_path)
    case_type = case_type.lower().strip()

    results = []

    if not path.exists():
        return [
            {
                "status": "ERROR",
                "check": "File exists",
                "message": f"Config file not found: {path}",
            }
        ]

    if path.suffix.lower() != ".cfg":
        results.append(
            {
                "status": "WARN",
                "check": "File extension",
                "message": "Config file does not end with .cfg",
            }
        )
    else:
        results.append(
            {
                "status": "PASS",
                "check": "File extension",
                "message": "Config file has .cfg extension",
            }
        )

    config_text = path.read_text(encoding="utf-8")

    for key in GENERIC_REQUIRED_SU2_KEYS:
        if has_su2_key(config_text, key):
            results.append(
                {
                    "status": "PASS",
                    "check": key,
                    "message": f"{key} found",
                }
            )
        else:
            results.append(
                {
                    "status": "ERROR",
                    "check": key,
                    "message": f"{key} is missing",
                }
            )

    ext_iter = get_number_value(config_text, "EXT_ITER")

    if ext_iter is None:
        results.append(
            {
                "status": "ERROR",
                "check": "EXT_ITER value",
                "message": "Could not read EXT_ITER value",
            }
        )
    elif ext_iter <= 0:
        results.append(
            {
                "status": "ERROR",
                "check": "EXT_ITER value",
                "message": "EXT_ITER must be greater than zero",
            }
        )
    else:
        results.append(
            {
                "status": "PASS",
                "check": "EXT_ITER value",
                "message": f"EXT_ITER is valid: {int(ext_iter)}",
            }
        )

    marker_keys = extract_marker_keys(config_text)
    marker_names = extract_marker_names(config_text)

    if marker_keys:
        results.append(
            {
                "status": "PASS",
                "check": "Marker keys",
                "message": f"Found marker keys: {', '.join(marker_keys)}",
            }
        )
    else:
        results.append(
            {
                "status": "WARN",
                "check": "Marker keys",
                "message": "No MARKER_* keys found. Check if this config defines boundaries.",
            }
        )

    if marker_names:
        results.append(
            {
                "status": "PASS",
                "check": "Boundary names",
                "message": f"Detected possible boundary names: {', '.join(marker_names)}",
            }
        )
    else:
        results.append(
            {
                "status": "WARN",
                "check": "Boundary names",
                "message": "Could not detect boundary names from MARKER lines.",
            }
        )

    if case_type == "nozzle":
        for key in NOZZLE_RECOMMENDED_KEYS:
            if has_su2_key(config_text, key):
                results.append(
                    {
                        "status": "PASS",
                        "check": f"Nozzle: {key}",
                        "message": f"{key} found",
                    }
                )
            else:
                results.append(
                    {
                        "status": "WARN",
                        "check": f"Nozzle: {key}",
                        "message": f"{key} is recommended for this nozzle starter case.",
                    }
                )

        expected_nozzle_markers = ["inlet", "outlet", "wall", "symmetry"]

        for marker in expected_nozzle_markers:
            if marker in marker_names:
                results.append(
                    {
                        "status": "PASS",
                        "check": f"Nozzle marker: {marker}",
                        "message": f"Boundary marker '{marker}' detected",
                    }
                )
            else:
                results.append(
                    {
                        "status": "WARN",
                        "check": f"Nozzle marker: {marker}",
                        "message": f"Boundary marker '{marker}' not detected. Make sure mesh/config names match.",
                    }
                )

    elif case_type != "generic":
        results.append(
            {
                "status": "WARN",
                "check": "Case type",
                "message": f"Unknown case type '{case_type}'. Generic validation was used.",
            }
        )

    return results


def config_has_errors(results: list[dict[str, str]]) -> bool:
    """
    Return True if any validation result has ERROR status.
    """
    return any(item["status"] == "ERROR" for item in results)