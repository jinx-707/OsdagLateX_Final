import pytest
from reporting.utils.escaping import escape_latex


def test_escape_latex_individual_chars():
    """Test each special character individually."""
    special_chars = {
        '\\': r'\textbackslash{}',
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
    }
    for raw, expected in special_chars.items():
        assert escape_latex(raw) == expected


def test_escape_latex_combined_string():
    raw = 'M20_Grade & Plate #3 (cost: 50%)'
    expected = r'M20\_Grade \& Plate \#3 (cost: 50\%)'
    assert escape_latex(raw) == expected


def test_escape_latex_empty_string():
    assert escape_latex('') == ''


def test_escape_latex_no_special_chars():
    raw = 'Hello world 123'
    assert escape_latex(raw) == raw


def test_escape_latex_none_raises():
    with pytest.raises(TypeError, match="expects a string, got None"):
        escape_latex(None)


def test_escape_latex_double_escape_visible():
    """
    Double-escaping should produce visibly different output (idempotency not expected).
    This guards against accidentally calling escape twice.
    """
    raw = '&'
    single = escape_latex(raw)
    double = escape_latex(single)
    assert single != double
