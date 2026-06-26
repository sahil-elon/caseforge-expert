from pathlib import Path

from caseforge.validators import validate_su2_config, config_has_errors
from caseforge.config_explainer import explain_su2_config
from caseforge.monitor import analyze_history, write_residual_plot


def count_status(results: list[dict[str, str]], status: str) -> int:
    """
    Count PASS/WARN/ERROR items.
    """
    return sum(1 for item in results if item["status"] == status)


def write_case_report(
    case_dir: str | Path,
    config_name: str = "case.cfg",
    history_name: str = "history.csv",
    output_name: str = "report.md",
) -> Path:
    """
    Create a Markdown report for a CaseForge-generated SU2 case.
    """
    case_path = Path(case_dir)
    config_path = case_path / config_name
    history_path = case_path / history_name
    output_path = case_path / output_name

    validation_results = validate_su2_config(config_path, case_type="generic")
    explanations = explain_su2_config(config_path)

    has_history = history_path.exists()
    history_analysis = analyze_history(history_path) if has_history else None
    residual_plot_path = None

    if has_history:
        try:
            residual_plot_path = write_residual_plot(
                history_path=history_path,
                output_path=case_path / "residual_plot.png",
            )
        except Exception:
            residual_plot_path = None
    pass_count = count_status(validation_results, "PASS")
    warn_count = count_status(validation_results, "WARN")
    error_count = count_status(validation_results, "ERROR")

    lines = [
        "# CaseForge Simulation Report",
        "",
        "This report was generated automatically by CaseForge.",
        "",
        "## Case Folder",
        "",
        f"`{case_path}`",
        "",
        "## Files Checked",
        "",
        f"- Config file: `{config_path}`",
        f"- History file: `{history_path}`" if has_history else "- History file: not found",
        "",
        "## Validation Summary",
        "",
        f"- PASS: {pass_count}",
        f"- WARN: {warn_count}",
        f"- ERROR: {error_count}",
        "",
    ]

    if config_has_errors(validation_results):
        lines.extend(
            [
                "**Overall status:** ❌ Config has errors.",
                "",
                "Fix the ERROR items before running SU2.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "**Overall status:** ✅ Config structure looks okay for a starter SU2 run.",
                "",
            ]
        )

    lines.extend(
        [
            "## Validation Details",
            "",
            "| Status | Check | Message |",
            "|---|---|---|",
        ]
    )

    for item in validation_results:
        lines.append(f"| {item['status']} | {item['check']} | {item['message']} |")

    lines.extend(
        [
            "",
            "## Important SU2 Settings Explained",
            "",
            "| Key | Value | Simple Meaning |",
            "|---|---|---|",
        ]
    )

    important_keys = {
        "SOLVER",
        "MESH_FILENAME",
        "MARKER_INLET",
        "MARKER_OUTLET",
        "MARKER_EULER",
        "MARKER_SYM",
        "CFL_NUMBER",
        "EXT_ITER",
        "OUTPUT_FILES",
    }

    for item in explanations:
        if item["key"] in important_keys:
            safe_value = item["value"].replace("|", "\\|")
            safe_simple = item["simple"].replace("|", "\\|")
            lines.append(f"| {item['key']} | `{safe_value}` | {safe_simple} |")

    lines.append("")

    lines.extend(
        [
            "## Convergence / History Summary",
            "",
        ]
    )
    if residual_plot_path is not None:
        lines.extend(
            [
                "![Residual convergence plot](residual_plot.png)",
                "",
            ]
        )
    if not has_history:
        lines.extend(
            [
                "No `history.csv` file was found.",
                "",
                "This is normal before running SU2. After a real SU2 run, place `history.csv` in this case folder and run the report command again.",
                "",
            ]
        )
    elif history_analysis is None:
        lines.append("History analysis was not performed.")
        lines.append("")
    elif not history_analysis["ok"]:
        lines.extend(
            [
                f"History status: **{history_analysis['health']}**",
                "",
                history_analysis["message"],
                "",
            ]
        )
    else:
        lines.extend(
            [
                f"Rows found: **{history_analysis['rows']}**",
                "",
                f"Health: **{history_analysis['health']}**",
                "",
                f"{history_analysis['message']}",
                "",
                "| Residual | First | Last | Minimum | Trend | Improvement |",
                "|---|---:|---:|---:|---|---:|",
            ]
        )

        for residual in history_analysis["residuals"]:
            improvement = residual["improvement_ratio"]

            if improvement is None:
                improvement_text = "N/A"
            elif improvement == float("inf"):
                improvement_text = "infinite"
            else:
                improvement_text = f"{improvement:.2f}x"

            lines.append(
                "| "
                f"{residual['name']} | "
                f"{residual['first']:.3e} | "
                f"{residual['last']:.3e} | "
                f"{residual['min']:.3e} | "
                f"{residual['trend']} | "
                f"{improvement_text} |"
            )

        lines.append("")

    lines.extend(
        [
            "## Beginner Notes",
            "",
            "- If residuals decrease, the solver is generally moving in the right direction.",
            "- If residuals increase strongly, try reducing CFL number.",
            "- If SU2 cannot find a marker, check that mesh boundary names match the config boundary names.",
            "- If the solution looks strange, check mesh quality, boundary conditions, and physical inputs.",
            "",
            "## Next Steps",
            "",
            "1. Open the SU2 output files in ParaView.",
            "2. Check Mach number, pressure, and temperature contours.",
            "3. Compare convergence behavior with the residual summary.",
            "4. Update this report after every major simulation change.",
            "",
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")

    return output_path