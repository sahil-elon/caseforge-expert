from caseforge.generator import create_nozzle_case


def test_create_nozzle_case_generates_files(tmp_path):
    output_dir = tmp_path / "nozzle_case"

    created_files = create_nozzle_case(
        output_dir=str(output_dir),
        mesh_file="nozzle.su2",
        inlet_pressure=500000.0,
        outlet_pressure=101325.0,
        temperature=300.0,
        iterations=1000,
    )

    expected_files = [
        output_dir / "case.cfg",
        output_dir / "run.bat",
        output_dir / "run.sh",
        output_dir / "case_info.md",
    ]

    for file_path in expected_files:
        assert file_path.exists()

    assert len(created_files) == 4

    cfg_text = (output_dir / "case.cfg").read_text(encoding="utf-8")

    assert "SOLVER= EULER" in cfg_text
    assert "MESH_FILENAME= nozzle.su2" in cfg_text
    assert "MARKER_INLET" in cfg_text
    assert "MARKER_OUTLET" in cfg_text