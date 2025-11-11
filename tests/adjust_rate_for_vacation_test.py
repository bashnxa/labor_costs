import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from parser import _adjust_rate_for_vacation


@pytest.fixture
def mock_employee():
    """Фикстура для создания тестового сотрудника"""

    def _make_employee(rate, vacation_start=None, vacation_end=None):
        class Employee:
            def __init__(self, rate, vacation_range):
                self.rate = rate
                self.vacation_range = vacation_range

        vacation_range = (
            [vacation_start, vacation_end] if vacation_start and vacation_end else None
        )
        return Employee(rate, vacation_range)

    return _make_employee


class TestEmployee:
    def __init__(self, rate, vacation_range=None):
        self.rate = rate
        self.vacation_range = vacation_range


class TestAdjustRateForVacation:
    @patch("parser.get_employee_data")
    def test_employee_not_found(self, mock_get_employee):
        """Тест когда сотрудник не найден"""
        mock_get_employee.return_value = None
        result = _adjust_rate_for_vacation("Unknown", 30)
        assert result == 1.0

    @patch("parser.get_employee_data")
    def test_no_vacation_range(self, mock_get_employee):
        """Тест когда у сотрудника нет диапазона отпуска"""
        employee = TestEmployee(rate=1000.0, vacation_range=None)
        mock_get_employee.return_value = employee
        result = _adjust_rate_for_vacation("Employee1", 30)
        assert result == 1000.0

    @patch("parser.get_employee_data")
    def test_empty_vacation_range(self, mock_get_employee):
        """Тест когда диапазон отпуска пустой"""
        employee = TestEmployee(rate=1000.0, vacation_range=[])
        mock_get_employee.return_value = employee
        result = _adjust_rate_for_vacation("Employee1", 30)
        assert result == 1000.0

    @patch("parser.get_employee_data")
    def test_vacation_no_overlap(self, mock_get_employee):
        """Тест когда отпуск не пересекается с отчетным периодом"""
        today = datetime.today().date()
        report_days = 30
        report_start = today - timedelta(days=report_days - 1)

        # Отпуск до отчетного периода
        vacation_start = report_start - timedelta(days=10)
        vacation_end = report_start - timedelta(days=1)

        employee = TestEmployee(
            rate=1000.0, vacation_range=[vacation_start, vacation_end]
        )
        mock_get_employee.return_value = employee

        result = _adjust_rate_for_vacation("Employee1", report_days)
        assert result == 1000.0

    @patch("parser.get_employee_data")
    def test_vacation_full_overlap(self, mock_get_employee):
        """Тест когда отпуск полностью покрывает отчетный период"""
        today = datetime.today().date()
        report_days = 30
        report_start = today - timedelta(days=report_days - 1)

        employee = TestEmployee(rate=1000.0, vacation_range=[report_start, today])
        mock_get_employee.return_value = employee

        result = _adjust_rate_for_vacation("Employee1", report_days)

        # Должна быть применена минимальная ставка
        total_workdays = sum(
            1
            for i in range(report_days)
            if (report_start + timedelta(days=i)).weekday() < 5
        )
        expected_rate = 1000.0 * (1 / total_workdays)
        assert result == expected_rate

    @patch("parser.get_employee_data")
    def test_vacation_partial_overlap(self, mock_get_employee):
        """Тест когда отпуск частично пересекается с отчетным периодом"""
        today = datetime.today().date()
        report_days = 10
        report_start = today - timedelta(days=report_days - 1)

        # Отпуск на 3 рабочих дня в середине периода
        vacation_start = report_start + timedelta(days=2)
        vacation_end = report_start + timedelta(days=6)

        employee = TestEmployee(
            rate=1000.0, vacation_range=[vacation_start, vacation_end]
        )
        mock_get_employee.return_value = employee

        result = _adjust_rate_for_vacation("Employee1", report_days)

        # Проверяем что результат меньше исходной ставки
        assert result < 1000.0
        assert result > 0

    @patch("parser.get_employee_data")
    def test_single_day_report_period(self, mock_get_employee):
        """Тест для отчетного периода в один день"""
        today = datetime.today().date()

        employee = TestEmployee(rate=1000.0, vacation_range=[today, today])
        mock_get_employee.return_value = employee

        result = _adjust_rate_for_vacation("Employee1", 1)

        # Если это рабочий день и он в отпуске
        if today.weekday() < 5:
            expected_rate = 1000.0 * (1 / 1)  # Минимальная ставка
        else:
            expected_rate = 1000.0  # Выходной - ставка не меняется

        assert result == expected_rate

    @patch("parser.get_employee_data")
    def test_rate_zero(self, mock_get_employee):
        """Тест с нулевой ставкой"""
        employee = TestEmployee(rate=0.0, vacation_range=None)
        mock_get_employee.return_value = employee
        result = _adjust_rate_for_vacation("Employee1", 30)
        assert result == 0.0


# Дополнительные параметризованные тесты для граничных случаев
@pytest.mark.parametrize(
    "rate,vacation_days,expected_change",
    [
        (1000.0, 0, False),  # Нет отпуска - ставка не меняется
        (1000.0, 5, True),  # 5 дней отпуска - ставка должна уменьшиться
        (500.0, 10, True),  # 10 дней отпуска - ставка должна уменьшиться
    ],
)
@patch("parser.get_employee_data")
def test_vacation_effect_on_rate(
    mock_get_employee, rate, vacation_days, expected_change
):
    """Параметризованный тест влияния отпуска на ставку"""
    today = datetime.today().date()
    report_days = 30
    report_start = today - timedelta(days=report_days - 1)

    # Создаем отпуск указанной продолжительности
    vacation_start = report_start
    vacation_end = report_start + timedelta(days=vacation_days - 1)

    employee = TestEmployee(rate=rate, vacation_range=[vacation_start, vacation_end])
    mock_get_employee.return_value = employee

    result = _adjust_rate_for_vacation("Employee1", report_days)

    if expected_change:
        assert result < rate
    else:
        assert result == rate
