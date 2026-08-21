import pytest
from reporting.models.table import Table
from reporting.models.figure import Figure
from reporting.models.section import Section
from reporting.models.report import Report, ReportConfig


def test_table_validation():
    t = Table(headers=["A", "B"], rows=[["1", "2"]])
    assert t.headers == ["A", "B"]

    with pytest.raises(ValueError):
        Table(headers=["A", "B"], rows=[["1"]])

    with pytest.raises(ValueError):
        Table(headers=["A"], rows=[])


def test_section_level_validation():
    with pytest.raises(ValueError):
        Section(title="Test", level=4)


def test_report_creation():
    sec = Section(title="Intro", content=["Hello"])
    report = Report(title="Test Report", author="Me", sections=[sec])
    assert report.title == "Test Report"
