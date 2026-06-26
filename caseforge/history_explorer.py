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

def _numeric_dataframe_with_iteration(df: pd.DataFrame, iteration_column: str) -> pd.DataFrame:
    """
    Convert history dataframe values to numeric where possible.

    We avoid using errors='ignore' because some pandas versions behave differently.
    Instead, we try numeric conversion column by column.
    If a column cannot be converted, we keep the original text column.
    """
    numeric_df = df.copy()

    for col in numeric_df.columns:
        converted = pd.to_numeric(numeric_df[col], errors="coerce")

        # If at least one value was successfully converted, use the numeric version.
        # Otherwise keep the original column.
        if converted.notna().sum() > 0:
            numeric_df[col] = converted

    numeric_df[iteration_column] = pd.to_numeric(
        numeric_df[iteration_column],
        errors="coerce",
    )

    numeric_df = numeric_df.dropna(subset=[iteration_column])

    return numeric_df
def get_iteration_snapshot(history_file: str | Path, iteration: int) -> dict[str, Any]:
    """
    Get all available history values at a requested iteration.

    If the exact iteration is not found, return the nearest available iteration.
    """
    df = load_history_file(history_file)
    iteration_column = detect_iteration_column(df)
    df = _numeric_dataframe_with_iteration(df, iteration_column)

    if df.empty:
        raise ValueError("No valid iteration data found in history file.")

    distances = (df[iteration_column] - iteration).abs()
    nearest_index = distances.idxmin()
    row = df.loc[nearest_index]

    actual_iteration = int(row[iteration_column])
    exact_match = actual_iteration == iteration

    values = {}

    for col in df.columns:
        value = row[col]

        if pd.isna(value):
            values[col] = None
        elif isinstance(value, (int, float)):
            values[col] = float(value)
        else:
            converted = _safe_float(value)
            values[col] = converted if converted is not None else str(value)

    return {
        "file": str(history_file),
        "requested_iteration": iteration,
        "actual_iteration": actual_iteration,
        "exact_match": exact_match,
        "iteration_column": iteration_column,
        "values": values,
    }


def compare_iterations(
    history_file: str | Path,
    iteration_a: int,
    iteration_b: int,
) -> dict[str, Any]:
    """
    Compare all numeric values between two requested iterations.

    If exact iterations are not present, nearest available iterations are used.
    """
    snap_a = get_iteration_snapshot(history_file, iteration_a)
    snap_b = get_iteration_snapshot(history_file, iteration_b)

    values_a = snap_a["values"]
    values_b = snap_b["values"]

    comparison = {}

    for key in values_a:
        if key not in values_b:
            continue

        a = values_a[key]
        b = values_b[key]

        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            delta = b - a

            if a != 0:
                percent_change = (delta / abs(a)) * 100.0
            else:
                percent_change = None

            comparison[key] = {
                "a": a,
                "b": b,
                "delta": delta,
                "percent_change": percent_change,
            }

    return {
        "file": str(history_file),
        "iteration_a_requested": iteration_a,
        "iteration_b_requested": iteration_b,
        "iteration_a_actual": snap_a["actual_iteration"],
        "iteration_b_actual": snap_b["actual_iteration"],
        "comparison": comparison,
    }


def filter_iteration_range(
    history_file: str | Path,
    from_iter: int | None = None,
    to_iter: int | None = None,
) -> tuple[pd.DataFrame, str]:
    """
    Load history file and optionally filter by iteration range.
    """
    df = load_history_file(history_file)
    iteration_column = detect_iteration_column(df)
    df = _numeric_dataframe_with_iteration(df, iteration_column)

    if from_iter is not None:
        df = df[df[iteration_column] >= from_iter]

    if to_iter is not None:
        df = df[df[iteration_column] <= to_iter]

    if df.empty:
        raise ValueError("No rows found in the requested iteration range.")

    return df, iteration_column


def field_trend_summary(
    history_file: str | Path,
    field: str,
    from_iter: int | None = None,
    to_iter: int | None = None,
) -> dict[str, Any]:
    """
    Summarize how one selected field changes over an iteration range.
    """
    df, iteration_column = filter_iteration_range(history_file, from_iter, to_iter)

    if field not in df.columns:
        available = ", ".join(df.columns)
        raise ValueError(f"Field '{field}' not found. Available columns: {available}")

    values = pd.to_numeric(df[field], errors="coerce").dropna()

    if values.empty:
        raise ValueError(f"Field '{field}' does not contain numeric values.")

    iterations = pd.to_numeric(df.loc[values.index, iteration_column], errors="coerce")

    return {
        "file": str(history_file),
        "field": field,
        "iteration_column": iteration_column,
        "rows": int(len(values)),
        "first_iteration": int(iterations.iloc[0]),
        "last_iteration": int(iterations.iloc[-1]),
        "start": _safe_float(values.iloc[0]),
        "end": _safe_float(values.iloc[-1]),
        "min": _safe_float(values.min()),
        "max": _safe_float(values.max()),
        "mean": _safe_float(values.mean()),
        "std": _safe_float(values.std()),
        "delta": _safe_float(values.iloc[-1] - values.iloc[0]),
    }


def diagnose_history(history_file: str | Path, final_window: int = 500) -> dict[str, Any]:
    """
    Create basic engineering-style diagnostic notes for a SU2 history file.

    This is intentionally conservative:
    it does not claim a CFD solution is physically correct.
    It only comments on scalar history behavior.
    """
    summary = summarize_history(history_file)
    df = load_history_file(history_file)
    iteration_column = detect_iteration_column(df)
    groups = classify_history_columns(df, iteration_column)

    notes: list[str] = []

    rows = summary["rows"]
    notes.append(f"History file contains {rows} rows.")

    if summary["first_iteration"] is not None and summary["last_iteration"] is not None:
        notes.append(
            f"Iteration range detected: {summary['first_iteration']} to {summary['last_iteration']}."
        )

    residual_notes = []

    for col in groups["residuals"]:
        series = pd.to_numeric(df[col], errors="coerce").dropna()

        if len(series) < 2:
            continue

        start = float(series.iloc[0])
        end = float(series.iloc[-1])
        drop = end - start

        if end < start:
            residual_notes.append(
                f"{col}: decreased from {start:.4g} to {end:.4g} "
                f"(change {drop:.4g})."
            )
        else:
            residual_notes.append(
                f"{col}: did not decrease overall; changed from {start:.4g} to {end:.4g}."
            )

    if residual_notes:
        notes.append("Residual behavior:")
        notes.extend(residual_notes)
    else:
        notes.append("No residual-like columns were detected.")

    coefficient_notes = []

    window_size = min(final_window, len(df))

    for col in groups["coefficients"]:
        series = pd.to_numeric(df[col], errors="coerce").dropna()

        if len(series) < 2:
            continue

        final_series = series.tail(window_size)

        final_mean = float(final_series.mean())
        final_min = float(final_series.min())
        final_max = float(final_series.max())

        spread = final_max - final_min

        if abs(final_mean) > 1e-12:
            relative_spread_percent = (spread / abs(final_mean)) * 100.0
        else:
            relative_spread_percent = None

        if relative_spread_percent is not None:
            coefficient_notes.append(
                f"{col}: final-window mean={final_mean:.6g}, "
                f"range={spread:.6g}, relative spread={relative_spread_percent:.3f}%."
            )
        else:
            coefficient_notes.append(
                f"{col}: final-window mean={final_mean:.6g}, range={spread:.6g}."
            )

    if coefficient_notes:
        notes.append(f"Coefficient stability over final {window_size} rows:")
        notes.extend(coefficient_notes)
    else:
        notes.append("No aerodynamic coefficient-like columns were detected.")

    notes.append(
        "Diagnostic note: CaseForge analyzes scalar history trends only. "
        "Physical correctness still requires mesh quality review, boundary-condition review, "
        "flow-field visualization, and engineering judgment."
    )

    return {
        "file": str(history_file),
        "rows": rows,
        "first_iteration": summary["first_iteration"],
        "last_iteration": summary["last_iteration"],
        "notes": notes,
    }


def plot_field_trend(
    history_file: str | Path,
    field: str,
    output_file: str | Path,
    from_iter: int | None = None,
    to_iter: int | None = None,
) -> Path:
    """
    Plot one selected history field over an iteration range.
    """
    import matplotlib.pyplot as plt

    df, iteration_column = filter_iteration_range(history_file, from_iter, to_iter)

    if field not in df.columns:
        available = ", ".join(df.columns)
        raise ValueError(f"Field '{field}' not found. Available columns: {available}")

    x = pd.to_numeric(df[iteration_column], errors="coerce")
    y = pd.to_numeric(df[field], errors="coerce")

    valid = x.notna() & y.notna()

    if valid.sum() == 0:
        raise ValueError(f"No numeric data available for field '{field}'.")

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure()
    plt.plot(x[valid], y[valid], marker="o")
    plt.xlabel(iteration_column)
    plt.ylabel(field)
    plt.title(f"{field} trend")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()

    return output_path
def _numeric_dataframe_with_iteration(df: pd.DataFrame, iteration_column: str) -> pd.DataFrame:
    """
    Convert history dataframe values to numeric where possible.

    We use errors='coerce' because it is stable across pandas versions.
    If a column has at least one numeric value, we keep the numeric version.
    Otherwise, we keep the original text column.
    """
    numeric_df = df.copy()

    for col in numeric_df.columns:
        converted = pd.to_numeric(numeric_df[col], errors="coerce")

        if converted.notna().sum() > 0:
            numeric_df[col] = converted

    numeric_df[iteration_column] = pd.to_numeric(
        numeric_df[iteration_column],
        errors="coerce",
    )

    numeric_df = numeric_df.dropna(subset=[iteration_column])

    return numeric_df


def get_iteration_snapshot(history_file: str | Path, iteration: int) -> dict[str, Any]:
    """
    Get all available history values at a requested iteration.

    If exact iteration is not present, this function uses the nearest available iteration.

    Example:
    Requested: 26000
    Available: 25000 and 50000
    Used: 25000
    """
    df = load_history_file(history_file)
    iteration_column = detect_iteration_column(df)
    df = _numeric_dataframe_with_iteration(df, iteration_column)

    if df.empty:
        raise ValueError("No valid iteration data found in history file.")

    distances = (df[iteration_column] - iteration).abs()
    nearest_index = distances.idxmin()
    row = df.loc[nearest_index]

    actual_iteration = int(row[iteration_column])
    exact_match = actual_iteration == iteration

    values = {}

    for col in df.columns:
        value = row[col]

        if pd.isna(value):
            values[col] = None
        elif isinstance(value, (int, float)):
            values[col] = float(value)
        else:
            converted = _safe_float(value)
            values[col] = converted if converted is not None else str(value)

    return {
        "file": str(history_file),
        "requested_iteration": iteration,
        "actual_iteration": actual_iteration,
        "exact_match": exact_match,
        "iteration_column": iteration_column,
        "values": values,
    }