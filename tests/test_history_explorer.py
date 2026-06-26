from caseforge.history_explorer import summarize_history


def test_summarize_history_detects_columns(tmp_path):
    history_file = tmp_path / "history.csv"

    history_file.write_text(
        "\n".join(
            [
                "Inner_Iter,RMS_DENSITY,RMS_MOMENTUM-X,RMS_ENERGY,CL,CD,CMz",
                "0,-1.0,-1.1,-1.3,0.100,0.050,-0.010",
                "10000,-3.2,-3.0,-3.3,0.350,0.030,-0.025",
                "50000,-7.8,-7.5,-7.9,0.426,0.018,-0.041",
            ]
        ),
        encoding="utf-8",
    )

    summary = summarize_history(history_file)

    assert summary["rows"] == 3
    assert summary["iteration_column"] == "Inner_Iter"
    assert summary["first_iteration"] == 0
    assert summary["last_iteration"] == 50000

    assert "RMS_DENSITY" in summary["groups"]["residuals"]
    assert "RMS_MOMENTUM-X" in summary["groups"]["residuals"]
    assert "CL" in summary["groups"]["coefficients"]
    assert "CD" in summary["groups"]["coefficients"]
    assert "CMz" in summary["groups"]["coefficients"]

    assert summary["residual_summary"]["RMS_DENSITY"]["start"] == -1.0
    assert summary["residual_summary"]["RMS_DENSITY"]["end"] == -7.8