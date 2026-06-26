from caseforge.monitor import analyze_history, write_residual_plot


def test_analyze_history_detects_residuals_coefficients_forces_and_moments(tmp_path):
    history_file = tmp_path / "history.csv"

    history_file.write_text(
        """Inner_Iter,RMS_DENSITY,RMS_MOMENTUM-X,RMS_ENERGY,CL,CD,LIFT,DRAG,MOMENT_Z
1,1.0E-1,2.0E-1,3.0E-1,0.10,0.080,10.0,8.0,0.50
2,7.0E-2,1.4E-1,2.1E-1,0.25,0.060,25.0,6.0,0.40
3,4.0E-2,8.0E-2,1.2E-1,0.38,0.045,38.0,4.5,0.35
4,2.0E-2,4.0E-2,6.0E-2,0.45,0.035,45.0,3.5,0.30
5,8.0E-3,1.5E-2,2.5E-2,0.49,0.030,49.0,3.0,0.28
6,3.0E-3,6.0E-3,9.0E-3,0.50,0.028,50.0,2.8,0.26
""",
        encoding="utf-8",
    )

    analysis = analyze_history(history_file)

    assert analysis["ok"] is True
    assert analysis["health"] == "GOOD"
    assert analysis["rows"] == 6
    assert analysis["iteration_column"] == "Inner_Iter"

    assert len(analysis["residuals"]) >= 3
    assert len(analysis["coefficients"]) >= 2
    assert len(analysis["forces"]) >= 2
    assert len(analysis["moments"]) >= 1


def test_write_residual_plot_creates_png(tmp_path):
    history_file = tmp_path / "history.csv"

    history_file.write_text(
        """Inner_Iter,RMS_DENSITY,RMS_ENERGY
1,1.0E-1,3.0E-1
2,7.0E-2,2.1E-1
3,4.0E-2,1.2E-1
4,2.0E-2,6.0E-2
""",
        encoding="utf-8",
    )

    output_path = tmp_path / "residual_plot.png"

    saved_path = write_residual_plot(history_file, output_path)

    assert saved_path.exists()
    assert saved_path.suffix == ".png"