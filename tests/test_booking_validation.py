"""Pure Unit Tests: การตรวจสอบความถูกต้องและกฎทางธุรกิจก่อนการจองคิว (Queue Booking Validation)

ไฟล์นี้ออกแบบตามหลักการ Pure Unit Test:
- ทดสอบเฉพาะฟังก์ชันและการตรวจสอบ Logic แยกขาดจากระบบอื่น
- ไม่ต้องต่อ Database จริง (ทำงานบน RAM / In-Memory 100%)
- รันได้เร็วระดับเสี้ยววินาที (Milliseconds)

ครอบคลุม:
1. การตรวจสอบข้อมูลที่ผู้ใช้กรอกก่อนจองคิว (Input Validation before booking)
2. การตรวจสอบว่าข้อมูลที่จำเป็นครบถ้วน (Required fields completeness)
3. การตรวจสอบกฎการจองคิว เช่น รูปแบบเวลาไม่ถูกต้อง, ยังไม่ได้เลือกเวลา, ข้อมูลไม่ครบ
4. การสร้างแบบร่างการจองคิว (Booking Draft) และป้ายแสดงผล
"""

import datetime as dt
import pytest
from pydantic import ValidationError

from dental_clinic_system.state import AppState, format_appointment
from dental_clinic_system.backend.api_queue import QueueCreate
from dental_clinic_system.backend.schedule_state import ScheduleState


# ===========================================================================
# 1. ตรวจสอบข้อมูลก่อนจองคิวในระดับ State (AppState Booking Logic)
# ===========================================================================

def test_booking_rejected_when_time_not_selected():
    """ตรวจสอบกฎการจองคิว: ต้องเลือกช่วงเวลาก่อนจอง

    หากยังไม่ได้เลือกเวลา (booking_time ว่าง) ระบบต้องไม่อนุมัติและไม่สร้าง booking_draft
    """
    state = AppState()
    state.booking_date = "2026-11-10"
    state.booking_time = ""  # ยังไม่ได้เลือกเวลา

    # ส่งฟอร์มรายละเอียดคนไข้
    state.submit_booking_details({"name": "สมชาย ใจดี", "phone": "0812345678"})

    # ตรวจสอบว่า booking_draft ต้องว่างเปล่า (ไม่อนุญาตให้ไปต่อ)
    assert state.booking_draft == {}


def test_booking_draft_created_when_required_data_complete():
    """ตรวจสอบว่าข้อมูลที่จำเป็นครบถ้วนแล้วสามารถสร้าง Booking Draft ได้สำเร็จ:

    - วันที่, เวลา, บริการ, ชื่อคนไข้, เบอร์โทร
    - สถานะเริ่มต้นของ Draft ต้องเป็น 'รออนุมัติ'
    """
    state = AppState()
    state.booking_date = "2026-11-10"
    state.booking_time = "10:30"
    state.booking_service = "ขูดหินปูน"
    state.booking_dentist = "ไม่ระบุ"

    state.submit_booking_details({
        "name": "สมชาย ใจดี",
        "phone": "0812345678",
        "disease": "ไม่มี",
        "allergy": "ไม่มี",
        "note": "ขอช่วงเช้า",
    })

    draft = state.booking_draft
    assert draft != {}
    assert draft["patient_name"] == "สมชาย ใจดี"
    assert draft["phone"] == "0812345678"
    assert draft["date"] == "2026-11-10"
    assert draft["time"] == "10:30"
    assert draft["service"] == "ขูดหินปูน"
    assert draft["status"] == "รออนุมัติ"
    assert draft["dentist"] == ""  # 'ไม่ระบุ' จะถูกแปลงเป็นค่าว่างตามกฎ
    assert "2569" in draft["date_th"]  # แปลง พ.ศ. แสดงผล


def test_booking_dentist_assignment_rule():
    """ตรวจสอบกฎการเลือกทันตแพทย์:

    - หากระบุชื่อหมอ -> Draft ต้องมีชื่อหมอคนนั้น
    - หากเลือก 'ไม่ระบุ' -> Draft ต้องเป็นสตริงว่าง
    """
    state = AppState()
    state.booking_date = "2026-11-10"
    state.booking_time = "14:00"

    # กรณีระบุชื่อทันตแพทย์
    state.booking_dentist = "ทพ. วรวัฒน์"
    state.submit_booking_details({"name": "คนไข้ ก", "phone": "0899999999"})
    assert state.booking_draft["dentist"] == "ทพ. วรวัฒน์"

    # กรณีไม่ระบุ
    state.booking_dentist = "ไม่ระบุ"
    state.submit_booking_details({"name": "คนไข้ ข", "phone": "0899999999"})
    assert state.booking_draft["dentist"] == ""


# ===========================================================================
# 2. ตรวจสอบข้อมูลที่จำเป็นผ่าน Pydantic Schema (Schema Validation)
# ===========================================================================

def test_queue_create_validation_success():
    """ตรวจสอบข้อมูลที่ผู้ใช้กรอกผ่าน Schema เมื่อข้อมูลครบถ้วนและถูกต้อง"""
    data = QueueCreate(
        patient_name="วิภาดา สดใส",
        phone_number="0876543210",
        booking_date=dt.date(2026, 11, 20),
        booking_time=dt.time(11, 0),
        service_type="อุดฟัน",
    )
    assert data.patient_name == "วิภาดา สดใส"
    assert data.phone_number == "0876543210"
    assert data.underlying_disease == "ไม่มี"  # ค่า default
    assert data.drug_allergy == "ไม่มี"  # ค่า default


def test_queue_create_validation_missing_required_fields():
    """ตรวจสอบกรณีข้อมูลที่จำเป็นไม่ครบถ้วน เช่น ไม่ระบุชื่อ, เบอร์ หรือบริการ

    ต้องเกิด ValidationError ทันทีโดยไม่ต้องแตะ Database
    """
    # 1. ขาด patient_name
    with pytest.raises(ValidationError):
        QueueCreate(
            patient_name=None,  # type: ignore
            phone_number="0812345678",
            booking_date=dt.date(2026, 11, 20),
            booking_time=dt.time(10, 0),
            service_type="ถอนฟัน",
        )

    # 2. ขาด service_type
    with pytest.raises(ValidationError):
        QueueCreate(
            patient_name="สมควร",
            phone_number="0812345678",
            booking_date=dt.date(2026, 11, 20),
            booking_time=dt.time(10, 0),
            service_type=None,  # type: ignore
        )


def test_queue_create_validation_invalid_date_or_time():
    """ตรวจสอบกรณีเวลาหรือวันที่ไม่ถูกต้องตามรูปแบบ (Type Validation)"""
    # เวลาผิดรูปแบบ (ไม่ใช่เวลามาตรฐาน)
    with pytest.raises(ValidationError):
        QueueCreate(
            patient_name="สมควร",
            phone_number="0812345678",
            booking_date=dt.date(2026, 11, 20),
            booking_time="invalid-time",  # type: ignore
            service_type="ตรวจฟัน",
        )


# ===========================================================================
# 3. ตรวจสอบกฎการจองคิวใน ScheduleState ก่อนบันทึก
# ===========================================================================

def test_schedule_state_validation_empty_name_or_phone():
    """ตรวจสอบการคัดกรองข้อมูลก่อนสร้างคิว:

    หากชื่อหรือเบอร์โทรว่างเปล่า ScheduleState ต้องไม่อนุมัติให้ออกใบคิว
    """
    state = ScheduleState()

    # 1. ชื่อว่าง
    state.q_name = "   "
    state.q_phone = "0812345678"
    state.create_queue_booking()
    assert state.is_booking_slip_ready is False

    # 2. เบอร์ว่าง
    state.q_name = "สมชาย"
    state.q_phone = ""
    state.create_queue_booking()
    assert state.is_booking_slip_ready is False

