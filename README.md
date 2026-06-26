# CaseForge Expert

[![Tests](https://github.com/sahil-elon/caseforge-expert/actions/workflows/tests.yml/badge.svg)](https://github.com/sahil-elon/caseforge-expert/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

CaseForge Expert is an advanced SU2 workflow analytics toolkit built from the CaseForge v0.1.0 foundation.

It is focused on expert-level SU2 history exploration, convergence diagnosis, plotting, configuration review, and automated CFD reporting.

> Note: The original CaseForge repository remains the basic/stable version. This repository is the advanced expert-focused version.

## Why CaseForge Expert?

SU2 is powerful, but reviewing CFD runs can become time-consuming when working with long configuration files, large history files, residual trends, aerodynamic coefficients, and simulation reports.

CaseForge Expert reduces this friction by turning common SU2 review and analysis tasks into simple terminal commands.

Instead of manually opening `history.csv` in Excel, Python, or plotting tools, CaseForge Expert can quickly summarize the run, extract values at specific iterations, compare iterations, analyze trends, generate plots, and produce basic convergence-style diagnostic notes.

## Current Expert Features

### SU2 History Analysis

| Command                          | Purpose                                             |
| -------------------------------- | --------------------------------------------------- |
| `caseforge history summary`      | Summarize a SU2 history file                        |
| `caseforge history get`          | Extract all values at an exact or nearest iteration |
| `caseforge history diff`         | Compare scalar values between two iterations        |
| `caseforge history trend`        | Analyze one selected field over an iteration range  |
| `caseforge history trend --plot` | Generate a plot for a selected field                |
| `caseforge history diagnose`     | Produce basic engineering-style diagnostic notes    |

### Existing CaseForge Foundation

| Command                    | Purpose                                    |
| -------------------------- | ------------------------------------------ |
| `caseforge create nozzle`  | Generate a starter SU2 nozzle case         |
| `caseforge create generic` | Generate a generic SU2 case structure      |
| `caseforge inspect`        | Inspect SU2 `.cfg` files                   |
| `caseforge validate`       | Validate common SU2 configuration issues   |
| `caseforge explain`        | Explain SU2 config keys in simple language |
| `caseforge monitor`        | Analyze basic residual convergence history |
| `caseforge report`         | Generate a Markdown simulation report      |
| `caseforge doctor`         | Check local setup and case structure       |

## Installation

Clone the repository:

```bash
git clone https://github.com/sahil-elon/caseforge-expert.git
cd caseforge-expert
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

Install CaseForge Expert:

```bash
python -m pip install -e .
```

For development and tests:

```bash
python -m pip install -e ".[dev]"
```

## Quick Start

Check that CaseForge Expert is installed:

```bash
caseforge --help
```

Check the history analysis command group:

```bash
caseforge history --help
```

Summarize a SU2 history file:

```bash
caseforge history summary path/to/history.csv
```

Extract values at a specific iteration:

```bash
caseforge history get path/to/history.csv --iter 25000
```

If the exact iteration is not present, CaseForge Expert uses the nearest available iteration.

Compare two iterations:

```bash
caseforge history diff path/to/history.csv --iter-a 10000 --iter-b 50000
```

Analyze the trend of one field:

```bash
caseforge history trend path/to/history.csv --field CL --from-iter 10000 --to-iter 50000
```

Generate a plot for one field:

```bash
caseforge history trend path/to/history.csv --field CL --from-iter 10000 --to-iter 50000 --plot
```

Run diagnostic notes:

```bash
caseforge history diagnose path/to/history.csv
```

Use a smaller final window for coefficient stability checks:

```bash
caseforge history diagnose path/to/history.csv --final-window 100
```

## Example Expert Workflow

```bash
caseforge history summary history.csv
caseforge history get history.csv --iter 25000
caseforge history diff history.csv --iter-a 10000 --iter-b 50000
caseforge history trend history.csv --field CL --from-iter 10000 --to-iter 50000 --plot
caseforge history diagnose history.csv
```

Generated plot output:

```txt
history_plots/
└── CL_trend.png
```

## Example Basic SU2 Workflow

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

Generate a report:

```bash
caseforge report demo_case
```

Check your local setup:

```bash
caseforge doctor --case-dir demo_case
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

## Current Case Generation Support

CaseForge Expert currently supports starter case generation for nozzle and generic SU2 cases.

| Command                      | Status    |
| ---------------------------- | --------- |
| `caseforge create nozzle`    | Available |
| `caseforge create generic`   | Available |
| `caseforge create airfoil`   | Planned   |
| `caseforge create wedge`     | Planned   |
| `caseforge create flatplate` | Planned   |

## What CaseForge Expert Is Not

CaseForge Expert is not a CFD solver.

It does not replace SU2, Pointwise, ParaView, mesh-quality checks, flow-field visualization, or engineering judgment.

It is a workflow analytics assistant designed to make SU2 case setup, review, convergence inspection, history-file analysis, plotting, and reporting easier.

The diagnostic command analyzes scalar history trends only. Physical correctness still requires mesh review, boundary-condition review, flow visualization, validation, and domain expertise.

## Requirements

* Python 3.10 or newer
* Typer
* Rich
* Jinja2
* Pandas
* Matplotlib

Optional tools:

* SU2 for running simulations
* ParaView or `pvpython` for advanced visualization workflows

CaseForge Expert can still generate, inspect, validate, explain, analyze, and report cases even if SU2 or ParaView is not installed.

## Development

Run tests:

```bash
pytest
```

Run tests with detailed output:

```bash
pytest -v
```

Check CLI locally:

```bash
caseforge --help
caseforge history --help
```

## Roadmap

### History Analysis

* Add multi-field plotting
* Add automatic residual drop-rate analysis
* Add oscillation detection for unstable coefficients
* Add CSV export for iteration comparison results
* Add Markdown/PDF history analysis reports

### SU2 Config Analysis

* Add expert-level config audit
* Add config-to-config comparison
* Add boundary marker consistency checks
* Add solver setting recommendations

### Case Generation

* Add airfoil case generation
* Add supersonic wedge case generation
* Add flat plate boundary-layer case generation
* Add more reusable aerospace CFD templates

### Future Ecosystem

* Add ParaView automation support
* Add Streamlit or web dashboard UI
* Add example CFD cases with real SU2 outputs
* Integrate with future Forge tools for meshing and visualization workflows

## License

This project is licensed under the MIT License.
