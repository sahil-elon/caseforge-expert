from caseforge.config_explainer import explain_su2_config, write_explanation_markdown


def test_explain_su2_config(tmp_path):
    config_file = tmp_path / "case.cfg"

    config_file.write_text(
        """
SOLVER= EULER
MATH_PROBLEM= DIRECT
MESH_FILENAME= nozzle.su2
EXT_ITER= 1000
""",
        encoding="utf-8",
    )

    explanations = explain_su2_config(config_file)

    keys = [item["key"] for item in explanations]

    assert "SOLVER" in keys
    assert "MATH_PROBLEM" in keys
    assert "MESH_FILENAME" in keys


def test_write_explanation_markdown(tmp_path):
    output_file = tmp_path / "config_explanation.md"

    explanations = [
        {
            "key": "SOLVER",
            "value": "EULER",
            "simple": "Tells SU2 what physics to solve.",
            "detail": "Euler means inviscid flow.",
        }
    ]

    saved_path = write_explanation_markdown(explanations, output_file)

    assert saved_path.exists()

    text = saved_path.read_text(encoding="utf-8")

    assert "# SU2 Config Explanation" in text
    assert "SOLVER" in text
    assert "EULER" in text