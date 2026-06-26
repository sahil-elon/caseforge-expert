from pathlib import Path
from typing import Any

import pandas as pd


def _clean_column_name(column: str) -> str:
    """
    Clean column names coming from SU2 history files.

    SU2 history files may contain column names with:
    - spaces
    - quotes
    - extra brackets
    - inconsistent formatting

    This function makes them easier to work with.
    """
    return str(column).strip().strip('"').strip("'")


def load_history_file(history_file: str | Path) -> pd.DataFrame:
    """
    Load a SU2-style history file into a pandas DataFrame.

    We first try normal CSV loading.
    If that fails, we try whitespace-separated loading.

    This is useful because SU2 history outputs may be .csv or .dat-like.
    """
    path = Path(history_file)

    if not path.exists():
        raise FileNotFoundError(f"History file not found: {path}")

    try:
        df = pd.read_csv(path, comment="#")
    except Exception:
        df = pd.read_csv(path, comment="#", sep=r"\s+", engine="python")

    df.columns = [_clean_column_name(col) for col in df.columns]

    df = df.dropna(axis=1, how="all")

    if df.empty:
        raise ValueError(f"History file is empty or could not be parsed: {path}")

    return df


def detect_iteration_column(df: pd.DataFrame) -> str:
    """
    Detect which column represents iteration number.

    Common SU2 names can be:
    - Iter
    - ITER
    - Inner_Iter
    - Outer_Iter
    - Time_Iter

    If none are found, we safely use the first column.
    """
    possible_names = {
        "iter",
        "iteration",
        "inneriter",
        "outeriter",
        "timeiter",
        "inner_iter",
        "outer_iter",
        "time_iter",
    }

    for col in df.columns:
        simplified = col.lower().replace(" ", "").replace("-", "_")
        compact = simplified.replace("_", "")

        if simplified in possible_names or compact in possible_names:
            return col

    return df.columns[0]


def _is_numeric_column(df: pd.DataFrame, column: str) -> bool:
    """
    Check if a column behaves like numeric data.
    """
    converted = pd.to_numeric(df[column], errors="coerce")
    return converted.notna().sum() > 0


def classify_history_columns(df: pd.DataFrame, iteration_column: str) -> dict[str, list[str]]:
    """
    Classify history columns into engineering groups.

    This helps users understand what the history file contains.
    """
    residuals: list[str] = []
    coefficients: list[str] = []
    forces: list[str] = []
    moments: list[str] = []
    other_numeric: list[str] = []

    coefficient_names = {
        "cl",
        "cd",
        "csf",
        "cmx",
        "cmy",
        "cmz",
        "cfx",
        "cfy",
        "cfz",
        "ct",
        "cq",
        "efficiency",
    }

    for col in df.columns:
        if col == iteration_column:
            continue

        if not _is_numeric_column(df, col):
            continue

        lower = col.lower()

        if "rms" in lower or "res" in lower or "residual" in lower:
            residuals.append(col)
            continue

        compact = (
            lower.replace(" ", "")
            .replace("_", "")
            .replace("-", "")
            .replace("[", "")
            .replace("]", "")
            .replace('"', "")
            .replace("'", "")
        )

        if compact in coefficient_names:
            coefficients.append(col)
            continue

        if "force" in lower or compact.startswith("force"):
            forces.append(col)
            continue

        if "moment" in lower or compact.startswith("moment"):
            moments.append(col)
            continue

        other_numeric.append(col)

    return {
        "residuals": residuals,
        "coefficients": coefficients,
        "forces": forces,
        "moments": moments,
        "other_numeric": other_numeric,
    }


def _safe_float(value: Any) -> float | None:
    """
    Convert a value to float safely.
    """
    try:
        return float(value)
    except Exception:
        return None


def _column_start_end(df: pd.DataFrame, column: str) -> dict[str, float | None]:
    """
    Get first and final numeric values of a column.
    """
    series = pd.to_numeric(df[column], errors="coerce").dropna()

    if series.empty:
        return {"start": None, "end": None}

    return {
        "start": _safe_float(series.iloc[0]),
        "end": _safe_float(series.iloc[-1]),
    }


def summarize_history(history_file: str | Path) -> dict[str, Any]:
    """
    Create a structured summary of a SU2 history file.

    This function does not print anything.
    It returns data that the CLI can display.
    """
    df = load_history_file(history_file)
    iteration_column = detect_iteration_column(df)
    groups = classify_history_columns(df, iteration_column)

    iteration_values = pd.to_numeric(df[iteration_column], errors="coerce").dropna()

    if iteration_values.empty:
        first_iteration = None
        last_iteration = None
    else:
        first_iteration = int(iteration_values.iloc[0])
        last_iteration = int(iteration_values.iloc[-1])

    residual_summary = {}

    for col in groups["residuals"]:
        values = _column_start_end(df, col)
        start = values["start"]
        end = values["end"]

        if start is not None and end is not None:
            change = end - start
        else:
            change = None

        residual_summary[col] = {
            "start": start,
            "end": end,
            "change": change,
        }

    coefficient_summary = {}

    for col in groups["coefficients"]:
        series = pd.to_numeric(df[col], errors="coerce").dropna()

        if series.empty:
            continue

        coefficient_summary[col] = {
            "start": _safe_float(series.iloc[0]),
            "end": _safe_float(series.iloc[-1]),
            "min": _safe_float(series.min()),
            "max": _safe_float(series.max()),
            "mean": _safe_float(series.mean()),
        }

    return {
        "file": str(history_file),
        "rows": int(len(df)),
        "columns": list(df.columns),
        "iteration_column": iteration_column,
        "first_iteration": first_iteration,
        "last_iteration": last_iteration,
        "groups": groups,
        "residual_summary": residual_summary,
        "coefficient_summary": coefficient_summary,
    }