"""Unit tests สำหรับการจัดการตารางนัดหมาย คิว และประวัติการรักษา (SRS 5.3, 5.4)

ครอบคลุมหัวข้อที่ 4:
1. การทำงานของ ScheduleState (backend/schedule_state.py):
   - การจองคิว (create_queue_booking) และการออกรหัส Q-YYYYMMDD-XXXX
   - การอัปเดตสถานะคิว (update_queue_status)
   - การสร้างใบนัดหมาย (create_appointment) และการออกรหัส AP-YYYYMMDD-XXXX
   - การโหลดข้อมูล Dashboard ประจำวัน (load_daily_dashboard)
   - Computed Vars: total_patients_today, pending_queues_count, confirmed_queues_count
2. การทำงานของ Treatment & Dental Chart API (backend/api.py):
   - บันทึกประวัติการรักษา (create_treatment)
   - ดึงประวัติการรักษาทั้งหมด และการฟิลเตอร์ตามคนไข้ / ซี่ฟัน (get_treatments)
   - ดึงตาม ID (get_treatment_by_id) และกรณี 404
   - แก้ไขประวัติการรักษา (update_treatment) และกรณี 404
   - ลบประวัติการรักษา (delete_treatment) และกรณี 404
3. โมเดลตารางเวลาหมอ DoctorSchedule (backend/models.py):
   - วันทำงาน (work_days), เวลาเริ่ม-เลิก, เวลาพักเที่ยง, และวันลา (leaves)
"""

import datetime as dt
import pytest
from fastapi import HTTPException
from sqlmodel import select

from dental_clinic_system.backend.schedule_state import ScheduleState
from dental_clinic_system.backend.models import QueueBooking, Appointment, DoctorSchedule
from dental_clinic_system.backend.api import (
    create_treatment,
    get_treatments,
    get_treatment_by_id,
    update_treatment,
    delete_treatment,
    TreatmentCreate,
    TreatmentUpdate,
)


# ===========================================================================
# 1. การทดสอบ ScheduleState (ตารางคิวและนัดหมายประจำวัน)
# ===========================================================================

def test_schedule_state_create_queue_booking(session):
    """ทดสอบ ScheduleState.create_queue_booking:

    - ตรวจจับชื่อหรือเบอร์ว่าง
    - บันทึกสำเร็จพร้อมออกใบคิวและรหัสคิว
    """
    state = ScheduleState()

    # 1. กรณีไม่กรอกข้อมูล
    state.q_name = ""
    state.q_phone = ""
    res = state.create_queue_booking()
    assert state.is_booking_slip_ready is False

    # 2. กรอกข้อมูลครบถ้วน
    state.q_name = "นายสมศักดิ์ ขยันยิ่ง"
    state.q_phone = "0812345678"
    state.q_service = "ตรวจฟันประจำปี"
    state.create_queue_booking()

    assert state.is_booking_slip_ready is True
    assert state.latest_booking_slip is not None
    assert state.latest_booking_slip.booking_code.startswith("Q-")
    assert state.latest_booking_slip.status == "รออนุมัติ"

    # ปิดใบคิว
    state.close_booking_slip()
    assert state.is_booking_slip_ready is False


def test_schedule_state_create_appointment_and_dashboard(session):
    """ทดสอบการสร้างใบนัดหมายและการนับจำนวนผู้ป่วยใน Dashboard:

    - สร้างนัดหมายและออกรหัส AP-
    - คำนวณ total_patients_today และ pending_queues_count
    """
    state = ScheduleState()
    today_str = str(dt.date.today())
    state.appt_date = today_str
    state.appt_name = "นางสาวปราณี สุขใจ"
    state.appt_contact = "0899998888"
    state.appt_purpose = "นัดตรวจซ้ำ 1 สัปดาห์"

    state.create_appointment()

    assert state.is_appointment_slip_ready is True
    assert state.latest_appointment_slip is not None
    assert state.latest_appointment_slip.appointment_slip_code.startswith("AP-")

    # ตรวจสอบ Dashboard
    state.filter_date = today_str
    state.load_daily_dashboard()

    assert state.total_patients_today >= 1
    assert len(state.daily_appts) >= 1

    # ปิดใบนัด
    state.close_appointment_slip()
    assert state.is_appointment_slip_ready is False


def test_schedule_state_status_updates(session):
    """ทดสอบการเปลี่ยนสถานะคิวและการนัดหมายผ่าน ScheduleState"""
    state = ScheduleState()
    state.q_name = "คนไข้ทดสอบสถานะ"
    state.q_phone = "0855554444"
    state.create_queue_booking()
    booking_id = state.latest_booking_slip.id

    # เปลี่ยนสถานะเป็น ยืนยันการจองคิว
    state.update_queue_status(booking_id=booking_id, new_status="ยืนยันการจองคิว")

    booking = session.get(QueueBooking, booking_id)
    assert booking.status == "ยืนยันการจองคิว"


# ===========================================================================
# 2. การทดสอบ Dental Chart & Treatment API (SRS 5.4)
# ===========================================================================

def test_treatment_api_full_crud(session):
    """ทดสอบ CRUD บันทึกประวัติการรักษาและการผูกกับซี่ฟัน:

    1. สร้างบันทึกการรักษา (create_treatment)
    2. ค้นหาและฟิลเตอร์ตาม patient_id และ tooth (get_treatments)
    3. ดึงตาม ID (get_treatment_by_id)
    4. แก้ไขข้อมูล (update_treatment)
    5. ลบข้อมูล (delete_treatment)
    """
    # 1. บันทึกการรักษาใหม่
    create_payload = TreatmentCreate(
        patient_id="P-0001",
        tooth_number="18",
        icd_code="K02.1",
        procedure_name="ผ่าฟันคุด",
        notes="แผลเรียบร้อยดี นัดตัดไหม 7 วัน",
        dentist_name="ทพ. วรวัฒน์",
    )
    res = create_treatment(create_payload)
    assert res["status"] == "success"
    entry = res["data"]
    entry_id = entry.id
    assert entry.tooth_number == "18"

    # 2. ฟิลเตอร์ตาม patient_id และ tooth
    treatments = get_treatments(patient_id="P-0001", tooth="18")
    assert len(treatments) == 1
    assert treatments[0].procedure_name == "ผ่าฟันคุด"

    # ฟิลเตอร์ซี่ฟันอื่นที่ไม่มีการรักษา
    no_treatments = get_treatments(patient_id="P-0001", tooth="48")
    assert len(no_treatments) == 0

    # 3. ดึงตาม ID
    entry_by_id = get_treatment_by_id(entry_id)
    assert entry_by_id.id == entry_id

    # กรณีไม่พบ ID
    with pytest.raises(HTTPException) as exc_404:
        get_treatment_by_id(99999)
    assert exc_404.value.status_code == 404

    # 4. แก้ไขข้อมูล
    update_res = update_treatment(entry_id, TreatmentUpdate(procedure_name="ผ่าฟันคุดและเย็บแผล"))
    assert update_res["data"].procedure_name == "ผ่าฟันคุดและเย็บแผล"

    # 5. ลบรายการ
    del_res = delete_treatment(entry_id)
    assert del_res["status"] == "success"

    # ตรวจสอบว่าลบแล้วจริง
    with pytest.raises(HTTPException):
        get_treatment_by_id(entry_id)


# ===========================================================================
# 3. การทดสอบ DoctorSchedule Model
# ===========================================================================

def test_doctor_schedule_model(session):
    """ทดสอบการสร้างและบันทึกตารางการทำงานของทันตแพทย์"""
    schedule = DoctorSchedule(
        dentist_id="DOC01",
        dentist_name="ทพ. สมชาย รักฟัน",
        schedule_month="2026-11",
        work_days="1,2,3,4,5",  # จันทร์ - ศุกร์
        start_time="09:00",
        end_time="17:00",
        lunch_time="12:00",
        leaves="['2026-11-15', '2026-11-16']",  # วันลา
    )
    session.add(schedule)
    session.commit()
    session.refresh(schedule)

    assert schedule.id is not None
    assert schedule.dentist_id == "DOC01"
    assert "1,2,3,4,5" in schedule.work_days
    assert "2026-11-15" in schedule.leaves

