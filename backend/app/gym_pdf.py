from datetime import date, datetime
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

GYM_MEMBER_LABELS = {"bhumika": "Bhumika", "shyam": "Shyam", "laya": "Laya"}


def with_day(value: date | str | None) -> str:
    if value is None:
        return "-"
    if isinstance(value, str):
        value = datetime.strptime(value, "%Y-%m-%d").date()
    return f"{value.isoformat()} ({value.strftime('%a')})"

HEADER_BG = colors.HexColor("#115e59")
SUBHEADER_BG = colors.HexColor("#0f766e")
ROW_BG = colors.HexColor("#f6f7f9")
LINE_COLOR = colors.HexColor("#dde4ea")


def build_gym_attendance_pdf(
    month_label: str,
    attendance_rows: list[dict[str, Any]],
    cycles_by_member: dict[str, list[dict[str, Any]]],
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        title=f"Gym Attendance Report - {month_label}",
    )
    styles = getSampleStyleSheet()
    elements: list[Any] = []

    elements.append(Paragraph(f"Gym Attendance Report &mdash; {month_label}", styles["Title"]))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Attendance", styles["Heading2"]))
    elements.append(Spacer(1, 4))
    attendance_header = ["Date", "Bhumika", "Shyam", "Laya", "Comments"]
    attendance_table_data = [attendance_header]
    for row in attendance_rows:
        attendance_table_data.append(
            [
                with_day(row["entry_date"]),
                "Yes" if row["bhumika"] else "-",
                "Yes" if row["shyam"] else "-",
                "Yes" if row["laya"] else "-",
                row["comments"] or "-",
            ]
        )
    if len(attendance_table_data) == 1:
        elements.append(Paragraph("No classes attended this month.", styles["Normal"]))
    else:
        attendance_table = Table(attendance_table_data, colWidths=[85, 50, 50, 50, 135], repeatRows=1)
        attendance_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, LINE_COLOR),
                    ("ALIGN", (1, 0), (3, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_BG]),
                ]
            )
        )
        elements.append(attendance_table)

    elements.append(Spacer(1, 18))
    elements.append(Paragraph("Fee Cycles &mdash; 12 classes per cycle, Rs 7,000 per cycle", styles["Heading2"]))
    elements.append(Spacer(1, 6))

    for member, cycles in cycles_by_member.items():
        elements.append(Paragraph(GYM_MEMBER_LABELS.get(member, member.title()), styles["Heading3"]))
        elements.append(Spacer(1, 2))
        if not cycles:
            elements.append(Paragraph("No classes attended yet.", styles["Normal"]))
            elements.append(Spacer(1, 10))
            continue
        cycle_header = ["Cycle", "Classes", "Date Range", "Status", "Fee", "Paid"]
        cycle_table_data = [cycle_header]
        for cycle in cycles:
            class_dates = cycle["class_dates"]
            date_range = f"{with_day(class_dates[0])} to {with_day(class_dates[-1])}" if class_dates else "-"
            status_label = "Complete" if cycle["complete"] else f"In progress ({cycle['count']}/12)"
            if cycle["paid"]:
                paid_label = f"Paid on {with_day(cycle['paid_date'])}" if cycle["paid_date"] else "Paid"
            else:
                paid_label = "Unpaid"
            fee_label = f"Rs {cycle['fee_amount']:.0f}" if cycle["complete"] else "-"
            cycle_table_data.append(
                [str(cycle["cycle_number"]), str(cycle["count"]), date_range, status_label, fee_label, paid_label]
            )
        cycle_table = Table(cycle_table_data, colWidths=[35, 42, 170, 85, 48, 95], repeatRows=1)
        cycle_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), SUBHEADER_BG),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, LINE_COLOR),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_BG]),
                ]
            )
        )
        elements.append(cycle_table)
        elements.append(Spacer(1, 14))

    doc.build(elements)
    return buffer.getvalue()
