"""Integration Test: วงจรชีวิตและการใช้งานของผู้ป่วย (Patient End-to-End Journey)

Scenario:
1. ผู้ป่วยใหม่กรอกข้อมูลสมัครสมาชิกผ่าน API (POST /auth/register)
2. ตรวจสอบว่าระบบสร้างบัญชี User พร้อมรหัสผ่านแฮช และเปิดเวชระเบียนใน Patient ด้วยรหัส HN 'P-0001'
3. ผู้ป่วยล็อกอินเข้าสู่ระบบ (POST /auth/login) เพื่อรับข้อมูลส่วนตัว
4. ผู้ป่วยตรวจสอบและอัปเดตประวัติสุขภาพของตนเอง เช่น โรคประจำตัว/การแพ้ยา (PUT /patients/{hn_code})
5. ผู้ป่วยทำการจองคิวตรวจฟันออนไลน์ (POST /api/queues)
6. ตรวจสอบว่าคิวถูกบันทึกลงในระบบอย่างถูกต้อง พร้อมสถานะเริ่มต้น 'รออนุมัติ' และมีรหัสคิว Q-XXXXXX
"""

import datetime as dt
from sqlmodel import select

from dental_clinic_system.backend.api_auth import (
    register_user,
    login_user,
    get_patient_by_hn,
    update_patient_record,
    RegisterRequest,
    LoginRequest,
    PatientUpdateRequest,
)
from dental_clinic_system.backend.api_queue import (
    create_queue_booking,
    get_all_queues,
    QueueCreate,
)
from dental_clinic_system.backend.models import User, Patient, QueueBooking


def test_complete_patient_journey(integration_session):
    """ทดสอบ Flow เต็มของผู้ป่วยตั้งแต่สมัครสมาชิก -> ล็อกอิน -> อัปเดตข้อมูล -> จองคิว"""

    # -----------------------------------------------------------------------
    # Step 1: สมัครสมาชิกผู้ป่วยใหม่
    # -----------------------------------------------------------------------
    reg_payload = RegisterRequest(
        first_name="ธีรเดช",
        last_name="เจริญสุข",
        phone="0891234567",
        email="teeradej@example.com",
        password="MySecretPassword123!",
        confirm="MySecretPassword123!",
        gender="ชาย",
        dob="1992-08-14",
        address="99/1 อาคารสยาม ปทุมวัน กทม.",
        disease="ไม่มี",
        allergy="ไม่มี",
    )
    reg_response = register_user(reg_payload)

    assert reg_response["message"] == "สมัครสมาชิกสำเร็จ"
    hn_code = reg_response["hn_code"]
    user_id = reg_response["user_id"]
    assert hn_code == "P-0001"

    # ตรวจสอบความถูกต้องของ Foreign Key ใน Database
    patient_record = integration_session.exec(
        select(Patient).where(Patient.hn_code == hn_code)
    ).first()
    assert patient_record is not None
    assert patient_record.user_id == user_id
    assert patient_record.first_name == "ธีรเดช"

    # -----------------------------------------------------------------------
    # Step 2: เข้าสู่ระบบ (Login)
    # -----------------------------------------------------------------------
    login_payload = LoginRequest(
        username="teeradej@example.com",
        password="MySecretPassword123!",
        role="patient",
    )
    login_response = login_user(login_payload)

    assert login_response["message"] == "เข้าสู่ระบบสำเร็จ"
    assert login_response["user"]["id"] == user_id
    assert login_response["patient"]["hn_code"] == hn_code
    assert login_response["patient"]["first_name"] == "ธีรเดช"

    # -----------------------------------------------------------------------
    # Step 3: อัปเดตประวัติสุขภาพ (เพิ่มประวัติแพ้ยา)
    # -----------------------------------------------------------------------
    update_patient_record(
        hn_code=hn_code,
        payload=PatientUpdateRequest(
            drug_allergy="แพ้ยา Amoxicillin (ผื่นคัน)",
            phone_number="0899998888",  # อัปเดตเบอร์ใหม่
        ),
    )

    # ตรวจสอบข้อมูลหลังอัปเดต
    patient_updated = get_patient_by_hn(hn_code)
    assert patient_updated["drug_allergy"] == "แพ้ยา Amoxicillin (ผื่นคัน)"
    assert patient_updated["phone_number"] == "0899998888"

    # -----------------------------------------------------------------------
    # Step 4: จองคิวตรวจฟันออนไลน์
    # -----------------------------------------------------------------------
    booking_date = dt.date(2026, 11, 20)
    booking_time = dt.time(10, 30)

    queue_payload = QueueCreate(
        patient_name=f"{patient_updated['first_name']} {patient_updated['last_name']}",
        phone_number=patient_updated["phone_number"],
        booking_date=booking_date,
        booking_time=booking_time,
        service_type="ขูดหินปูนและตรวจฟันประจำปี",
        underlying_disease=patient_updated["underlying_disease"],
        drug_allergy=patient_updated["drug_allergy"],
    )

    queue_response = create_queue_booking(queue_payload, session=integration_session)

    assert queue_response["status"] == "success"
    booking_item = queue_response["data"]
    assert booking_item.id is not None
    assert booking_item.booking_code.startswith("Q-")
    assert booking_item.status == "รออนุมัติ"
    assert booking_item.drug_allergy == "แพ้ยา Amoxicillin (ผื่นคัน)"

    # ตรวจสอบว่าคิวปรากฏในรายการของวันที่จอง
    today_queues = get_all_queues(booking_date=booking_date, session=integration_session)
    assert len(today_queues) == 1
    assert today_queues[0].booking_code == booking_item.booking_code

