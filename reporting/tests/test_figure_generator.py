import os
import pytest
from reporting.models.figure import Figure
from reporting.generators.figure_generator import generate_figure_latex


def test_figure_generator_missing_file():
    fig = Figure(path="nonexistent.png")
    with pytest.raises(FileNotFoundError):
        generate_figure_latex(fig)


def test_figure_generator_valid(tmp_path):
    img_path = tmp_path / "test.png"
    img_path.write_text("dummy")
    fig = Figure(path=str(img_path), caption="Test", label="fig:test")
    latex = generate_figure_latex(fig)
    assert r"\includegraphics" in latex
    assert "test.png" in latex
    assert "Test" in latex
    assert "fig:test" in latex
