from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from caseforge.generator import create_nozzle_case, create_generic_case
from caseforge.validators import validate_su2_config, config_has_errors
from caseforge.config_explainer import explain_su2_config, write_explanation_markdown
from caseforge.monitor import analyze_history, write_residual_plot
from caseforge.report import write_case_report
from caseforge.system_check import run_doctor, doctor_has_errors, doctor_has_warnings
from caseforge.config_inspector import inspect_su2_config
from caseforge.history_explorer import (
    compare_iterations,
    diagnose_history,
    field_trend_summary,
    get_iteration_snapshot,
    plot_field_trend,
    summarize_history,
)

app = typer.Typer(
    help="CaseForge Expert: SU2 workflow analytics toolkit for case inspection, history exploration, convergence diagnosis, and reporting."
)

console = Console()

history_app = typer.Typer(help="Explore and analyze SU2 history files.")
app.add_typer(history_app, name="history")


@app.command()
def version():
    """
    Show CaseForge version.
    """
    console.print("[bold green]CaseForge v0.1.0[/bold green]")
    
@history_app.command("summary")
def history_summary(
    history_file: str = typer.Argument(
        ...,
        help="Path to SU2 history.csv or history.dat file.",
    ),
):
    """
    Summarize a SU2 history file.
    """
    try:
        summary = summarize_history(history_file)
    except Exception as exc:
        console.print(f"[bold red]Failed to summarize history file:[/bold red] {exc}")
        raise typer.Exit(code=1)

    console.print("[bold blue]CaseForge History Summary[/bold blue]")
    console.print(f"File: {summary['file']}")
    console.print(f"Rows detected: {summary['rows']}")
    console.print(f"Iteration column: {summary['iteration_column']}")
    console.print(f"First iteration: {summary['first_iteration']}")
    console.print(f"Last iteration: {summary['last_iteration']}")

    column_table = Table(title="Detected Column Groups")
    column_table.add_column("Group", style="cyan")
    column_table.add_column("Columns", style="white")

    groups = summary["groups"]

    column_table.add_row("Residuals", ", ".join(groups["residuals"]) or "None detected")
    column_table.add_row("Coefficients", ", ".join(groups["coefficients"]) or "None detected")
    column_table.add_row("Forces", ", ".join(groups["forces"]) or "None detected")
    column_table.add_row("Moments", ", ".join(groups["moments"]) or "None detected")
    column_table.add_row("Other numeric", ", ".join(groups["other_numeric"]) or "None detected")

    console.print(column_table)

    residual_table = Table(title="Residual Start/End Summary")
    residual_table.add_column("Residual", style="cyan")
    residual_table.add_column("Start")
    residual_table.add_column("End")
    residual_table.add_column("Change")

    if summary["residual_summary"]:
        for name, values in summary["residual_summary"].items():
            residual_table.add_row(
                name,
                str(values["start"]),
                str(values["end"]),
                str(values["change"]),
            )
    else:
        residual_table.add_row("None detected", "-", "-", "-")

    console.print(residual_table)

    coefficient_table = Table(title="Coefficient Summary")
    coefficient_table.add_column("Coefficient", style="cyan")
    coefficient_table.add_column("Start")
    coefficient_table.add_column("End")
    coefficient_table.add_column("Min")
    coefficient_table.add_column("Max")
    coefficient_table.add_column("Mean")

    if summary["coefficient_summary"]:
        for name, values in summary["coefficient_summary"].items():
            coefficient_table.add_row(
                name,
                str(values["start"]),
                str(values["end"]),
                str(values["min"]),
                str(values["max"]),
                str(values["mean"]),
            )
    else:
        coefficient_table.add_row("None detected", "-", "-", "-", "-", "-")

    console.print(coefficient_table)


@history_app.command("get")
def history_get(
    history_file: str = typer.Argument(
        ...,
        help="Path to SU2 history.csv or history.dat file.",
    ),
    iteration: int = typer.Option(
        ...,
        "--iter",
        help="Requested iteration number.",
    ),
):
    """
    Show all available values at a requested iteration.
    """
    try:
        snapshot = get_iteration_snapshot(history_file, iteration)
    except Exception as exc:
        console.print(f"[bold red]Failed to get iteration snapshot:[/bold red] {exc}")
        raise typer.Exit(code=1)

    console.print("[bold blue]CaseForge Iteration Snapshot[/bold blue]")
    console.print(f"File: {snapshot['file']}")
    console.print(f"Requested iteration: {snapshot['requested_iteration']}")
    console.print(f"Actual iteration used: {snapshot['actual_iteration']}")

    if not snapshot["exact_match"]:
        console.print("[yellow]Exact iteration not found. Nearest available iteration was used.[/yellow]")

    table = Table(title="Iteration Values")
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    for key, value in snapshot["values"].items():
        table.add_row(str(key), str(value))

    console.print(table)


@history_app.command("diff")
def history_diff(
    history_file: str = typer.Argument(
        ...,
        help="Path to SU2 history.csv or history.dat file.",
    ),
    iter_a: int = typer.Option(
        ...,
        "--iter-a",
        help="First requested iteration.",
    ),
    iter_b: int = typer.Option(
        ...,
        "--iter-b",
        help="Second requested iteration.",
    ),
):
    """
    Compare numeric history values between two iterations.
    """
    try:
        result = compare_iterations(history_file, iter_a, iter_b)
    except Exception as exc:
        console.print(f"[bold red]Failed to compare iterations:[/bold red] {exc}")
        raise typer.Exit(code=1)

    console.print("[bold blue]CaseForge Iteration Difference[/bold blue]")
    console.print(f"File: {result['file']}")
    console.print(
        f"Iteration A: requested {result['iteration_a_requested']}, "
        f"used {result['iteration_a_actual']}"
    )
    console.print(
        f"Iteration B: requested {result['iteration_b_requested']}, "
        f"used {result['iteration_b_actual']}"
    )

    table = Table(title="Numeric Field Differences")
    table.add_column("Field", style="cyan")
    table.add_column("Iter A")
    table.add_column("Iter B")
    table.add_column("Delta")
    table.add_column("% Change")

    for field, values in result["comparison"].items():
        percent_change = values["percent_change"]

        if percent_change is None:
            percent_text = "-"
        else:
            percent_text = f"{percent_change:.3f}%"

        table.add_row(
            field,
            f"{values['a']:.6g}",
            f"{values['b']:.6g}",
            f"{values['delta']:.6g}",
            percent_text,
        )

    console.print(table)


@history_app.command("trend")
def history_trend(
    history_file: str = typer.Argument(
        ...,
        help="Path to SU2 history.csv or history.dat file.",
    ),
    field: str = typer.Option(
        ...,
        "--field",
        help="History field to analyze, for example CL, CD, RMS_DENSITY.",
    ),
    from_iter: int | None = typer.Option(
        None,
        "--from-iter",
        help="Optional starting iteration.",
    ),
    to_iter: int | None = typer.Option(
        None,
        "--to-iter",
        help="Optional ending iteration.",
    ),
    plot: bool = typer.Option(
        False,
        "--plot",
        help="Generate a plot for this field.",
    ),
):
    """
    Analyze one selected field over an iteration range.
    """
    try:
        trend = field_trend_summary(
            history_file,
            field=field,
            from_iter=from_iter,
            to_iter=to_iter,
        )
    except Exception as exc:
        console.print(f"[bold red]Failed to analyze field trend:[/bold red] {exc}")
        raise typer.Exit(code=1)

    console.print("[bold blue]CaseForge Field Trend Summary[/bold blue]")
    console.print(f"File: {trend['file']}")
    console.print(f"Field: {trend['field']}")
    console.print(f"Rows analyzed: {trend['rows']}")
    console.print(f"Iteration range: {trend['first_iteration']} to {trend['last_iteration']}")

    table = Table(title=f"{field} Trend")
    table.add_column("Metric", style="cyan")
    table.add_column("Value")

    for key in ["start", "end", "min", "max", "mean", "std", "delta"]:
        table.add_row(key, str(trend[key]))

    console.print(table)

    if plot:
        output_file = f"history_plots/{field}_trend.png"

        try:
            saved_path = plot_field_trend(
                history_file,
                field=field,
                output_file=output_file,
                from_iter=from_iter,
                to_iter=to_iter,
            )
        except Exception as exc:
            console.print(f"[bold red]Failed to create plot:[/bold red] {exc}")
            raise typer.Exit(code=1)

        console.print(f"[bold green]Plot saved:[/bold green] {saved_path}")    

@history_app.command("diagnose")
def history_diagnose(
    history_file: str = typer.Argument(
        ...,
        help="Path to SU2 history.csv or history.dat file.",
    ),
    final_window: int = typer.Option(
        500,
        "--final-window",
        help="Number of final rows used for coefficient stability checks.",
    ),
):
    """
    Generate basic engineering notes from a SU2 history file.
    """
    try:
        diagnosis = diagnose_history(history_file, final_window=final_window)
    except Exception as exc:
        console.print(f"[bold red]Failed to diagnose history file:[/bold red] {exc}")
        raise typer.Exit(code=1)

    console.print("[bold blue]CaseForge History Diagnosis[/bold blue]")
    console.print(f"File: {diagnosis['file']}")
    console.print(f"Rows: {diagnosis['rows']}")
    console.print(f"First iteration: {diagnosis['first_iteration']}")
    console.print(f"Last iteration: {diagnosis['last_iteration']}")

    console.print("\n[bold]Diagnostic Notes[/bold]")

    for note in diagnosis["notes"]:
        console.print(f"- {note}")


@app.command()
def create(
    case_type: str = typer.Argument(
        ...,
        help="Case type to create. Supported: nozzle, generic.",
    ),
    output: str = typer.Option(
        "caseforge_output",
        "--output",
        "-o",
        help="Folder where the generated case files will be saved.",
    ),
    mesh_file: str = typer.Option(
        "nozzle.su2",
        "--mesh",
        help="SU2 mesh filename to use in the generated config.",
    ),
    inlet_pressure: float = typer.Option(
        500000.0,
        "--inlet-pressure",
        help="Nozzle inlet total pressure in Pascal.",
    ),
    outlet_pressure: float = typer.Option(
        101325.0,
        "--outlet-pressure",
        help="Nozzle outlet static pressure in Pascal.",
    ),
    temperature: float = typer.Option(
        300.0,
        "--temperature",
        help="Inlet total temperature in Kelvin.",
    ),
    iterations: int = typer.Option(
        1000,
        "--iterations",
        help="Number of SU2 solver iterations.",
    ),
    solver: str = typer.Option(
        "EULER",
        "--solver",
        help="SU2 solver for generic cases. Example: EULER, RANS, NAVIER_STOKES.",
    ),
    cfl: float = typer.Option(
        1.0,
        "--cfl",
        help="CFL number for the generated config.",
    ),
    wall_marker: str = typer.Option(
        "wall",
        "--wall-marker",
        help="Wall boundary marker name for generic cases.",
    ),
    farfield_marker: str = typer.Option(
        "farfield",
        "--farfield-marker",
        help="Farfield boundary marker name for generic cases.",
    ),
    freestream_pressure: float = typer.Option(
        101325.0,
        "--freestream-pressure",
        help="Freestream/reference pressure in Pascal for generic cases.",
    ),
    freestream_temperature: float = typer.Option(
        300.0,
        "--freestream-temperature",
        help="Freestream/reference temperature in Kelvin for generic cases.",
    ),
):
    """
    Create a starter SU2 case.
    """

    case_type = case_type.lower().strip()

    if case_type not in {"nozzle", "generic"}:
        console.print("[bold red]Supported case types right now: nozzle, generic[/bold red]")
        console.print("Soon we will add: airfoil, wedge, and flatplate.")
        raise typer.Exit(code=1)

    if iterations <= 0:
        console.print("[bold red]Iterations must be greater than zero.[/bold red]")
        raise typer.Exit(code=1)

    if cfl <= 0:
        console.print("[bold red]CFL number must be greater than zero.[/bold red]")
        raise typer.Exit(code=1)

    if case_type == "nozzle":
        if inlet_pressure <= 0:
            console.print("[bold red]Inlet pressure must be positive.[/bold red]")
            raise typer.Exit(code=1)

        if outlet_pressure <= 0:
            console.print("[bold red]Outlet pressure must be positive.[/bold red]")
            raise typer.Exit(code=1)

        if inlet_pressure <= outlet_pressure:
            console.print("[bold red]For a nozzle case, inlet pressure should be greater than outlet pressure.[/bold red]")
            raise typer.Exit(code=1)

        if temperature <= 0:
            console.print("[bold red]Temperature must be positive.[/bold red]")
            raise typer.Exit(code=1)

        console.print("[bold blue]Creating nozzle case...[/bold blue]")

        created_files = create_nozzle_case(
            output_dir=output,
            mesh_file=mesh_file,
            inlet_pressure=inlet_pressure,
            outlet_pressure=outlet_pressure,
            temperature=temperature,
            iterations=iterations,
        )

    else:
        if freestream_pressure <= 0:
            console.print("[bold red]Freestream pressure must be positive.[/bold red]")
            raise typer.Exit(code=1)

        if freestream_temperature <= 0:
            console.print("[bold red]Freestream temperature must be positive.[/bold red]")
            raise typer.Exit(code=1)

        console.print("[bold blue]Creating generic SU2 case...[/bold blue]")

        created_files = create_generic_case(
            output_dir=output,
            mesh_file=mesh_file,
            solver=solver.upper(),
            iterations=iterations,
            cfl=cfl,
            wall_marker=wall_marker,
            farfield_marker=farfield_marker,
            freestream_pressure=freestream_pressure,
            freestream_temperature=freestream_temperature,
        )

    table = Table(title="Created files")
    table.add_column("File", style="cyan")

    for file_path in created_files:
        table.add_row(str(file_path))

    console.print(table)
    console.print("[bold green]Case created successfully.[/bold green]")

@app.command()
def validate(
    config_file: str = typer.Argument(..., help="Path to SU2 config file. Example: caseforge_output/case.cfg"),
    case_type: str = typer.Option(
        "generic",
        "--case-type",
        help="Validation mode: generic or nozzle.",
    ),
):
    """
    Validate a SU2 config file for common beginner mistakes.
    """
    console.print(f"[bold blue]Validating SU2 config:[/bold blue] {config_file}")

    results = validate_su2_config(config_file, case_type=case_type)

    table = Table(title="Validation Results")
    table.add_column("Status", style="bold")
    table.add_column("Check", style="cyan")
    table.add_column("Message", style="white")

    for item in results:
        status = item["status"]

        if status == "PASS":
            status_text = "[green]PASS[/green]"
        elif status == "WARN":
            status_text = "[yellow]WARN[/yellow]"
        else:
            status_text = "[red]ERROR[/red]"

        table.add_row(status_text, item["check"], item["message"])

    console.print(table)

    if config_has_errors(results):
        console.print()
        console.print("[bold red]Validation failed. Fix the ERROR items before running SU2.[/bold red]")
        raise typer.Exit(code=1)

    console.print()
    console.print("[bold green]Validation passed. This config looks ready for a starter SU2 run.[/bold green]")

@app.command()
def explain(
    config_file: str = typer.Argument(..., help="Path to SU2 config file. Example: caseforge_output/case.cfg"),
    details: bool = typer.Option(
        False,
        "--details",
        "-d",
        help="Show detailed explanations too.",
    ),
    save_md: bool = typer.Option(
        False,
        "--save-md",
        help="Save explanations to a Markdown file.",
    ),
):
    """
    Explain a SU2 config file in beginner-friendly language.
    """
    console.print(f"[bold blue]Explaining SU2 config:[/bold blue] {config_file}")

    explanations = explain_su2_config(config_file)

    table = Table(title="SU2 Config Explanation")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="yellow")
    table.add_column("Simple Meaning", style="white")

    if details:
        table.add_column("Detail", style="green")

    for item in explanations:
        value = item["value"]

        if len(value) > 45:
            value = value[:42] + "..."

        if details:
            table.add_row(item["key"], value, item["simple"], item["detail"])
        else:
            table.add_row(item["key"], value, item["simple"])

    console.print(table)

    if save_md:
        config_path = Path(config_file)
        output_path = config_path.parent / "config_explanation.md"

        saved_path = write_explanation_markdown(
            explanations=explanations,
            output_path=output_path,
        )

        console.print()
        console.print(f"[bold green]Markdown explanation saved:[/bold green] {saved_path}")

    console.print()
    console.print("[bold green]Done. This is your config translated into human language.[/bold green]")

@app.command()
def monitor(
    history_file: str = typer.Argument(..., help="Path to SU2 history.csv file."),
    plot: bool = typer.Option(
        False,
        "--plot",
        help="Save a residual convergence plot as PNG.",
    ),
):
    """
    Analyze SU2 history.csv convergence health and important metrics.
    """
    console.print(f"[bold blue]Monitoring SU2 history file:[/bold blue] {history_file}")

    analysis = analyze_history(history_file)

    if not analysis["ok"]:
        console.print(f"[bold red]{analysis['message']}[/bold red]")
        raise typer.Exit(code=1)

    console.print()
    console.print(f"[bold]Rows found:[/bold] {analysis['rows']}")

    if analysis.get("iteration_column"):
        console.print(f"[bold]Iteration column:[/bold] {analysis['iteration_column']}")

    def print_metric_table(title: str, rows: list[dict], improvement_label: str = "Ratio"):
        if not rows:
            return

        table = Table(title=title)
        table.add_column("Name", style="cyan")
        table.add_column("First", style="white")
        table.add_column("Last", style="white")
        table.add_column("Min", style="white")
        table.add_column("Max", style="white")
        table.add_column("Trend", style="bold")
        table.add_column(improvement_label, style="green")

        for item in rows:
            improvement = item.get("improvement_ratio")

            if improvement is None:
                improvement_text = "N/A"
            elif improvement == float("inf"):
                improvement_text = "infinite"
            else:
                improvement_text = f"{improvement:.2f}x"

            if item["trend"] == "decreasing":
                trend_text = "[green]decreasing[/green]"
            elif item["trend"] == "increasing":
                trend_text = "[red]increasing[/red]"
            else:
                trend_text = "[yellow]flat[/yellow]"

            table.add_row(
                item["name"],
                f"{item['first']:.3e}",
                f"{item['last']:.3e}",
                f"{item['min']:.3e}",
                f"{item['max']:.3e}",
                trend_text,
                improvement_text,
            )

        console.print(table)

    print_metric_table("Residual Summary", analysis["residuals"], improvement_label="Improvement")
    print_metric_table("Aerodynamic Coefficients", analysis["coefficients"], improvement_label="First/Last")
    print_metric_table("Forces", analysis["forces"], improvement_label="First/Last")
    print_metric_table("Moments", analysis["moments"], improvement_label="First/Last")

    console.print()

    if analysis["health"] == "GOOD":
        console.print(f"[bold green]{analysis['message']}[/bold green]")
    elif analysis["health"] == "BAD":
        console.print(f"[bold red]{analysis['message']}[/bold red]")
        console.print("[yellow]Suggestion: reduce CFL number, check mesh quality, and verify boundary conditions.[/yellow]")
    else:
        console.print(f"[bold yellow]{analysis['message']}[/bold yellow]")

    if plot:
        try:
            plot_path = write_residual_plot(history_file)
            console.print()
            console.print(f"[bold green]Residual plot saved:[/bold green] {plot_path}")
        except Exception as error:
            console.print()
            console.print(f"[bold red]Could not create residual plot:[/bold red] {error}")
            raise typer.Exit(code=1)
@app.command()
def report(
    case_dir: str = typer.Argument(..., help="Path to case folder. Example: caseforge_output"),
):
    """
    Generate a Markdown report for a SU2 case folder.
    """
    console.print(f"[bold blue]Generating CaseForge report for:[/bold blue] {case_dir}")

    report_path = write_case_report(case_dir)

    console.print()
    console.print(f"[bold green]Report generated:[/bold green] {report_path}")
    console.print()
    console.print("Open this file in VS Code to inspect it.")

def main():
    """
    Entry point for the installed caseforge command.
    """
    app()

@app.command()
def doctor(
    case_dir: str | None = typer.Option(
        None,
        "--case-dir",
        help="Optional case folder to check. Example: demo_case",
    ),
):
    """
    Check CaseForge setup, dependencies, templates, and optional CFD tools.
    """
    console.print("[bold blue]Running CaseForge doctor...[/bold blue]")

    results = run_doctor(case_dir=case_dir)

    table = Table(title="CaseForge Doctor")
    table.add_column("Status", style="bold")
    table.add_column("Check", style="cyan")
    table.add_column("Message", style="white")

    for item in results:
        status = item["status"]

        if status == "PASS":
            status_text = "[green]PASS[/green]"
        elif status == "WARN":
            status_text = "[yellow]WARN[/yellow]"
        else:
            status_text = "[red]ERROR[/red]"

        table.add_row(status_text, item["check"], item["message"])

    console.print(table)
    console.print()

    if doctor_has_errors(results):
        console.print("[bold red]Doctor found errors. Fix ERROR items before publishing or running full workflows.[/bold red]")
        raise typer.Exit(code=1)

    if doctor_has_warnings(results):
        console.print("[bold yellow]Doctor found warnings. Basic CaseForge works, but some optional tools are missing.[/bold yellow]")
        console.print("[yellow]This is okay if you only want to generate, validate, explain, or report cases.[/yellow]")
        return

    console.print("[bold green]Everything looks healthy.[/bold green]")

@app.command()
def inspect(
    config_file: str = typer.Argument(..., help="Path to SU2 config file. Example: demo_case/case.cfg"),
):
    """
    Inspect a SU2 config file and print a quick engineering summary.
    """
    console.print(f"[bold blue]Inspecting SU2 config:[/bold blue] {config_file}")

    summary = inspect_su2_config(config_file)

    if not summary["ok"]:
        console.print(f"[bold red]{summary['message']}[/bold red]")
        raise typer.Exit(code=1)

    table = Table(title="SU2 Config Inspection")
    table.add_column("Item", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("File", summary["path"])
    table.add_row("Likely case type", summary["likely_case_type"])
    table.add_row("Total config keys", str(summary["total_keys"]))
    table.add_row("Solver", summary["solver"])
    table.add_row("Math problem", summary["math_problem"])
    table.add_row("Mesh filename", summary["mesh_filename"])
    table.add_row("Mesh format", summary["mesh_format"])
    table.add_row("Iterations", summary["iterations"])
    table.add_row("CFL number", summary["cfl"])
    table.add_row("Output files", summary["output_files"])

    marker_keys = ", ".join(summary["marker_keys"]) if summary["marker_keys"] else "None detected"
    marker_names = ", ".join(summary["marker_names"]) if summary["marker_names"] else "None detected"

    table.add_row("Marker keys", marker_keys)
    table.add_row("Boundary names", marker_names)

    console.print(table)
    console.print()
    console.print("[bold green]Inspection complete.[/bold green]")

if __name__ == "__main__":
    main()