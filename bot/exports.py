import csv
import io
from zoneinfo import ZoneInfo

from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from .db import Application

TZ = ZoneInfo("Asia/Tashkent")
HEADERS = ["№", "Ism-familiya", "Sinf", "Telefon", "Username", "Sana"]


def _rows(apps: list[Application]) -> list[list[str]]:
    return [
        [
            str(i),
            a.full_name,
            a.grade,
            a.phone,
            f"@{a.username}" if a.username else "",
            a.created_at.astimezone(TZ).strftime("%d.%m.%Y %H:%M"),
        ]
        for i, a in enumerate(apps, 1)
    ]


def to_csv(apps: list[Application]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(HEADERS)
    writer.writerows(_rows(apps))
    return buf.getvalue().encode("utf-8-sig")  # Excel'da to'g'ri ochilishi uchun


def to_xlsx(apps: list[Application]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Arizalar"
    ws.append(HEADERS)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for row in _rows(apps):
        ws.append(row)
    for col, width in zip("ABCDEF", (6, 32, 8, 18, 22, 18)):
        ws.column_dimensions[col].width = width
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def to_pdf(apps: list[Application]) -> bytes:
    pdfmetrics.registerFont(TTFont("DejaVu", "fonts/DejaVuSans.ttf"))
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), title="Arizalar")
    table = Table([HEADERS] + _rows(apps), repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "DejaVu"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    doc.build([table])
    return buf.getvalue()