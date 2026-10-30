import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from arabic_reshaper import reshape
from bidi.algorithm import get_display
from xml.sax.saxutils import escape

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_FILE = os.path.join(BASE_DIR, "IBMPlexSansArabic-Regular.ttf")
pdfmetrics.registerFont(TTFont("ArabicFont", FONT_FILE))


def fix_arabic(text):
    """تشكيل الحروف ثم ترتيب الاتجاه، مع هروب رموز XML."""
    if text is None:
        return ""
    value = str(text).strip()
    if not value:
        return ""
    return get_display(reshape(escape(value)))
from fontTools.ttLib import TTFont as FTFont

_FONT_CMAP = set()
for _table in FTFont(FONT_FILE)["cmap"].tables:
    _FONT_CMAP |= set(_table.cmap.keys())


def assert_font_covers(text):
    missing = sorted({c for c in fix_arabic(text) if ord(c) > 31 and ord(c) not in _FONT_CMAP})
    if missing:
        raise ValueError("أحرف غير موجودة في الخط: " + ", ".join(f"{c} U+{ord(c):04X}" for c in missing))

def generate_evidence_pdf(evidence_record, chain_logs):
    """إنشاء تقرير PDF للدليل وسجل الحيازة الخاص به"""
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

    styles = getSampleStyleSheet()

    arabic_style = ParagraphStyle(
        name="ArabicStyle",
        fontName="ArabicFont",
        fontSize=11,
        leading=17,
        alignment=TA_RIGHT,
        spaceAfter=6,
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
    elements.append(Paragraph(fix_arabic(f"رقم الدليل: {evidence_record['evidence_id']}"), arabic_style))
    elements.append(Paragraph(fix_arabic(f"اسم الملف: {evidence_record['file_name']}"), arabic_style))
    elements.append(Paragraph(fix_arabic(f"حجم الملف (بايت): {evidence_record['file_size_bytes']}"), arabic_style))
    elements.append(Paragraph(fix_arabic(f"البصمة الأصلية (SHA-256): {evidence_record['original_hash']}"), arabic_style))
    elements.append(Paragraph(fix_arabic(f"اسم المسجل: {evidence_record['registered_by']}"), arabic_style))
    elements.append(Paragraph(fix_arabic(f"تاريخ التسجيل: {evidence_record['created_at']}"), arabic_style))

    elements.append(Spacer(1, 15))
    elements.append(Paragraph(fix_arabic("--- سجل سلسلة الحيازة ---"), arabic_style))

    # جدول سجلات الحيازة: العمود الأول (ملاحظات) يظهر في أقصى اليسار، والوقت في أقصى اليمين
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
