from caseforge.config_inspector import inspect_su2_config


def test_inspect_nozzle_like_config(tmp_path):
    config_file = tmp_path / "case.cfg"

    config_file.write_text(
        """
SOLVER= EULER
MATH_PROBLEM= DIRECT
MESH_FILENAME= nozzle.su2
MESH_FORMAT= SU2
EXT_ITER= 1000
CFL_NUMBER= 1.0
OUTPUT_FILES= (RESTART, PARAVIEW)
MARKER_INLET= ( inlet, 300.0, 500000.0, 1.0, 0.0, 0.0 )
MARKER_OUTLET= ( outlet, 101325.0 )
MARKER_EULER= ( wall )
MARKER_SYM= ( symmetry )
""",
        encoding="utf-8",
    )

    summary = inspect_su2_config(config_file)

    assert summary["ok"] is True
    assert summary["solver"] == "EULER"
    assert summary["mesh_filename"] == "nozzle.su2"
    assert summary["iterations"] == "1000"
    assert summary["likely_case_type"] == "Internal flow / nozzle-like case"
    assert "MARKER_INLET" in summary["marker_keys"]
    assert "inlet" in summary["marker_names"]