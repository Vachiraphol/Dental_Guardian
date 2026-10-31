"""Unit tests สำหรับ API ระบบคิวและการนัดหมาย (api_queue.py)

ทดสอบตามข้อกำหนด SRS 5.3:
1. การจองคิวออนไลน์ (create_queue_booking):
   - ตรวจสอบการออกรหัสคิวอัตโนมัติ (เช่น Q-XXXXXX)
   - สถานะเริ่มต้นต้องเป็น "รออนุมัติ"
2. การค้นหาและกรองคิว (get_all_queues):
   - กรองตามวันที่ (booking_date)
   - กรองตามสถานะ (status)
3. การอัปเดตสถานะคิว (update_queue_status):
   - เปลี่ยนสถานะเป็น "กำลังรับบริการ" หรือ "เสร็จสิ้น"
   - กรณีไม่พบคิว (HTTP 404)
4. การสร้างใบนัดหมาย (create_appointment):
   - ตรวจสอบการออกรหัสใบนัด (APP-XXXXXX)
   - การดึงรายการนัดหมายตามวันที่ (get_all_appointments)
5. การเลื่อนนัดหมาย (reschedule_appointment):
   - ตรวจสอบว่าบันทึกวัน/เวลาเดิมลงใน rescheduled_from_date / rescheduled_from_time
   - สถานะเปลี่ยนเป็น "เลื่อนนัดหมาย"
   - กรณีไม่พบนัดหมายที่จะเลื่อน (HTTP 404)
"""

import datetime as dt
import pytest
from fastapi import HTTPException
from dental_clinic_system.backend.api_queue import (
    create_queue_booking,
    get_all_queues,
    update_queue_status,
    create_appointment,
    get_all_appointments,
    reschedule_appointment,
    QueueCreate,
    QueueStatusUpdate,
    AppointmentCreate,
    AppointmentReschedule,
)


def test_create_queue_booking(session):
    """ทดสอบสร้างรายการจองคิวใหม่:

    - ต้องบันทึกลงตาราง QueueBooking
    - ต้องสุ่มสร้างรหัสคิวขึ้นต้นด้วย 'Q-'
    - สถานะเริ่มต้นต้องเป็น 'รออนุมัติ'
    """
    payload = QueueCreate(
        patient_name="วิชัย สุขสำราญ",
        phone_number="0819876543",
        booking_date=dt.date(2026, 11, 15),
        booking_time=dt.time(10, 30),
        service_type="ขูดหินปูน",
        underlying_disease="ไม่มี",
        drug_allergy="ไม่มี",
    )

    res = create_queue_booking(payload=payload, session=session)

    assert res["status"] == "success"
    queue_item = res["data"]
    assert queue_item.id is not None
    assert queue_item.booking_code.startswith("Q-")
    assert queue_item.status == "รออนุมัติ"
    assert queue_item.patient_name == "วิชัย สุขสำราญ"


def test_get_all_queues_with_filters(session):
    """ทดสอบดึงรายการคิวและฟิลเตอร์ตามวันที่และสถานะ"""
    d1 = dt.date(2026, 11, 15)
    d2 = dt.date(2026, 11, 16)

    q1 = create_queue_booking(
        payload=QueueCreate(
            patient_name="คนไข้คนที่ 1",
            phone_number="0811111111",
            booking_date=d1,
            booking_time=dt.time(9, 0),
            service_type="ตรวจฟัน",
        ),
        session=session,
    )["data"]

    create_queue_booking(
        payload=QueueCreate(
            patient_name="คนไข้คนที่ 2",
            phone_number="0822222222",
            booking_date=d2,
            booking_time=dt.time(10, 0),
            service_type="อุดฟัน",
        ),
        session=session,
    )

    # 1. กรองตามวันที่ d1
    res_d1 = get_all_queues(booking_date=d1, session=session)
    assert len(res_d1) == 1
    assert res_d1[0].patient_name == "คนไข้คนที่ 1"

    # 2. อัปเดตสถานะ q1 แล้วกรองตามสถานะ
    update_queue_status(queue_id=q1.id, payload=QueueStatusUpdate(status="เสร็จสิ้น"), session=session)
    res_finished = get_all_queues(status="เสร็จสิ้น", session=session)
    assert len(res_finished) == 1
    assert res_finished[0].id == q1.id


def test_update_queue_status(session):
    """ทดสอบการเปลี่ยนสถานะคิว เช่น จาก 'รออนุมัติ' -> 'เสร็จสิ้น'"""
    create_res = create_queue_booking(
        payload=QueueCreate(
            patient_name="นภา แจ่มใส",
            phone_number="0822223333",
            booking_date=dt.date(2026, 11, 15),
            booking_time=dt.time(13, 0),
            service_type="อุดฟัน",
        ),
        session=session,
    )
    queue_id = create_res["data"].id

    update_res = update_queue_status(
        queue_id=queue_id,
        payload=QueueStatusUpdate(status="เสร็จสิ้น"),
        session=session,
    )
    assert update_res["status"] == "success"
    assert update_res["data"].status == "เสร็จสิ้น"


def test_update_queue_status_not_found(session):
    """ทดสอบกรณีอัปเดตสถานะของคิวที่ไม่มีอยู่จริง ต้องเกิด HTTP 404"""
    with pytest.raises(HTTPException) as exc_info:
        update_queue_status(
            queue_id=99999,
            payload=QueueStatusUpdate(status="เสร็จสิ้น"),
            session=session,
        )
    assert exc_info.value.status_code == 404


def test_create_and_reschedule_appointment(session):
    """ทดสอบการสร้างใบนัดหมาย ดึงรายการตามวัน และการเลื่อนนัดหมาย:

    - สร้างใบนัดและตรวจรหัส APP-XXXXXX
    - เลื่อนวันนัดและตรวจว่าระบบบันทึกวันเดิมไว้ใน rescheduled_from_date
    - กรณีเลื่อนนัดหมายที่ไม่มีอยู่จริง ต้องเกิด 404
    """
    # 1. สร้างใบนัดหมาย
    original_date = dt.date(2026, 11, 20)
    original_time = dt.time(9, 0)
    appt_res = create_appointment(
        payload=AppointmentCreate(
            patient_name="มานี รักดี",
            contact_info="0833334444",
            appointment_date=original_date,
            appointment_time=original_time,
            purpose="ติดตามอาการหลังถอนฟัน",
            notes="คนไข้สะดวกช่วงเช้า",
        ),
        session=session,
    )
    assert appt_res["status"] == "success"
    appt = appt_res["data"]
    assert appt.appointment_slip_code.startswith("APP-")
    appt_id = appt.id

    # 2. ตรวจสอบการดึงรายการนัดหมายตามวันที่
    appts = get_all_appointments(appointment_date=original_date, session=session)
    assert len(appts) >= 1

    # 3. เลื่อนวันนัดหมายไปยังสัปดาห์ถัดไป
    new_date = dt.date(2026, 11, 27)
    new_time = dt.time(10, 0)
    reschedule_res = reschedule_appointment(
        appointment_id=appt_id,
        payload=AppointmentReschedule(
            new_date=new_date,
            new_time=new_time,
            notes="คนไข้ติดธุระด่วน ขอเลื่อน 1 สัปดาห์",
        ),
        session=session,
    )

    updated_appt = reschedule_res["data"]
    # ตรวจสอบว่าวันเดิมถูกบันทึกเก็บไว้
    assert updated_appt.rescheduled_from_date == original_date
    assert updated_appt.rescheduled_from_time == original_time
    assert updated_appt.appointment_date == new_date
    assert updated_appt.appointment_time == new_time
    assert updated_appt.status == "เลื่อนนัดหมาย"

    # 4. ทดสอบเลื่อนนัดหมายที่ไม่มี ID ในระบบ ต้องได้ 404
    with pytest.raises(HTTPException) as exc_404:
        reschedule_appointment(
            appointment_id=99999,
            payload=AppointmentReschedule(new_date=new_date, new_time=new_time),
            session=session,
        )
    assert exc_404.value.status_code == 404
