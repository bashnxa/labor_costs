import random
import io
from translations import t

import matplotlib.pyplot as plt

from bs4 import BeautifulSoup, Tag

from config import EMPLOYEES, WEEKLY_WORK_HOURS, REMINDER_LIMIT


def extract_last_level_rows(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    time_entry_rows = soup.find_all("tr", class_="last-level")
    return (
        "\n".join(str(row) for row in time_entry_rows)
        if time_entry_rows
        else t("no_data")
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
    report_message: str = ""
    short_names = [name.split()[0] for name in work_hours.keys()]
    max_name_length: int = max(len(name) for name in short_names)
    for name, hours in work_hours.items():
        formatted_hours: str = "|".join(hours[:-1])
        total: str = hours[-1]
        name_padded: str = f"{name.split()[0]:<{max_name_length}}"
        report_message += f"👤 {name_padded}|{formatted_hours} ➡️{total}\n"
    return f"<pre>{report_message}</pre>"


def _find_underworked_employees(work_hours: dict[str, list[str]]) -> list[str]:
    missing_entries: list[str] = []
    variation = random.uniform(0.95, 1.05)  # nosec B311
    for employee_name, hours in work_hours.items():
        total_hours = int(hours[-1]) if hours and hours[-1].isdigit() else 0
        required_hours = (
            WEEKLY_WORK_HOURS
            * REMINDER_LIMIT
            * float(EMPLOYEES.get(employee_name, {}).get("rate", 1.0))
        ) * variation
        if total_hours < required_hours:
            missing_entries.append(str(EMPLOYEES[employee_name]["tg"]))
    absent_employees = [name for name in EMPLOYEES if name not in work_hours]
    missing_entries.extend(absent_employees)
    return missing_entries


def _generate_hours_chart(work_hours: dict[str, list[str]]) -> bytes:
    short_names = [name.split()[0] for name in work_hours.keys()]
    hours = [
        int(hours[-1]) if hours and hours[-1].isdigit() else 0
        for hours in work_hours.values()
    ]
    colors = [
        (
            "mediumpurple"
            if float(EMPLOYEES.get(name, {}).get("rate", 1.0)) < 1
            else "skyblue"
        )
        for name in work_hours.keys()
    ]
    plt.figure(figsize=(5, 3))
    bars = plt.bar(short_names, hours, color=colors, width=0.6)
    plt.axhline(
        y=WEEKLY_WORK_HOURS, color="skyblue", linestyle="--", label=t("weekly_norm")
    )
    plt.axhline(
        y=WEEKLY_WORK_HOURS / 2,
        color="mediumpurple",
        linestyle="--",
        label=t("half_norm"),
    )
    plt.xticks(rotation=30, ha="right", fontsize=9)
    plt.yticks(fontsize=9)
    plt.legend(fontsize=9, loc="lower right", framealpha=0.3)
    for bar, hour in zip(bars, hours):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            str(hour),
            ha="center",
            va="bottom",
            fontsize=9,
        )
    buf = io.BytesIO()
    plt.tight_layout(pad=1)
    plt.savefig(buf, format="png", dpi=100)
    buf.seek(0)
    plt.close()
    return buf.getvalue()


def format_hours_report(time_entries_html: str) -> tuple[str, bytes | None, bool]:
    work_hours = parse_time_entries(time_entries_html)
    if not work_hours:
        return t("no_data"), None, False

    report_message = _generate_report(work_hours)
    missing_entries = _find_underworked_employees(work_hours)
    missing_message = (
        "⏳ " + t("fill_hours") + ": " + ", ".join(missing_entries)
        if missing_entries
        else "✅ " + t("all_filled")
    )
    chart_image = _generate_hours_chart(work_hours)
    return report_message + missing_message, chart_image, bool(missing_entries)
