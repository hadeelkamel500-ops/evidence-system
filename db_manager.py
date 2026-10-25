from datetime import datetime
import hashlib
import sqlite3

# اسم ملف قاعدة البيانات
DB_NAME = "evidence_system.db"


def calculate_file_hash(file_path):
  """حساب بصمة SHA-256 لأي ملف لضمان سلامته الرقمية"""
  sha256_hash = hashlib.sha256()
  try:
    with open(file_path, "rb") as f:
      for byte_block in iter(lambda: f.read(4096), b""):
        sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
  except Exception:
    return ""


def get_connection():
  """إنشاء اتصال مع قاعدة البيانات"""
  conn = sqlite3.connect(DB_NAME)
  conn.row_factory = sqlite3.Row  # لاسترجاع البيانات بأسماء الأعمدة
  return conn


def init_db():
  """إنشاء الجداول الأساسية بالنظام إذا لم تكن موجودة"""
  conn = get_connection()
  cursor = conn.cursor()

  # جدول الأدلة الرقمية
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidences (
            evidence_id TEXT PRIMARY KEY,
            file_name TEXT NOT NULL,
            file_size_bytes INTEGER NOT NULL,
            original_hash TEXT NOT NULL,
            registered_by TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

  # 2. جدول سجل سلسلة الحيازة (Chain of Custody Log)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS chain_of_custody (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_id TEXT NOT NULL,
            action TEXT NOT NULL,
            performed_by TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL,
            calculated_hash TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (evidence_id) REFERENCES evidences (evidence_id)
        )
    """)

  conn.commit()
  conn.close()


def register_evidence(
    evidence_id, file_name, file_size, file_hash, user_name
):
  """تسجيل دليل رقمي جديد مع إضافته لسلسلة الحيازة تلقائياً"""
  conn = get_connection()
  cursor = conn.cursor()
  now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  try:
    cursor.execute(
        """
            INSERT INTO evidences (evidence_id, file_name, file_size_bytes, original_hash, registered_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
        (evidence_id, file_name, file_size, file_hash, user_name, now),
    )

    cursor.execute(
        """
            INSERT INTO chain_of_custody (evidence_id, action, performed_by, timestamp, status, calculated_hash, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            evidence_id,
            "تسجيل دليل جديد",
            user_name,
            now,
            "سليم / الأصلي",
            file_hash,
            "تم تسجيل الدليل لأول مرة في النظام.",
        ),
    )

    conn.commit()
    return True, "تم تسجيل الدليل بنجاح!"
  except sqlite3.IntegrityError:
    return False, "خطأ: رقم الدليل (ID) موجود مسبقاً، يرجى اختيار رقم آخر."
  except Exception as e:
    return False, f"حدث خطأ غير متوقع: {str(e)}"
  finally:
    conn.close()


def log_verification(
    evidence_id, user_name, current_hash, is_valid, notes=""
):
  """تسجيل عملية فحص سلامة الدليل في سجل الحيازة"""
  conn = get_connection()
  cursor = conn.cursor()
  now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  status = (
      "سليم (لم يتغير)"
      if is_valid
      else "تحذير: تم التعديل/التلاعب بالملف!"
  )
  action = "فحص سلامة الدليل"

  cursor.execute(
      """
        INSERT INTO chain_of_custody (evidence_id, action, performed_by, timestamp, status, calculated_hash, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
      (
          evidence_id,
          action,
          user_name,
          now,
          status,
          current_hash,
          notes,
      ),
  )

  conn.commit()
  conn.close()


def get_evidence(evidence_id):
  """جلب بيانات دليل معين"""
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute(
      "SELECT * FROM evidences WHERE evidence_id = ?", (evidence_id,)
  )
  result = cursor.fetchone()
  conn.close()
  return result


def get_chain_of_custody(evidence_id):
  """جلب كافة السجلات والأحداث لدليل معين مرتبة من الأحدث للأقدم"""
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute(
      "SELECT * FROM chain_of_custody WHERE evidence_id = ? ORDER BY"
      " log_id DESC",
      (evidence_id,),
  )
  results = cursor.fetchall()
  conn.close()
  return results