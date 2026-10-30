import os
from io import BytesIO
from xml.sax.saxutils import escape

from arabic_reshaper import reshape
from bidi.algorithm import get_display
from fontTools.ttLib import TTFont as FTFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_FILE = os.path.join(BASE_DIR, "IBMPlexSansArabic-Regular.ttf")

pdfmetrics.registerFont(TTFont("ArabicFont", FONT_FILE))


def fix_arabic(text):
    """تشكيل الحروف ثم ترتيب الاتجاه، ثم هروب رموز XML (بهذا الترتيب)."""
    if text is None:
        return ""
    value = str(text).strip()
    if not value:
        return ""
    return escape(get_display(reshape(value)))


# الحروف المدعومة في الخط
_FONT_CMAP = set()
for _table in FTFont(FONT_FILE)["cmap"].tables:
    _FONT_CMAP |= set(_table.cmap.keys())


def assert_font_covers(text):
    shaped = get_display(reshape(str(text)))
    missing = sorted({c for c in shaped if ord(c) > 31 and ord(c) not in _FONT_CMAP})
    if missing:
        raise ValueError(
            "أحرف غير موجودة في الخط: " + ", ".join(f"{c} U+{ord(c):04X}" for c in missing)
        )


def generate_evidence_pdf(evidence_record, chain_logs):
    """إنشاء تقرير PDF للدليل وسجل الحيازة الخاص به"""
    # تحويل sqlite3.Row (أو أي كائن مشابه) إلى dict حتى يعمل .get()
    evidence_record = dict(evidence_record)
    chain_logs = [dict(log) for log in chain_logs]

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )

    elements = []

    arabic_style = ParagraphStyle(
        name="ArabicStyle",
        fontName="ArabicFont",
        fontSize=11,
        leading=17,
        alignment=TA_RIGHT,
        spaceAfter=6,
        wordWrap="CJK",  # لكسر النصوص الطويلة مثل البصمة
    )

    title_style = ParagraphStyle(
        name="TitleStyle",
        fontName="ArabicFont",
        fontSize=16,
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=15,
    )

    cell_style = ParagraphStyle(
        name="CellStyle",
        fontName="ArabicFont",
        fontSize=8,
        leading=11,
        alignment=TA_RIGHT,
        wordWrap="CJK",
    )

    head_cell_style = ParagraphStyle(
        name="HeadCellStyle",
        parent=cell_style,
        fontSize=9,
        leading=12,
    )

    def cell(value, style=cell_style):
        return Paragraph(fix_arabic(value), style)

    # عنوان التقرير
    elements.append(Paragraph(fix_arabic("تقرير فحص وحيازة الدليل الرقمي"), title_style))
    elements.append(Spacer(1, 10))

    # بيانات الدليل الأساسية
    elements.append(Paragraph(fix_arabic("--- بيانات الدليل الأساسية ---"), arabic_style))
    elements.append(Paragraph(fix_arabic(f"رقم الدليل: {evidence_record.get('evidence_id', '')}"), arabic_style))
    elements.append(Paragraph(fix_arabic(f"اسم الملف: {evidence_record.get('file_name', '')}"), arabic_style))
    elements.append(Paragraph(fix_arabic(f"حجم الملف (بايت): {evidence_record.get('file_size_bytes', '')}"), arabic_style))
    elements.append(Paragraph(fix_arabic(f"البصمة الأصلية (SHA-256): {evidence_record.get('original_hash', '')}"), arabic_style))
    elements.append(Paragraph(fix_arabic(f"اسم المسجل: {evidence_record.get('registered_by', '')}"), arabic_style))
    elements.append(Paragraph(fix_arabic(f"تاريخ التسجيل: {evidence_record.get('created_at', '')}"), arabic_style))

    elements.append(Spacer(1, 15))
    elements.append(Paragraph(fix_arabic("--- سجل سلسلة الحيازة ---"), arabic_style))

    # العمود الأول (ملاحظات) في أقصى اليسار، والوقت في أقصى اليمين
    table_data = [[
        cell("ملاحظات", head_cell_style),
        cell("الحالة", head_cell_style),
        cell("المنفذ", head_cell_style),
        cell("الإجراء", head_cell_style),
        cell("الوقت", head_cell_style),
    ]]

    for log in chain_logs:
        table_data.append([
            cell(log.get("notes") or ""),
            cell(log.get("status") or ""),
            cell(log.get("performed_by") or ""),
            cell(log.get("action") or ""),
            cell(log.get("timestamp") or ""),
        ])

    t = Table(table_data, colWidths=[150, 80, 90, 100, 110], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, -1), "ArabicFont"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.7, colors.black),
    ]))

    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer

