import os
import streamlit as st
import db_manager as db

# إعدادات الصفحة
st.set_page_config(
    page_title="نظام إدارة الأدلة الرقمية", page_icon="🛡️", layout="wide"
)

# التأكد من إعداد قاعدة البيانات وتحديث الجداول
db.init_db()

# إنشاء مجلد محلي لحفظ الملفات المرفوعة مؤقتاً لحساب بصمتها
UPLOAD_DIR = "uploaded_evidences"
if not os.path.exists(UPLOAD_DIR):
  os.makedirs(UPLOAD_DIR)

st.title("🛡️ نظام إدارة الأدلة الرقمية وسلسلة الحيازة")
st.markdown("---")

# القائمة الجانبية للتنقل بين وظائف التطبيق
menu = [
    "1. تسجيل دليل جديد",
    "2. التحقق من سلامة الدليل",
    "3. سجل سلسلة الحيازة",
]
choice = st.sidebar.selectbox("اختر الخدمة المطلوبة:", menu)

# ----------------------------------------------------
# الوظيفة الأولى: تسجيل دليل جديد
# ----------------------------------------------------
if choice == "1. تسجيل دليل جديد":
  st.header("📝 تسجيل دليل جديد")

  col1, col2 = st.columns(2)
  with col1:
    evidence_id = st.text_input("رقم الدليل (Evidence ID):", placeholder="EV-101")
    user_name = st.text_input(
        "اسم المسجل / المحقق:", placeholder="هديل عبد الله"
    )

  uploaded_file = st.file_uploader(
      "اختر ملف الدليل الرقمي:",
      type=["txt", "pdf", "png", "jpg", "jpeg", "docx"],
  )

  if st.button("حفظ وتجميع البصمة"):
    if not evidence_id or not user_name or uploaded_file is None:
      st.warning("⚠️ يرجى تعبئة جميع الحقول ورفع ملف الدليل.")
    else:
      # حفظ الملف المرفوع في مجلد النظام
      file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
      with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

      # حساب البصمة الرقمية SHA-256 للملف
      file_hash = db.calculate_file_hash(file_path)
      file_size = os.path.getsize(file_path)

      # حفظ البيانات في قاعدة البيانات
      success, message = db.register_evidence(
          evidence_id, uploaded_file.name, file_size, file_hash, user_name
      )

      if success:
        st.success(message)
        st.info(f"🔑 البصمة الرقمية (SHA-256): {file_hash}")
      else:
        st.error(message)

# ----------------------------------------------------
# الوظيفة الثانية: التحقق من سلامة الدليل
# ----------------------------------------------------
elif choice == "2. التحقق من سلامة الدليل":
  st.header("🔍 فحص والتحقق من سلامة الدليل الرقمي")

  evidence_id = st.text_input("أدخل رقم الدليل المراد فحصه:")
  checker_name = st.text_input(
      "اسم الفاحص:", placeholder="المحقق المسؤول"
  )
  check_file = st.file_uploader("رفع الملف المراد فحصه ومطابقته:")

  if st.button("فحص السلامة"):
    if not evidence_id or not checker_name or check_file is None:
      st.warning("⚠️ يرجى إدخال جميع البيانات ورفع الملف.")
    else:
      # جلب البيانات الأصلية للدليل من قاعدة البيانات
      record = db.get_evidence(evidence_id)

      if record is None:
        st.error("❌ لم يتم العثور على دليل بهذا الرقم!")
      else:
        # حفظ الملف المرفوع مؤقتاً للقيام بجمعه وحسابه
        temp_path = os.path.join(UPLOAD_DIR, f"check_{check_file.name}")
        with open(temp_path, "wb") as f:
          f.write(check_file.getbuffer())

        # حساب البصمة الحالية للملف المرفوع
        current_hash = db.calculate_file_hash(temp_path)
        original_hash = record["original_hash"]

        # إزالة الملف المؤقت
        if os.path.exists(temp_path):
          os.remove(temp_path)

        # مقارنة البصمات
        is_valid = current_hash == original_hash

        # تسجيل النتيجة في سجل الحيازة
        db.log_verification(
            evidence_id,
            checker_name,
            current_hash,
            is_valid,
            "تم إجراء الفحص عبر الواجهة.",
        )

        st.subheader("نتائج الفحص:")
        st.write(f"**البصمة الأصلية المسجلة:** `{original_hash}`")
        st.write(f"**البصمة الحالية للملف:** `{current_hash}`")

        if is_valid:
          st.balloons()
          st.success("✅ الدليل سليم ولم يتعرض لأي تعديل!")
        else:
          st.error(
              "⚠️ تحذير: البصمات غير متطابقة! الملف تم التعديل عليه أو تالف."
          )

# ----------------------------------------------------
# الوظيفة الثالثة: سجل سلسلة الحيازة
# ----------------------------------------------------
# ----------------------------------------------------
# الوظيفة الثالثة: سجل سلسلة الحيازة والتقارير
# ----------------------------------------------------
elif choice == "3. سجل سلسلة الحيازة":
  st.header("📜 سجل سلسلة الحيازة وتصدير التقارير")

  search_id = st.text_input("أدخل رقم الدليل لعرض سجله وتصدير التقرير:")

  if st.button("بحث وعرض السجل"):
    if search_id:
      evidence = db.get_evidence(search_id)
      if evidence:
        st.subheader(f"بيانات الدليل: {evidence['file_name']}")
        st.json(dict(evidence))

        st.subheader("سجل الإجراءات والفحوصات:")
        logs = db.get_chain_of_custody(search_id)
        if logs:
          st.table([dict(log) for log in logs])

          # زر تحميل تقرير الـ PDF
          import report_generator

          pdf_buffer = report_generator.generate_evidence_pdf(
              evidence, [dict(l) for l in logs]
          )

          st.download_button(
              label="📥 تحميل التقرير الرسمي (PDF)",
              data=pdf_buffer,
              file_name=f"Evidence_Report_{search_id}.pdf",
              mime="application/pdf",
          )
        else:
          st.info("لا توجد سجلات مسجلة لهذا الدليل حتى الآن.")
      else:
        st.error("رقم الدليل غير موجود.")