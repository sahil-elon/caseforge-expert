from caseforge.generator import create_generic_case


def test_create_generic_case_generates_files(tmp_path):
    output_dir = tmp_path / "generic_case"

    created_files = create_generic_case(
        output_dir=str(output_dir),
        mesh_file="mesh.su2",
        solver="EULER",
        iterations=500,
        cfl=1.0,
        wall_marker="wall",
        farfield_marker="farfield",
        freestream_pressure=101325.0,
        freestream_temperature=300.0,
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
    assert "MESH_FILENAME= mesh.su2" in cfg_text
    assert "MARKER_EULER= ( wall )" in cfg_text
    assert "MARKER_FAR= ( farfield )" in cfg_text