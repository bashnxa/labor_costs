from datetime import date

import pytest
from parser import (
    extract_last_level_rows,
    parse_time_entries,
    _adjust_rate_for_vacation,
    _is_employee_on_full_vacation,
    _find_underworked_employees,
    _generate_report,
)
from config import EMPLOYEES
from schema import EmployeeData


@pytest.fixture
def sample_html():
    return """
    <table>
        <tr class="last-level">
            <td class="name">Alice Smith</td>
            <td class="hours"><span class="hours-int">2</span></td>
            <td class="hours"><span class="hours-int">3</span></td>
            <td class="hours"><span class="hours-int">5</span></td>
        </tr>
    </table>
    """


def test_extract_last_level_rows(sample_html):
    result = extract_last_level_rows(sample_html)
    assert '<tr class="last-level">' in result


def test_parse_time_entries(sample_html):
    EMPLOYEES["Alice Smith"] = {"rate": 1.0}
    result = parse_time_entries(sample_html)
    assert "Alice Smith" in result
    assert result["Alice Smith"] == ["2", "3", "5"]


def test_adjust_rate_for_vacation_no_vacation():
    EMPLOYEES["Test"] = {"rate": 1.0}
    rate = _adjust_rate_for_vacation("Test", 7)
    assert rate == 1.0


def test_is_employee_on_full_vacation():
    EMPLOYEES["Carol"] = EmployeeData(
        tg="", rate=1, vacation_range=[date(2024, 1, 1), date(2100, 1, 1)]
    )
    result = _is_employee_on_full_vacation("Carol", 3)
    assert result is True


def test_generate_report_format():
    hours_data = {"Alice Smith": ["2", "3", "10"]}
    report = _generate_report(hours_data, 3)
    assert "Alice" in report
    assert "10" in report


def test_find_underworked_employee(monkeypatch):
    EMPLOYEES["Eve"] = EmployeeData(tg="@eve", rate=1.0)
    monkeypatch.setattr("parser.random.uniform", lambda *args, **kwargs: 1.0)
    monkeypatch.setattr("parser._is_employee_on_full_vacation", lambda *a, **kw: False)
    hours_data = {"Eve": ["1", "2", "3", "4", "5", "6", "10"]}
    result = _find_underworked_employees(hours_data, 7)
    assert "@eve" in result
