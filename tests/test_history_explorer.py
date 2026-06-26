from caseforge.history_explorer import (
    compare_iterations,
    diagnose_history,
    field_trend_summary,
    get_iteration_snapshot,
    summarize_history,
)


def _write_sample_history(tmp_path):
    history_file = tmp_path / "history.csv"

    history_file.write_text(
        "\n".join(
            [
                "Inner_Iter,RMS_DENSITY,RMS_MOMENTUM-X,RMS_ENERGY,CL,CD,CMz",
                "0,-1.0,-1.1,-1.3,0.100,0.050,-0.010",
                "10000,-3.2,-3.0,-3.3,0.350,0.030,-0.025",
                "25000,-5.5,-5.3,-5.6,0.420,0.020,-0.038",
                "50000,-7.8,-7.5,-7.9,0.426,0.018,-0.041",
            ]
        ),
        encoding="utf-8",
    )

    return history_file


def test_summarize_history_detects_columns(tmp_path):
    history_file = _write_sample_history(tmp_path)

    summary = summarize_history(history_file)

    assert summary["rows"] == 4
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


def test_get_iteration_snapshot_exact_iteration(tmp_path):
    history_file = _write_sample_history(tmp_path)

    snapshot = get_iteration_snapshot(history_file, 25000)

    assert snapshot["requested_iteration"] == 25000
    assert snapshot["actual_iteration"] == 25000
    assert snapshot["exact_match"] is True
    assert snapshot["values"]["CL"] == 0.420
    assert snapshot["values"]["CD"] == 0.020


def test_get_iteration_snapshot_nearest_iteration(tmp_path):
    history_file = _write_sample_history(tmp_path)

    snapshot = get_iteration_snapshot(history_file, 26000)

    assert snapshot["requested_iteration"] == 26000
    assert snapshot["actual_iteration"] == 25000
    assert snapshot["exact_match"] is False


def test_compare_iterations(tmp_path):
    history_file = _write_sample_history(tmp_path)

    result = compare_iterations(history_file, 10000, 50000)

    assert result["iteration_a_actual"] == 10000
    assert result["iteration_b_actual"] == 50000

    comparison = result["comparison"]

    assert comparison["CL"]["a"] == 0.350
    assert comparison["CL"]["b"] == 0.426
    assert round(comparison["CL"]["delta"], 6) == 0.076

    assert comparison["CD"]["a"] == 0.030
    assert comparison["CD"]["b"] == 0.018
    assert round(comparison["CD"]["delta"], 6) == -0.012


def test_field_trend_summary(tmp_path):
    history_file = _write_sample_history(tmp_path)

    trend = field_trend_summary(
        history_file,
        field="CL",
        from_iter=10000,
        to_iter=50000,
    )

    assert trend["field"] == "CL"
    assert trend["rows"] == 3
    assert trend["first_iteration"] == 10000
    assert trend["last_iteration"] == 50000
    assert trend["start"] == 0.350
    assert trend["end"] == 0.426
    assert round(trend["delta"], 6) == 0.076


def test_diagnose_history_returns_notes(tmp_path):
    history_file = _write_sample_history(tmp_path)

    diagnosis = diagnose_history(history_file)

    assert diagnosis["rows"] == 4
    assert diagnosis["first_iteration"] == 0
    assert diagnosis["last_iteration"] == 50000
    assert len(diagnosis["notes"]) > 0
    assert any("Residual behavior" in note for note in diagnosis["notes"])
    assert any("Diagnostic note" in note for note in diagnosis["notes"])