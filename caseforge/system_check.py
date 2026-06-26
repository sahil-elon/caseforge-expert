from pathlib import Path
import importlib.util
import shutil
import sys


def check_python_version() -> dict[str, str]:
    """
    Check if Python version is supported.
    """
    major = sys.version_info.major
    minor = sys.version_info.minor

    version_text = f"{major}.{minor}.{sys.version_info.micro}"

    if major == 3 and minor >= 10:
        return {
            "status": "PASS",
            "check": "Python version",
            "message": f"Python {version_text} is supported.",
        }

    return {
        "status": "ERROR",
        "check": "Python version",
        "message": f"Python {version_text} found. CaseForge needs Python 3.10 or newer.",
    }


def check_python_package(import_name: str, friendly_name: str) -> dict[str, str]:
    """
    Check if a Python package can be imported.
    """
    if importlib.util.find_spec(import_name) is not None:
        return {
            "status": "PASS",
            "check": friendly_name,
            "message": f"{friendly_name} is installed.",
        }

    return {
        "status": "ERROR",
        "check": friendly_name,
        "message": f"{friendly_name} is missing. Install it with pip.",
    }


def check_command(command_name: str, friendly_name: str, required: bool = False) -> dict[str, str]:
    """
    Check if a command exists in system PATH.
    """
    command_path = shutil.which(command_name)

    if command_path:
        return {
            "status": "PASS",
            "check": friendly_name,
            "message": f"Found: {command_path}",
        }

    if required:
        return {
            "status": "ERROR",
            "check": friendly_name,
            "message": f"{command_name} not found in PATH.",
        }

    return {
        "status": "WARN",
        "check": friendly_name,
        "message": f"{command_name} not found. Some features may not work on this machine.",
    }


def check_template_files() -> dict[str, str]:
    """
    Check if CaseForge template files exist.
    """
    package_dir = Path(__file__).resolve().parent
    template_path = package_dir / "templates" / "nozzle_euler.cfg.j2"

    if template_path.exists():
        return {
            "status": "PASS",
            "check": "Nozzle template",
            "message": f"Found: {template_path}",
        }

    return {
        "status": "ERROR",
        "check": "Nozzle template",
        "message": f"Missing template file: {template_path}",
    }


def check_case_folder(case_dir: str | None = None) -> list[dict[str, str]]:
    """
    Optionally check a generated case folder.
    """
    if case_dir is None:
        return []

    path = Path(case_dir)

    results = []

    if not path.exists():
        return [
            {
                "status": "ERROR",
                "check": "Case folder",
                "message": f"Case folder not found: {path}",
            }
        ]

    results.append(
        {
            "status": "PASS",
            "check": "Case folder",
            "message": f"Case folder found: {path}",
        }
    )

    expected_files = ["case.cfg", "run.bat", "run.sh", "case_info.md"]

    for file_name in expected_files:
        file_path = path / file_name

        if file_path.exists():
            results.append(
                {
                    "status": "PASS",
                    "check": file_name,
                    "message": f"{file_name} found.",
                }
            )
        else:
            results.append(
                {
                    "status": "WARN",
                    "check": file_name,
                    "message": f"{file_name} not found in case folder.",
                }
            )

    return results


def run_doctor(case_dir: str | None = None) -> list[dict[str, str]]:
    """
    Run all system/setup checks.
    """
    results = []

    results.append(check_python_version())

    required_packages = [
        ("typer", "Typer"),
        ("rich", "Rich"),
        ("jinja2", "Jinja2"),
        ("pandas", "Pandas"),
        ("matplotlib", "Matplotlib"),
    ]

    for import_name, friendly_name in required_packages:
        results.append(check_python_package(import_name, friendly_name))

    results.append(check_template_files())

    results.append(check_command("SU2_CFD", "SU2 solver", required=False))
    results.append(check_command("pvpython", "ParaView Python", required=False))
    results.append(check_command("paraview", "ParaView GUI", required=False))

    results.extend(check_case_folder(case_dir))

    return results


def doctor_has_errors(results: list[dict[str, str]]) -> bool:
    """
    Return True if doctor found ERROR items.
    """
    return any(item["status"] == "ERROR" for item in results)


def doctor_has_warnings(results: list[dict[str, str]]) -> bool:
    """
    Return True if doctor found WARN items.
    """
    return any(item["status"] == "WARN" for item in results)