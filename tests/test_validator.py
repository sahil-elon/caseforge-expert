from caseforge.validators import validate_su2_config, config_has_errors


def test_validate_good_su2_config(tmp_path):
    config_file = tmp_path / "case.cfg"

    config_file.write_text(
        """
SOLVER= EULER
MATH_PROBLEM= DIRECT
MESH_FILENAME= nozzle.su2
MESH_FORMAT= SU2
EXT_ITER= 1000
OUTPUT_FILES= (RESTART, PARAVIEW)
MARKER_INLET= ( inlet, 300.0, 500000.0, 1.0, 0.0, 0.0 )
MARKER_OUTLET= ( outlet, 101325.0 )
MARKER_EULER= ( wall )
MARKER_SYM= ( symmetry )
""",
        encoding="utf-8",
    )

    results = validate_su2_config(config_file, case_type="generic")

    assert not config_has_errors(results)

    checks = [item["check"] for item in results]

    assert "SOLVER" in checks
    assert "MESH_FILENAME" in checks
    assert "EXT_ITER value" in checks


def test_validate_missing_file_has_error(tmp_path):
    missing_file = tmp_path / "missing.cfg"

    results = validate_su2_config(missing_file)

    assert config_has_errors(results)
    assert results[0]["status"] == "ERROR"


def test_validate_bad_ext_iter_has_error(tmp_path):
    config_file = tmp_path / "bad.cfg"

    config_file.write_text(
        """
SOLVER= EULER
MATH_PROBLEM= DIRECT
MESH_FILENAME= nozzle.su2
MESH_FORMAT= SU2
EXT_ITER= 0
OUTPUT_FILES= (PARAVIEW)
""",
        encoding="utf-8",
    )

    results = validate_su2_config(config_file)

    assert config_has_errors(results)