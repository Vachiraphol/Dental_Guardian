"""Unit tests สำหรับ API การยืนยันตัวตนและข้อมูลคนไข้ (api_auth.py)

ทดสอบ:
1. SRS 5.2 - User Authentication & Member:
   - การลงทะเบียนผู้ป่วยใหม่ (register)
   - กรณีฟิลด์สำคัญว่างเปล่า
   - กรณีรหัสผ่านไม่ตรงกัน หรือสั้นเกินไป
   - กรณีอีเมลซ้ำในระบบ
   - การเข้าสู่ระบบ (login) แบบผู้ป่วย และเจ้าหน้าที่
   - กรณีรหัสผ่านผิด หรือเลือก Role ไม่ตรงกับสิทธิ์
   - การเปลี่ยนรหัสผ่าน (change-password) ทั้งกรณีสำเร็จและกรณีผิดพลาด
   - การขอ OTP รีเซ็ตรหัสผ่าน และการยืนยันรหัสผ่านใหม่
2. SRS 5.1 - Patient Records:
   - การสร้างเวชระเบียนผู้ป่วยใหม่
   - การค้นหาคนไข้ตามรหัส HN
   - การค้นหาคนไข้แบบ Filter Search (ชื่อ/เบอร์/HN)
   - กรณีค้นหาไม่พบ (404 Not Found)
   - การแก้ไขข้อมูลเวชระเบียน (update_patient_record) ทั้งสำเร็จและกรณี 404
"""

import pytest
from fastapi import HTTPException
from dental_clinic_system.backend.api_auth import (
    register_user,
    login_user,
    change_password,
    request_password_reset,
    confirm_password_reset,
    create_patient_record,
    get_patient_by_hn,
    list_all_patients,
    update_patient_record,
    RegisterRequest,
    LoginRequest,
    ChangePasswordRequest,
    RequestResetRequest,
    ConfirmResetRequest,
    PatientCreateRequest,
    PatientUpdateRequest,
)
from dental_clinic_system.backend.models import User, Patient
from sqlmodel import select


def test_register_user_success(session):
    """ทดสอบกรณีสมัครสมาชิกสำเร็จ:

    - ต้องบันทึกทั้งตาราง User และ Patient
    - ต้องออกรหัส HN ในรูปแบบ P-0001
    """
    payload = RegisterRequest(
        first_name="สมชาย",
        last_name="ใจดี",
        phone="0812345678",
        email="somchai@example.com",
        password="password123",
        confirm="password123",
        gender="ชาย",
        dob="1995-05-20",
    )

    response = register_user(payload)

    # 1. ตรวจสอบ response ว่าสำเร็จและได้ HN Code
    assert response["message"] == "สมัครสมาชิกสำเร็จ"
    assert response["hn_code"] == "P-0001"
    assert response["user_id"] is not None

    # 2. ตรวจสอบข้อมูลในฐานข้อมูล
    user = session.exec(select(User).where(User.username == "somchai@example.com")).first()
    assert user is not None
    assert user.full_name == "สมชาย ใจดี"
    assert user.role == "patient"

    patient = session.exec(select(Patient).where(Patient.hn_code == "P-0001")).first()
    assert patient is not None
    assert patient.phone_number == "0812345678"
    assert patient.gender == "ชาย"


def test_register_user_empty_fields(session):
    """ทดสอบกรณีข้อมูลสำคัญเว้นว่าง ต้องเกิด HTTP 400"""
    payload = RegisterRequest(
        first_name="",  # ว่าง
        last_name="ใจดี",
        phone="0812345678",
        email="empty@example.com",
        password="password123",
        confirm="password123",
    )
    with pytest.raises(HTTPException) as exc_info:
        register_user(payload)
    assert exc_info.value.status_code == 400
    assert "ครบถ้วน" in exc_info.value.detail


def test_register_user_password_mismatch(session):
    """ทดสอบกรณีรหัสผ่านกับการยืนยันรหัสผ่านไม่ตรงกัน ต้องเกิด HTTP 400"""
    payload = RegisterRequest(
        first_name="สมหญิง",
        last_name="รักเรียน",
        phone="0899999999",
        email="somying@example.com",
        password="password123",
        confirm="wrongpass123",  # ไม่ตรงกัน
    )

    with pytest.raises(HTTPException) as exc_info:
        register_user(payload)

    assert exc_info.value.status_code == 400
    assert "ไม่ตรงกัน" in exc_info.value.detail


def test_register_user_password_too_short(session):
    """ทดสอบกรณีรหัสผ่านสั้นกว่า 8 ตัวอักษร ต้องเกิด HTTP 400"""
    payload = RegisterRequest(
        first_name="สมหญิง",
        last_name="รักเรียน",
        phone="0899999999",
        email="short@example.com",
        password="123",  # สั้นเกินไป (< 8 ตัว)
        confirm="123",
    )

    with pytest.raises(HTTPException) as exc_info:
        register_user(payload)

    assert exc_info.value.status_code == 400
    assert "8 ตัวอักษร" in exc_info.value.detail


def test_register_user_duplicate_email(session):
    """ทดสอบกรณีอีเมลซ้ำกับที่มีอยู่แล้วในระบบ ต้องเกิด HTTP 400"""
    payload = RegisterRequest(
        first_name="ผู้ใช้",
        last_name="คนแรก",
        phone="0811111111",
        email="duplicate@example.com",
        password="password123",
        confirm="password123",
    )
    register_user(payload)  # สมัครครั้งแรก

    # พยายามสมัครซ้ำด้วยอีเมลเดิม
    with pytest.raises(HTTPException) as exc_info:
        register_user(payload)

    assert exc_info.value.status_code == 400
    assert "ถูกใช้งานในระบบแล้ว" in exc_info.value.detail


def test_login_user_patient_success(session):
    """ทดสอบเข้าสู่ระบบฝั่งคนไข้สำเร็จ พร้อมตรวจข้อมูลผู้ป่วยที่ส่งกลับมา"""
    register_user(RegisterRequest(
        first_name="วีระ",
        last_name="กล้าหาญ",
        phone="0855555555",
        email="weera@example.com",
        password="mysecretpassword",
        confirm="mysecretpassword",
    ))

    login_payload = LoginRequest(
        username="weera@example.com",
        password="mysecretpassword",
        role="patient",
    )
    res = login_user(login_payload)

    assert res["message"] == "เข้าสู่ระบบสำเร็จ"
    assert res["user"]["username"] == "weera@example.com"
    assert res["patient"] is not None
    assert res["patient"]["hn_code"] == "P-0001"


def test_login_user_wrong_password(session):
    """ทดสอบเข้าสู่ระบบแต่ใส่รหัสผ่านผิด ต้องเกิด HTTP 401 Unauthorized"""
    register_user(RegisterRequest(
        first_name="อนันต์",
        last_name="มั่งมี",
        phone="0844444444",
        email="anan@example.com",
        password="correctpassword",
        confirm="correctpassword",
    ))

    login_payload = LoginRequest(
        username="anan@example.com",
        password="wrongpassword",  # รหัสผ่านผิด
        role="patient",
    )
    with pytest.raises(HTTPException) as exc_info:
        login_user(login_payload)

    assert exc_info.value.status_code == 401
    assert "ไม่ถูกต้อง" in exc_info.value.detail


def test_login_user_role_mismatch(session):
    """ทดสอบบัญชีผู้ป่วยพยายามล็อกอินเข้าส่วนของทันตแพทย์/เจ้าหน้าที่ (staff)

    ต้องถูกปฏิเสธด้วย HTTP 403 Forbidden
    """
    register_user(RegisterRequest(
        first_name="คนไข้",
        last_name="ทั่วไป",
        phone="0833333333",
        email="patient_only@example.com",
        password="password123",
        confirm="password123",
    ))

    login_payload = LoginRequest(
        username="patient_only@example.com",
        password="password123",
        role="staff",
    )
    with pytest.raises(HTTPException) as exc_info:
        login_user(login_payload)

    assert exc_info.value.status_code == 403
    assert "ไม่มีสิทธิ์" in exc_info.value.detail


def test_change_password_success_and_errors(session):
    """ทดสอบการเปลี่ยนรหัสผ่าน ทั้งกรณีสำเร็จและกรณีข้อผิดพลาดต่าง ๆ:

    - รหัสใหม่สั้นกว่า 8 ตัว
    - รหัสใหม่กับยืนยันไม่ตรงกัน
    - รหัสใหม่ซ้ำกับรหัสเดิม
    - รหัสเดิมไม่ถูกต้อง
    - เปลี่ยนสำเร็จ
    """
    email = "changepw@example.com"
    register_user(RegisterRequest(
        first_name="ทดสอบ",
        last_name="เปลี่ยนรหัส",
        phone="0822222222",
        email=email,
        password="oldpassword123",
        confirm="oldpassword123",
    ))

    # 1. รหัสใหม่สั้นกว่า 8 ตัว
    with pytest.raises(HTTPException) as e1:
        change_password(ChangePasswordRequest(
            email=email,
            current_password="oldpassword123",
            new_password="short",
            confirm_password="short",
        ))
    assert e1.value.status_code == 400

    # 2. รหัสใหม่กับยืนยันไม่ตรงกัน
    with pytest.raises(HTTPException) as e2:
        change_password(ChangePasswordRequest(
            email=email,
            current_password="oldpassword123",
            new_password="newpassword123",
            confirm_password="mismatchpassword",
        ))
    assert e2.value.status_code == 400

    # 3. รหัสใหม่ซ้ำกับรหัสเดิม
    with pytest.raises(HTTPException) as e3:
        change_password(ChangePasswordRequest(
            email=email,
            current_password="oldpassword123",
            new_password="oldpassword123",
            confirm_password="oldpassword123",
        ))
    assert e3.value.status_code == 400

    # 4. รหัสเดิมไม่ถูกต้อง
    with pytest.raises(HTTPException) as e4:
        change_password(ChangePasswordRequest(
            email=email,
            current_password="wrongoldpassword",
            new_password="newpassword999",
            confirm_password="newpassword999",
        ))
    assert e4.value.status_code == 400

    # 5. เปลี่ยนสำเร็จ
    change_res = change_password(ChangePasswordRequest(
        email=email,
        current_password="oldpassword123",
        new_password="newpassword999",
        confirm_password="newpassword999",
    ))
    assert change_res["message"] == "เปลี่ยนรหัสผ่านเรียบร้อยแล้ว"


def test_forgot_password_request_and_confirm(session):
    """ทดสอบ Flow ลืมรหัสผ่าน (ขอ OTP และยืนยันรหัสใหม่)"""
    email = "forgot@example.com"
    register_user(RegisterRequest(
        first_name="สมศักดิ์",
        last_name="สุขใจ",
        phone="0891112222",
        email=email,
        password="originalpassword",
        confirm="originalpassword",
    ))

    # 1. ขอรีเซ็ตรหัสผ่าน
    req_res = request_password_reset(RequestResetRequest(email=email))
    assert "OTP" in req_res["message"] or "ส่ง" in req_res["message"]

    # 2. ขอกรณีอีเมลที่ไม่มีในระบบ ต้องได้ 404
    with pytest.raises(HTTPException) as exc_404:
        request_password_reset(RequestResetRequest(email="notfound@example.com"))
    assert exc_404.value.status_code == 404

    # 3. ยืนยันรหัสผ่านใหม่
    confirm_res = confirm_password_reset(ConfirmResetRequest(
        email=email,
        otp="123456",
        new_password="brandnewpassword123",
        confirm_password="brandnewpassword123",
    ))
    assert confirm_res["message"] == "ตั้งรหัสผ่านใหม่เรียบร้อยแล้ว"


def test_patient_records_flow_and_search(session):
    """ทดสอบระบบเวชระเบียน (Patient Records):

    1. สร้างเวชระเบียน (create_patient_record)
    2. ค้นหาคนไข้แบบ Search Filter (list_all_patients)
    3. ดึงข้อมูลตาม HN (get_patient_by_hn)
    4. แก้ไขข้อมูลผู้ป่วย (update_patient_record)
    """
    # 1. สร้างเวชระเบียน 2 คน
    create_patient_record(PatientCreateRequest(
        first_name="ประสิทธิ์",
        last_name="ยอดเยี่ยม",
        phone_number="0877777777",
        birth_date="1988-12-05",
    ))
    create_patient_record(PatientCreateRequest(
        first_name="กรรณิการ์",
        last_name="สวยงาม",
        phone_number="0866666666",
        birth_date="1992-03-10",
    ))

    # 2. ค้นหาผู้ป่วยด้วยคำค้น "ประสิทธิ์"
    search_res = list_all_patients(search="ประสิทธิ์")
    assert len(search_res) == 1
    assert search_res[0]["full_name"] == "ประสิทธิ์ ยอดเยี่ยม"

    # 3. ดึงข้อมูลตามรหัส HN
    p1 = get_patient_by_hn("P-0001")
    assert p1["first_name"] == "ประสิทธิ์"

    # 4. อัปเดตข้อมูล
    update_patient_record("P-0001", PatientUpdateRequest(
        address="999 สยามแสควร์",
    ))
    p1_updated = get_patient_by_hn("P-0001")
    assert p1_updated["address"] == "999 สยามแสควร์"

    # 5. อัปเดตคนไข้ที่ไม่มีอยู่จริง ต้องเกิด HTTP 404
    with pytest.raises(HTTPException) as exc_info:
        update_patient_record("P-9999", PatientUpdateRequest(first_name="ไม่มีจริง"))
    assert exc_info.value.status_code == 404
