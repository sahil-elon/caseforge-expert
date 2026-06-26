# CaseForge

[![Tests](https://github.com/sahil-elon/caseforge/actions/workflows/tests.yml/badge.svg)](https://github.com/sahil-elon/caseforge/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

CaseForge is a beginner-friendly command-line toolkit for SU2-based aerospace CFD workflows.

It helps users generate starter SU2 cases, inspect configuration files, validate common setup mistakes, explain SU2 config keys in simple language, analyze convergence history files, plot residuals, and generate Markdown simulation reports.

## Why CaseForge?

SU2 is powerful, but setting up and reviewing CFD cases can be confusing for beginners. Configuration files can become long, history files can be hard to interpret, and simple mistakes in boundary markers or solver settings can waste hours.

CaseForge reduces this friction by turning common SU2 workflow tasks into simple commands.

## Features

* Generate starter SU2 nozzle cases
* Inspect SU2 `.cfg` files
* Validate SU2 configs for common beginner mistakes
* Explain SU2 config keys in beginner-friendly language
* Analyze SU2 `history.csv` convergence files
* Detect residuals, aerodynamic coefficients, forces, and moments
* Generate residual convergence plots
* Create Markdown simulation reports
* Check local setup using a doctor command

## Installation

Clone the repository:

```bash
git clone https://github.com/sahil-elon/caseforge.git
cd caseforge
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

On Linux/macOS:

```bash
source .venv/bin/activate
```

Install CaseForge:

```bash
python -m pip install -e .
```

For development and tests:

```bash
python -m pip install -e ".[dev]"
```

## Quick Start

Check that CaseForge is installed:

```bash
caseforge --help
```

Create a starter nozzle case:

```bash
caseforge create nozzle --output demo_case
```

Validate the generated config:

```bash
caseforge validate demo_case/case.cfg --case-type nozzle
```

Inspect the config:

```bash
caseforge inspect demo_case/case.cfg
```

Explain the config in simple language:

```bash
caseforge explain demo_case/case.cfg --save-md
```

Analyze a SU2 history file:

```bash
caseforge monitor demo_case/history.csv --plot
```

Generate a report:

```bash
caseforge report demo_case
```

Check your local setup:

```bash
caseforge doctor --case-dir demo_case
```

## ## Current Case Generation Support

CaseForge currently supports starter case generation for nozzle and generic SU2 cases.

| Command                      | Status    |
| ---------------------------- | --------- |
| `caseforge create nozzle`    | Available |
| `caseforge create generic`   | Available |
| `caseforge create airfoil`   | Planned   |
| `caseforge create wedge`     | Planned   |
| `caseforge create flatplate` | Planned   |

## Universal Commands

These commands are designed to work with many normal SU2-style files.

| Command    | Works with                   |
| ---------- | ---------------------------- |
| `inspect`  | Most SU2 `.cfg` files        |
| `validate` | Most SU2 `.cfg` files        |
| `explain`  | Most SU2 `.cfg` files        |
| `monitor`  | SU2-like `history.csv` files |
| `report`   | SU2 case folders             |



## Example Workflow

```bash
caseforge create nozzle --output demo_case
caseforge validate demo_case/case.cfg --case-type nozzle
caseforge inspect demo_case/case.cfg
caseforge explain demo_case/case.cfg --save-md
caseforge report demo_case
```

Generated files:

```txt
demo_case/
├── case.cfg
├── run.bat
├── run.sh
├── case_info.md
├── config_explanation.md
└── report.md
```

If a `history.csv` file is present, CaseForge can also generate:

```txt
residual_plot.png
```

## What CaseForge Is Not

CaseForge is not a CFD solver.

It does not replace SU2, Pointwise, ParaView, or engineering judgment.

It is a workflow assistant designed to make SU2 case setup, review, explanation, and reporting easier.

## Requirements

* Python 3.10 or newer
* Typer
* Rich
* Jinja2
* Pandas
* Matplotlib

Optional tools:

* SU2 for running simulations
* ParaView or pvpython for advanced visualization workflows

CaseForge can still generate, inspect, validate, explain, and report cases even if SU2 or ParaView is not installed.

## Development

Run tests:

```bash
pytest
```

Run tests with detailed output:

```bash
pytest -v
```

## Roadmap

* Add airfoil case generation
* Add supersonic wedge case generation
* Add flat plate boundary-layer case generation
* Add generic SU2 config generator
* Add Streamlit dashboard UI
* Add ParaView automation support
* Add better report customization
* Add more SU2 config explanations
* Add example CFD cases with real SU2 outputs

## License

This project is licensed under the MIT License.
