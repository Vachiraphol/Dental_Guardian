"""Unit tests สำหรับการตรวจสอบความถูกต้องของข้อมูลและฟอร์ม (Form & Data Validation)

ครอบคลุมหัวข้อที่ 2:
1. การตรวจสอบรหัสซี่ฟันตามระบบ FDI (Permanent 32 ซี่, Primary 20 ซี่, Molars)
2. ฟังก์ชัน tooth_label แปลงรหัสเป็นคำอธิบายภาษาไทยและทิศทางบน/ล่าง/ซ้าย/ขวา
3. พจนานุกรมรหัสโรค ICD-10 และฟังก์ชัน format_entry
4. การตรวจฟอร์มสมัครสมาชิก (AppState.register validation)
   - ข้อมูลที่มี * ว่างเปล่า
   - รหัสผ่านกับการยืนยันไม่ตรงกัน
   - รหัสผ่านสั้นกว่า 8 ตัวอักษร
   - อีเมลซ้ำ
5. การตรวจฟอร์มเข้าสู่ระบบ (AppState.login validation)
   - ไม่กรอกอีเมล/รหัสผ่าน
   - อีเมลหรือรหัสผ่านผิด
   - การจำกัดสิทธิ์ตาม Role (patient vs staff)
6. การจัดการผังฟันและสถานะเด็ก/ผู้ใหญ่ (chart_mode & is_child_case)
"""

from dental_clinic_system.state import (
    AppState,
    tooth_label,
    format_entry,
    ALL_TEETH,
    PERMANENT_TEETH_UPPER,
    PERMANENT_TEETH_LOWER,
    PRIMARY_TEETH_UPPER,
    PRIMARY_TEETH_LOWER,
    MOLARS,
    ICD10_TH,
)


# ===========================================================================
# 1. การตรวจความถูกต้องของรหัสซี่ฟัน (FDI Tooth Codes)
# ===========================================================================

def test_fdi_teeth_count_and_classification():
    """ตรวจสอบว่าจำนวนซี่ฟันในระบบถูกต้องตามมาตรฐานทันตกรรม:

    - ฟันแท้มี 32 ซี่ (บน 16, ล่าง 16)
    - ฟันน้ำนมมี 20 ซี่ (บน 10, ล่าง 10)
    - รวมทั้งหมด 52 ซี่
    """
    assert len(PERMANENT_TEETH_UPPER) == 16
    assert len(PERMANENT_TEETH_LOWER) == 16
    assert len(PRIMARY_TEETH_UPPER) == 10
    assert len(PRIMARY_TEETH_LOWER) == 10
    assert len(ALL_TEETH) == 52

    # ตรวจสอบฟันกราม (MOLARS)
    # ฟันคุด 18, 28, 38, 48 ต้องอยู่ในกลุ่ม Molars
    assert "18" in MOLARS
    assert "48" in MOLARS
    # ฟันหน้า 11, 21 ต้องไม่อยู่ในกลุ่ม Molars
    assert "11" not in MOLARS


def test_tooth_label_permanent_teeth():
    """ทดสอบการสร้างป้ายชื่อซี่ฟันแท้ (Permanent teeth labels):

    - '18' -> ซี่ 18 · ฟันคุด บนขวา
    - '11' -> ซี่ 11 · ฟันหน้าตรงกลาง บนขวา
    - '41' -> ซี่ 41 · ฟันหน้าตรงกลาง ล่างขวา
    """
    label_18 = tooth_label("18")
    assert "18" in label_18
    assert "ฟันคุด" in label_18
    assert "บนขวา" in label_18

    label_11 = tooth_label("11")
    assert "11" in label_11
    assert "ฟันหน้าตรงกลาง" in label_11

    label_41 = tooth_label("41")
    assert "ล่างขวา" in label_41


def test_tooth_label_primary_teeth():
    """ทดสอบการสร้างป้ายชื่อซี่ฟันน้ำนม (Primary teeth labels):

    - '51' -> ซี่ 51 · ฟันหน้าตรงกลาง บนขวา (ฟันน้ำนม)
    - '85' -> ซี่ 85 · ฟันกรามในสุด ล่างขวา (ฟันน้ำนม)
    """
    label_51 = tooth_label("51")
    assert "51" in label_51
    assert "ฟันน้ำนม" in label_51

    label_85 = tooth_label("85")
    assert "85" in label_85
    assert "ฟันกรามในสุด" in label_85
    assert "ฟันน้ำนม" in label_85


def test_tooth_label_fallback_on_invalid():
    """กรณีรหัสซี่ฟันไม่อยู่ในสารบบ ต้องคืนค่าเดิมหรือ '-'"""
    assert tooth_label("99") == "99"
    assert tooth_label("") == "-"


# ===========================================================================
# 2. การตรวจรหัสโรค ICD-10 และ Treatment Entry Formatter
# ===========================================================================

def test_icd10_mapping_and_format_entry():
    """ทดสอบรหัสโรคทางทันตกรรมมาตรฐาน และการแปลงบันทึกการรักษา"""
    assert "K02.1" in ICD10_TH  # ฟันผุถึงชั้นเนื้อฟัน
    assert "K05.1" in ICD10_TH  # เหงือกอักเสบเรื้อรัง

    entry = {
        "id": "E001",
        "patient_id": "P-0001",
        "tooth": "18",
        "icd": "K02.1",
        "procedure": "ถอนฟันคุด",
        "timestamp": "2026-10-31 10:30:00",
    }
    formatted = format_entry(entry)

    assert formatted["icd_th"] == ICD10_TH["K02.1"]
    assert "18" in formatted["tooth_label"]
    assert "2569" in formatted["ts_th"]  # แปลงปีเป็น พ.ศ.


# ===========================================================================
# 3. การตรวจฟอร์มสมัครสมาชิก (AppState.register Validation)
# ===========================================================================

def test_app_state_register_missing_fields(session):
    """ทดสอบกรอกข้อมูลไม่ครบในฟอร์มสมัครสมาชิกหน้าเว็บ"""
    state = AppState()

    # ไม่กรอกชื่อและเบอร์
    state.register({"first_name": "", "email": "test@test.com", "password": "pass"})
    assert "กรุณากรอกข้อมูล" in state.register_error


def test_app_state_register_password_mismatch(session):
    """ทดสอบรหัสผ่านไม่ตรงกันในหน้าเว็บ"""
    state = AppState()
    state.register({
        "first_name": "กมล",
        "last_name": "ศรีสุข",
        "phone": "0812345678",
        "email": "kamol@test.com",
        "password": "password123",
        "confirm": "wrongconfirm",
    })
    assert "ไม่ตรงกัน" in state.register_error


def test_app_state_register_short_password(session):
    """ทดสอบรหัสผ่านสั้นกว่า 8 ตัวในหน้าเว็บ"""
    state = AppState()
    state.register({
        "first_name": "กมล",
        "last_name": "ศรีสุข",
        "phone": "0812345678",
        "email": "kamol@test.com",
        "password": "123",
        "confirm": "123",
    })
    assert "อย่างน้อย 8 ตัวอักษร" in state.register_error


def test_app_state_register_duplicate_email(session):
    """ทดสอบสมัครซ้ำด้วยอีเมลเดิมในหน้าเว็บ"""
    state = AppState()
    form = {
        "first_name": "กมล",
        "last_name": "ศรีสุข",
        "phone": "0812345678",
        "email": "duplicate_state@test.com",
        "password": "password123",
        "confirm": "password123",
    }
    # สมัครครั้งแรก
    state.register(form)
    assert state.register_error == ""

    # สมัครซ้ำ
    state.register(form)
    assert "ถูกใช้งานในระบบแล้ว" in state.register_error


# ===========================================================================
# 4. การตรวจฟอร์มล็อกอิน (AppState.login Validation)
# ===========================================================================

def test_app_state_login_validation(session):
    """ทดสอบ Validation ในการเข้าสู่ระบบ:

    - ไม่กรอกข้อมูล
    - รหัสผ่านผิด
    - ตรวจจับสิทธิ์ไม่ตรงกัน
    """
    state = AppState()

    # 1. ไม่กรอกข้อมูล
    state.login({})
    assert "กรุณากรอกอีเมลและรหัสผ่าน" in state.login_error

    # 2. สมัครบัญชีตัวอย่างเพื่อทดสอบ
    state.register({
        "first_name": "คนไข้",
        "last_name": "ตัวอย่าง",
        "phone": "0898887777",
        "email": "sample_patient@test.com",
        "password": "password123",
        "confirm": "password123",
    })

    # 3. ล็อกอินด้วยรหัสผ่านผิด
    state.login_role = "patient"
    state.login({"email": "sample_patient@test.com", "password": "wrongpassword"})
    assert "ไม่ถูกต้อง" in state.login_error

    # 4. ล็อกอินสำเร็จ
    state.login({"email": "sample_patient@test.com", "password": "password123"})
    assert state.login_error == ""
    assert state.user_name == "คนไข้ ตัวอย่าง"


# ===========================================================================
# 5. การจัดการผังฟันและโหมดฟันเด็ก (Chart Mode & Child Case)
# ===========================================================================

def test_app_state_chart_mode():
    """ทดสอบการสลับโหมดผังฟันระหว่างผู้ใหญ่ (adult) และเด็ก (child)"""
    state = AppState()

    # ค่าเริ่มต้นเป็นโหมดผู้ใหญ่ (16 ซี่บน)
    assert state.chart_mode == "adult"
    assert len(state.active_teeth_upper) == 16
    assert state.active_teeth_upper[0] == "18"

    # สลับเป็นโหมดเด็ก (child -> ฟันน้ำนม 10 ซี่บน)
    state.set_chart_mode("child")
    assert state.chart_mode == "child"
    assert len(state.active_teeth_upper) == 10
    assert state.active_teeth_upper[0] == "55"

    # ทดสอบการเลือกซี่ฟัน
    state.select_tooth("51")
    assert state.selected_tooth == "51"
