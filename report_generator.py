from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from arabic_reshaper import reshape
from bidi.algorithm import get_display
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors
from io import BytesIO
import os

# تسجيل الخط العربي الذي قمتِ برفعه (تأكدي أن اسم الملف المطابق لما رفعتِيه في المجلد الرئيسي)
FONT_FILE = "ArbFONTS-CairoPlay-SemiBold.ttf"
pdfmetrics.registerFont(TTFont('ArabicFont', FONT_FILE))

def fix_arabic(text):
    """معالجة النص العربي ليظهر بشكل صحيح ومتصل في الـ PDF"""
    if not text:
        return ""
    reshaped_text = reshape(str(text))
    return get_display(reshaped_text)

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

    # تعريف أنماط النصوص بالخط العربي الجديد والمحاذاة الصحيحة لليمين
    arabic_style = ParagraphStyle(
        name="ArabicStyle",
        fontName="ArabicFont",  # استخدام الخط العربي المسجل
        fontSize=11,
        alignment=2,  # محاذاة لليمين
        spaceAfter=6,
    )

    title_style = ParagraphStyle(
        name="TitleStyle",
        fontName="ArabicFont",  # استخدام الخط العربي المسجل
        fontSize=16,
        alignment=1,  # في المنتصف
        spaceAfter=15,
    )

    # عنوان التقرير
    elements.append(
        Paragraph(
            fix_arabic("تقرير فحص وحيازة الدليل الرقمي"), title_style
        )
    )
    elements.append(Spacer(1, 10))

    # بيانات الدليل الأساسية
    elements.append(Paragraph(fix_arabic("--- بيانات الدليل الأساسية ---"), arabic_style))
    elements.append(
        Paragraph(
            fix_arabic(f"رقم الدليل: {evidence_record['evidence_id']}"),
            arabic_style,
        )
    )
    elements.append(
        Paragraph(
            fix_arabic(f"اسم الملف: {evidence_record['file_name']}"),
            arabic_style,
        )
    )
    elements.append(
        Paragraph(
            fix_arabic(f"حجم الملف (بايت): {evidence_record['file_size_bytes']}"),
            arabic_style,
        )
    )
    elements.append(
        Paragraph(
            fix_arabic(f"البصمة الأصلية (SHA-256): {evidence_record['original_hash']}"),
            arabic_style,
        )
    )
    elements.append(
        Paragraph(
            fix_arabic(f"اسم المسجل: {evidence_record['registered_by']}"),
            arabic_style,
        )
    )
    elements.append(
        Paragraph(
            fix_arabic(f"تاريخ التسجيل: {evidence_record['created_at']}"),
            arabic_style,
        )
    )

    elements.append(Spacer(1, 15))
    elements.append(Paragraph(fix_arabic("--- سجل سلسلة الحيازة ---"), arabic_style))

    # جدول سجلات الحيازة (تمت إضافة FONTNAME 'ArabicFont' لكل خلايا الجدول)
    table_data = [[
        fix_arabic("ملاحظات"),
        fix_arabic("الحالة"),
        fix_arabic("المنفذ"),
        fix_arabic("الإجراء"),
        fix_arabic("الوقت"),
    ]]

    for log in chain_logs:
        table_data.append([
            fix_arabic(str(log["notes"] or "")),
            fix_arabic(str(log["status"])),
            fix_arabic(str(log["performed_by"])),
            fix_arabic(str(log["action"])),
            fix_arabic(str(log["timestamp"])),
        ])

    t = Table(table_data, colWidths=[100, 100, 80, 90, 130])
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, -1), "ArabicFont"),  # استخدام الخط العربي للجدول
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ])
    )

    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer
