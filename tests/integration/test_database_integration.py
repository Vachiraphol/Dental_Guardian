"""Integration Test: การตรวจสอบการทำงานร่วมกันระหว่าง Backend และ Database Layer

ทดสอบตามข้อกำหนด:
1. Backend บันทึกข้อมูลการจองลง Database ได้จริง (Insert / Save)
2. อ่านข้อมูลการจองที่บันทึกไว้กลับมาได้ (Query / Read back)
3. การเรียกใช้ฟังก์ชัน Backend ทำงานร่วมกับชั้น Database ได้ถูกต้อง (State updates / Transactions)
"""

import datetime as dt
from sqlmodel import select
from dental_clinic_system.backend.api_queue import (
    create_queue_booking,
    update_queue_status,
    QueueCreate,
    QueueStatusUpdate,
)
from dental_clinic_system.backend.models import QueueBooking


def test_backend_saves_booking_to_database(integration_session):
    """1. ตรวจสอบว่า Backend บันทึกข้อมูลการจองลงชั้น Database ได้จริง"""
    payload = QueueCreate(
        patient_name="นายทดสอบ บันทึกข้อมูล",
        phone_number="0819991122",
        booking_date=dt.date(2026, 12, 1),
        booking_time=dt.time(9, 0),
        service_type="ตรวจสุขภาพช่องปาก",
        underlying_disease="ความดันโลหิตสูง",
        drug_allergy="แพ้ยาแอสไพริน",
    )

    # เรียกใช้ฟังก์ชัน Backend ให้ทำงานกับ Database
    response = create_queue_booking(payload, session=integration_session)

    assert response["status"] == "success"
    booking_data = response["data"]
    assert booking_data.id is not None
    generated_code = booking_data.booking_code
    assert generated_code.startswith("Q-")

    # ยืนยันว่าข้อมูลถูกเขียนลงในระดับ Database Table จริง
    db_record = integration_session.get(QueueBooking, booking_data.id)
    assert db_record is not None
    assert db_record.patient_name == "นายทดสอบ บันทึกข้อมูล"
    assert db_record.booking_code == generated_code
    assert db_record.status == "รออนุมัติ"


def test_backend_reads_booking_from_database(integration_session):
    """2. ตรวจสอบว่าสามารถอ่านข้อมูลการจองที่บันทึกไว้กลับมาได้อย่างครบถ้วนและถูกต้อง"""
    target_date = dt.date(2026, 12, 5)
    target_time = dt.time(14, 30)

    # บันทึกข้อมูล
    create_res = create_queue_booking(
        QueueCreate(
            patient_name="นางสาวทดสอบ อ่านข้อมูล",
            phone_number="0823334455",
            booking_date=target_date,
            booking_time=target_time,
            service_type="ขูดหินปูน",
            underlying_disease="ไม่มี",
            drug_allergy="ไม่มี",
        ),
        session=integration_session,
    )
    booking_id = create_res["data"].id
    booking_code = create_res["data"].booking_code

    # อ่านข้อมูลกลับมาจาก Database ผ่าน Query Statement
    statement = select(QueueBooking).where(QueueBooking.booking_code == booking_code)
    queried_record = integration_session.exec(statement).first()

    # ตรวจสอบความถูกต้องของข้อมูลทุกฟิลด์ที่อ่านกลับมา
    assert queried_record is not None
    assert queried_record.id == booking_id
    assert queried_record.patient_name == "นางสาวทดสอบ อ่านข้อมูล"
    assert queried_record.phone_number == "0823334455"
    assert queried_record.booking_date == target_date
    assert queried_record.booking_time == target_time
    assert queried_record.service_type == "ขูดหินปูน"
    assert queried_record.status == "รออนุมัติ"


def test_backend_functions_interact_correctly_with_database(integration_session):
    """3. ตรวจสอบว่าการเรียกใช้ฟังก์ชัน Backend ต่าง ๆ ทำงานร่วมกับ Database ได้ถูกต้อง (Transaction & Updates)"""
    # 3.1 บันทึกคิว
    booking = create_queue_booking(
        QueueCreate(
            patient_name="นายเปลี่ยนสถานะ คิว",
            phone_number="0897778899",
            booking_date=dt.date(2026, 12, 10),
            booking_time=dt.time(11, 0),
            service_type="อุดฟัน",
        ),
        session=integration_session,
    )["data"]

    # 3.2 เรียกฟังก์ชัน Backend อัปเดตสถานะเป็น 'กำลังรับบริการ'
    res_in_progress = update_queue_status(
        queue_id=booking.id,
        payload=QueueStatusUpdate(status="กำลังรับบริการ"),
        session=integration_session,
    )
    assert res_in_progress["status"] == "success"

    # ยืนยันว่าใน Database เปลี่ยนแปลงจริง
    integration_session.expire(booking)
    record_1 = integration_session.get(QueueBooking, booking.id)
    assert record_1.status == "กำลังรับบริการ"

    # 3.3 เรียกฟังก์ชัน Backend อัปเดตสถานะเป็น 'เสร็จสิ้น'
    res_done = update_queue_status(
        queue_id=booking.id,
        payload=QueueStatusUpdate(status="เสร็จสิ้น"),
        session=integration_session,
    )
    assert res_done["status"] == "success"

    # ยืนยันอีกครั้งว่าใน Database ปรับตามฟังก์ชัน Backend
    integration_session.expire(booking)
    record_2 = integration_session.get(QueueBooking, booking.id)
    assert record_2.status == "เสร็จสิ้น"

