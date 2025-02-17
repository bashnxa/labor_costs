from typing import Tuple

from bs4 import BeautifulSoup, Tag

from config import EMPLOYEES, WEEKLY_WORK_HOURS, REMINDER_LIMIT


def extract_last_level_rows(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    time_entry_rows = soup.find_all("tr", class_="last-level")
    return (
        "\n".join(str(row) for row in time_entry_rows)
        if time_entry_rows
        else "Нет данных"
    )


def parse_time_entries(time_entries_html: str) -> dict[str, list[str]]:
    soup: BeautifulSoup = BeautifulSoup(time_entries_html, "html.parser")
    rows = soup.find_all("tr", class_="last-level")
    work_hours: dict[str, list[str]] = {}
    for row in rows:
        if not isinstance(row, Tag):
            continue
        employee_name_td = row.find("td", class_="name")
        if not isinstance(employee_name_td, Tag):
            continue
        employee_name = employee_name_td.get_text(strip=True)
        hours: list[str] = []
        hour_cells = row.find_all("td", class_="hours")
        for cell in hour_cells:
            if not isinstance(cell, Tag):
                continue
            hour_span = cell.find("span", class_="hours-int")
            hours.append(hour_span.get_text(strip=True) if hour_span else "0")
        if employee_name in EMPLOYEES:
            work_hours[employee_name] = hours

    return work_hours


def _generate_report(work_hours: dict[str, list[str]]) -> str:
    report_message: str = "📊 Таблица учета времени:\n\n"
    max_name_length: int = max(len(name) for name in work_hours.keys())
    for name, hours in work_hours.items():
        formatted_hours: str = "|".join(hours[:-1])
        total: str = hours[-1]
        name_padded: str = name.ljust(max_name_length)
        report_message += f"👤 {name_padded}|{formatted_hours} ➡️{total}\n"
    return f"<pre>{report_message}</pre>"


def _find_underworked_employees(work_hours: dict[str, list[str]]) -> list[str]:
    missing_entries: list[str] = []
    for employee_name, hours in work_hours.items():
        total_hours = int(hours[-1]) if hours and hours[-1].isdigit() else 0
        required_hours = (
            WEEKLY_WORK_HOURS
            * REMINDER_LIMIT
            * float(EMPLOYEES.get(employee_name, {}).get("rate", 1.0))
        )
        if total_hours < required_hours:
            missing_entries.append(str(EMPLOYEES[employee_name]["tg"]))
    absent_employees = [name for name in EMPLOYEES if name not in work_hours]
    missing_entries.extend(absent_employees)
    return missing_entries


def format_hours_report(time_entries_html: str) -> Tuple[str, bool]:
    work_hours = parse_time_entries(time_entries_html)
    if not work_hours:
        return "❗ Нет данных о трудозатратах", False
    report_message = _generate_report(work_hours)
    missing_entries = _find_underworked_employees(work_hours)
    missing_message = (
        "\n⏳ Заполните трудовые затраты: " + " ".join(missing_entries)
        if missing_entries
        else "✅ Все сотрудники заполнили трудозатраты"
    )
    return report_message + missing_message, bool(missing_entries)
