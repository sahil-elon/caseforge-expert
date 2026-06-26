from pathlib import Path

import pandas as pd


def clean_column_name(column: str) -> str:
    """
    Clean a CSV column name for easier matching.
    """
    return str(column).strip().replace('"', "").replace("'", "")


def find_iteration_column(columns: list[str]) -> str | None:
    """
    Try to find the iteration column in a SU2 history file.
    """
    possible_words = ["iter", "iteration", "inner_iter", "outer_iter"]

    for column in columns:
        clean = clean_column_name(column).lower()
        if any(word in clean for word in possible_words):
            return column

    return None


def find_columns_by_keywords(
    columns: list[str],
    keywords: list[str],
    exclude_keywords: list[str] | None = None,
) -> list[str]:
    """
    Find columns that contain any keyword.

    Example:
    keywords = ["rms", "res"]
    """
    if exclude_keywords is None:
        exclude_keywords = []

    matched_columns = []

    for column in columns:
        clean = clean_column_name(column).lower()

        has_keyword = any(keyword.lower() in clean for keyword in keywords)
        has_excluded = any(keyword.lower() in clean for keyword in exclude_keywords)

        if has_keyword and not has_excluded:
            matched_columns.append(column)

    return matched_columns


def find_residual_columns(columns: list[str]) -> list[str]:
    """
    Find residual-like columns.

    Examples:
    RMS_DENSITY
    RMS_MOMENTUM-X
    RMS_RES
    Res_Flow[0]
    residual
    """
    return find_columns_by_keywords(
        columns=columns,
        keywords=["rms", "res", "residual"],
        exclude_keywords=["restart"],
    )


def find_coefficient_columns(columns: list[str]) -> list[str]:
    """
    Find aerodynamic coefficient columns.

    Examples:
    CL
    CD
    CMz
    C_L
    C_D
    Drag_Coefficient
    Lift_Coefficient
    """
    coefficient_columns = []

    direct_names = {
        "cl",
        "cd",
        "cm",
        "cmx",
        "cmy",
        "cmz",
        "c_l",
        "c_d",
        "c_m",
        "coeff_lift",
        "coeff_drag",
        "coeff_moment",
    }

    for column in columns:
        clean = clean_column_name(column).lower()
        compact = clean.replace("-", "_").replace(" ", "_")

        if compact in direct_names:
            coefficient_columns.append(column)
            continue

        if "coeff" in compact or "coefficient" in compact:
            coefficient_columns.append(column)
            continue

        if "drag" in compact and ("coef" in compact or "coeff" in compact):
            coefficient_columns.append(column)
            continue

        if "lift" in compact and ("coef" in compact or "coeff" in compact):
            coefficient_columns.append(column)
            continue

    return sorted(set(coefficient_columns))


def find_force_columns(columns: list[str]) -> list[str]:
    """
    Find force-like columns.

    Examples:
    FORCE_X
    FORCE_Y
    LIFT
    DRAG
    """
    return find_columns_by_keywords(
        columns=columns,
        keywords=["force", "lift", "drag"],
        exclude_keywords=["coefficient", "coeff", "coef"],
    )


def find_moment_columns(columns: list[str]) -> list[str]:
    """
    Find moment-like columns.

    Examples:
    MOMENT_X
    MOMENT_Y
    MOMENT_Z
    """
    return find_columns_by_keywords(
        columns=columns,
        keywords=["moment"],
        exclude_keywords=["coefficient", "coeff", "coef"],
    )


def summarize_numeric_column(data: pd.DataFrame, column: str) -> dict | None:
    """
    Create a numerical summary for one column.
    """
    numeric_values = pd.to_numeric(data[column], errors="coerce").dropna()

    if len(numeric_values) < 2:
        return None

    first_value = float(numeric_values.iloc[0])
    last_value = float(numeric_values.iloc[-1])
    min_value = float(numeric_values.min())
    max_value = float(numeric_values.max())

    if last_value < first_value:
        trend = "decreasing"
    elif last_value > first_value:
        trend = "increasing"
    else:
        trend = "flat"

    if first_value == 0:
        improvement_ratio = None
    else:
        improvement_ratio = first_value / last_value if last_value != 0 else float("inf")

    absolute_change = last_value - first_value

    return {
        "name": column,
        "first": first_value,
        "last": last_value,
        "min": min_value,
        "max": max_value,
        "trend": trend,
        "improvement_ratio": improvement_ratio,
        "absolute_change": absolute_change,
    }


def summarize_columns(data: pd.DataFrame, columns: list[str]) -> list[dict]:
    """
    Summarize many numeric columns.
    """
    summaries = []

    for column in columns:
        summary = summarize_numeric_column(data, column)

        if summary is not None:
            summaries.append(summary)

    return summaries


def judge_residual_health(residuals: list[dict]) -> tuple[str, str]:
    """
    Judge convergence health mainly from residual behavior.
    """
    if not residuals:
        return (
            "WARN",
            "No residual columns found. CaseForge can still inspect other metrics, but convergence health is unclear.",
        )

    decreasing_count = sum(1 for item in residuals if item["trend"] == "decreasing")
    increasing_count = sum(1 for item in residuals if item["trend"] == "increasing")

    if decreasing_count == len(residuals):
        return (
            "GOOD",
            "Residuals are decreasing. Simulation looks healthy.",
        )

    if increasing_count > 0:
        return (
            "BAD",
            "Some residuals are increasing. Simulation may be diverging.",
        )

    return (
        "WARN",
        "Residuals are not clearly improving.",
    )


def analyze_history(history_path: str | Path) -> dict:
    """
    Read a SU2 history.csv file and analyze convergence and metrics.
    """
    path = Path(history_path)

    if not path.exists():
        return {
            "ok": False,
            "message": f"History file not found: {path}",
            "rows": 0,
            "health": "ERROR",
            "iteration_column": None,
            "residuals": [],
            "coefficients": [],
            "forces": [],
            "moments": [],
        }

    try:
        data = pd.read_csv(path)
    except Exception as error:
        return {
            "ok": False,
            "message": f"Could not read CSV file: {error}",
            "rows": 0,
            "health": "ERROR",
            "iteration_column": None,
            "residuals": [],
            "coefficients": [],
            "forces": [],
            "moments": [],
        }

    if data.empty:
        return {
            "ok": False,
            "message": "History file is empty.",
            "rows": 0,
            "health": "ERROR",
            "iteration_column": None,
            "residuals": [],
            "coefficients": [],
            "forces": [],
            "moments": [],
        }

    columns = list(data.columns)

    iteration_column = find_iteration_column(columns)

    residual_columns = find_residual_columns(columns)
    coefficient_columns = find_coefficient_columns(columns)
    force_columns = find_force_columns(columns)
    moment_columns = find_moment_columns(columns)

    residuals = summarize_columns(data, residual_columns)
    coefficients = summarize_columns(data, coefficient_columns)
    forces = summarize_columns(data, force_columns)
    moments = summarize_columns(data, moment_columns)

    health, message = judge_residual_health(residuals)

    detected_any_metric = bool(residuals or coefficients or forces or moments)

    if not detected_any_metric:
        return {
            "ok": True,
            "message": "CSV was readable, but no known SU2 residual/force/coefficient columns were detected.",
            "rows": len(data),
            "health": "WARN",
            "iteration_column": iteration_column,
            "residuals": [],
            "coefficients": [],
            "forces": [],
            "moments": [],
        }

    return {
        "ok": True,
        "message": message,
        "rows": len(data),
        "health": health,
        "iteration_column": iteration_column,
        "residuals": residuals,
        "coefficients": coefficients,
        "forces": forces,
        "moments": moments,
    }


def write_residual_plot(
    history_path: str | Path,
    output_path: str | Path | None = None,
) -> Path:
    """
    Create a residual convergence plot from a SU2 history.csv file.
    """
    import matplotlib

    matplotlib.use("Agg")

    import matplotlib.pyplot as plt

    path = Path(history_path)

    if not path.exists():
        raise FileNotFoundError(f"History file not found: {path}")

    data = pd.read_csv(path)

    if data.empty:
        raise ValueError("History file is empty.")

    columns = list(data.columns)

    iteration_column = find_iteration_column(columns)
    residual_columns = find_residual_columns(columns)

    if not residual_columns:
        raise ValueError("No residual columns found in history file.")

    if iteration_column:
        x_values = pd.to_numeric(data[iteration_column], errors="coerce")
        x_label = iteration_column
    else:
        x_values = range(1, len(data) + 1)
        x_label = "Iteration"

    if output_path is None:
        output = path.parent / "residual_plot.png"
    else:
        output = Path(output_path)

    plt.figure(figsize=(10, 6))

    plotted_anything = False

    for column in residual_columns:
        y_values = pd.to_numeric(data[column], errors="coerce")

        valid = y_values.notna()

        if valid.sum() < 2:
            continue

        plt.plot(
            list(pd.Series(x_values)[valid]),
            list(y_values[valid]),
            label=column,
        )

        plotted_anything = True

    if not plotted_anything:
        raise ValueError("Could not plot residuals because valid numeric data was not found.")

    plt.yscale("log")
    plt.xlabel(x_label)
    plt.ylabel("Residual")
    plt.title("SU2 Residual Convergence")
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.legend()
    plt.tight_layout()

    output.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output, dpi=200)
    plt.close()

    return output