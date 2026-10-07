import csv
import io
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

from .db import Application

TZ = ZoneInfo("Asia/Tashkent")
HEADERS = [
    "№", "Ism-familiya", "Sinf", "Telefon", "Kunlar", "Bo'sh vaqt", "Username", "Sana"
]


def _rows(apps: list[Application]) -> list[list[str]]:
    return [
        [
            str(i),
            a.full_name,
            a.grade,
            a.phone,
            a.days,
            a.free_time,
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
    for col, width in zip("ABCDEFGH", (6, 32, 8, 18, 30, 30, 22, 18)):
        ws.column_dimensions[col].width = width
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def to_pdf(apps: list[Application]) -> bytes:
    pdfmetrics.registerFont(TTFont("DejaVu", "fonts/DejaVuSans.ttf"))
    style = ParagraphStyle("cell", fontName="DejaVu", fontSize=8, leading=10)

    def p(text: str) -> Paragraph:
        return Paragraph(escape(text), style)

    data = [[p(h) for h in HEADERS]] + [[p(c) for c in row] for row in _rows(apps)]

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        title="Arizalar",
        leftMargin=24,
        rightMargin=24,
        topMargin=24,
        bottomMargin=24,
    )
    table = Table(
        data,
        colWidths=[26, 130, 40, 86, 125, 185, 92, 72],
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    doc.build([table])
    return buf.getvalue()