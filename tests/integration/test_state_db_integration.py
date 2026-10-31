"""Integration Tests: ทดสอบการทำงานร่วมกันระหว่าง AppState Event Handlers และ Database จริง

ครอบคลุมส่วนที่เหลือทั้งหมดของ Integration Test ใน state.py:
1. วงจรยืนยันจองคิว การจัดเรียงรหัสคิวตามเวลา และการยกเลิกคิว (confirm_booking, cancel_booking)
2. วงจรการจัดการคิวของเจ้าหน้าที่: อนุมัติ, มาตามนัด, ปฏิเสธคิว (approve_request, mark_arrived, reject_request)
3. วงจรการออกใบนัดหมายครั้งถัดไป การเลื่อนนัด และการยกเลิกนัด (create_next_appt, reschedule, cancel_appt)
4. วงจรการบันทึกประวัติการรักษาผังฟัน และการสลับโหมดผังฟันเด็กอัตโนมัติ (save_entry, update_chart_mode_for_patient)
5. วงจรการบันทึกและโหลดตารางเวรทันตแพทย์ประจำเดือน (save_schedule, load_schedule_data)
6. วงจรการแก้ไขข้อมูลส่วนตัว เปลี่ยนรหัสผ่าน และลืมรหัสผ่านผ่านหน้าเว็บ (save_profile, change_password, request_reset, confirm_reset)
"""

import datetime as dt
from sqlmodel import select

from dental_clinic_system.state import AppState
from dental_clinic_system.backend.models import (
    User,
    Patient,
    QueueBooking,
    Appointment,
    TreatmentEntry,
    DoctorSchedule,
)


# ===========================================================================
# 1. ทดสอบการยืนยันจองคิว เรียงลำดับเลขคิวตามเวลา และยกเลิกคิว
# ===========================================================================

def test_confirm_booking_and_auto_resequencing(integration_session):
    """ทดสอบระบบจองคิวและจัดลำดับเลขคิวอัตโนมัติ (Queue Auto-Resequencing):

    - คนที่ 1 จองเวลา 14:00 -> ได้รหัส Q-20261115-001
    - คนที่ 2 จองวันเดียวกันแต่เวลาเช้ากว่า (09:00) -> ระบบต้องจัดลำดับใหม่ให้ 09:00 เป็น Q-20261115-001
      และเลื่อนคิว 14:00 ไปเป็น Q-20261115-002
    - เมื่อยกเลิกคิว Q-20261115-001 -> คิวที่เหลือต้องถูกจัดเลขกลับมาเป็น Q-20261115-001
    """
    state = AppState()
    target_date = "2026-11-15"

    # 1. คนไข้คนที่ 1 จองช่วงบ่าย 14:00
    state.booking_date = target_date
    state.booking_time = "14:00"
    state.booking_service = "ขูดหินปูน"
    state.booking_dentist = "ทพ. สมชาย"
    state.submit_booking_details({"name": "คนไข้บ่าย", "phone": "0811111111"})
    state.confirm_booking()

    assert state.booking_slip["id"] == "Q-20261115-001"
    assert state.booking_draft == {}

    # 2. คนไข้คนที่ 2 จองวันเดียวกัน แต่เวลาเช้า 09:00
    state.booking_date = target_date
    state.booking_time = "09:00"
    state.booking_service = "ตรวจฟัน"
    state.submit_booking_details({"name": "คนไข้เช้า", "phone": "0822222222"})
    state.confirm_booking()

    # คนไข้เช้าต้องได้คิว 001 และคนไข้บ่ายต้องเลื่อนเป็น 002 ใน Database
    assert state.booking_slip["id"] == "Q-20261115-001"

    q_morning = integration_session.exec(
        select(QueueBooking).where(QueueBooking.patient_name == "คนไข้เช้า")
    ).first()
    q_afternoon = integration_session.exec(
        select(QueueBooking).where(QueueBooking.patient_name == "คนไข้บ่าย")
    ).first()
    assert q_morning.booking_code == "Q-20261115-001"
    assert q_afternoon.booking_code == "Q-20261115-002"

    # 3. ยกเลิกคิวเช้า (Q-20261115-001) -> คิวบ่ายต้องถูกปรับเลขกลับมาเป็น Q-20261115-001
    state.cancel_booking("Q-20261115-001")
    integration_session.expire_all()

    remaining = integration_session.exec(select(QueueBooking)).all()
    assert len(remaining) == 1
    assert remaining[0].patient_name == "คนไข้บ่าย"
    assert remaining[0].booking_code == "Q-20261115-001"


# ===========================================================================
# 2. ทดสอบการจัดการคิวของเจ้าหน้าที่ (อนุมัติ, มาตามนัด, ปฏิเสธ)
# ===========================================================================

def test_staff_queue_approve_arrive_and_reject(integration_session):
    """ทดสอบการทำงานของเจ้าหน้าที่คลินิกผ่าน AppState:

    - approve_request: เปลี่ยนสถานะเป็น 'ยืนยันแล้ว'
    - mark_arrived: เปลี่ยนสถานะเป็น 'มาตามนัด'
    - reject_request: ปฏิเสธและลบรายการคิวออกจากฐานข้อมูล
    """
    state = AppState()
    state.booking_date = "2026-11-18"
    state.booking_time = "10:00"
    state.submit_booking_details({"name": "วิภาวรรณ", "phone": "0891234567"})
    state.confirm_booking()
    code = state.booking_slip["id"]

    # 1. กดอนุมัติคิว
    state.approve_request(code)
    integration_session.expire_all()
    booking = integration_session.exec(
        select(QueueBooking).where(QueueBooking.booking_code == code)
    ).first()
    assert booking.status == "ยืนยันแล้ว"

    # 2. กดบันทึกว่าคนไข้มาตามนัดแล้ว
    state.mark_arrived(code)
    integration_session.expire_all()
    booking = integration_session.exec(
        select(QueueBooking).where(QueueBooking.booking_code == code)
    ).first()
    assert booking.status == "มาตามนัด"

    # 3. ทดสอบการปฏิเสธคำขอจองคิว (open_reject -> reject_request)
    state.open_reject(code)
    assert state.reject_open is True
    assert state.reject_target == code

    state.reject_request({"reason": "หมอติดเคสฉุกเฉิน"})
    assert state.reject_open is False
    integration_session.expire_all()
    deleted_booking = integration_session.exec(
        select(QueueBooking).where(QueueBooking.booking_code == code)
    ).first()
    assert deleted_booking is None


# ===========================================================================
# 3. ทดสอบการออกใบนัดครั้งถัดไป การเลื่อนนัด และการยกเลิกนัด
# ===========================================================================

def test_create_next_appt_reschedule_and_cancel(integration_session):
    """ทดสอบการออกใบนัดครั้งถัดไป การเลื่อนวันนัด และการยกเลิกนัดหมายผ่าน AppState"""
    state = AppState()
    state.patients = [
        {
            "id": "P-0001",
            "full_name": "สมปอง รักฟัน",
            "phone": "0812223333",
            "disease": "ไม่มี",
            "allergy": "ไม่มี",
        }
    ]
    # จำลองว่าคนไข้เคยตรวจกับ ทพ. วรวัฒน์ เพื่อให้ระบบดึงชื่อหมอเดิมอัตโนมัติ
    state.appointments = [
        {
            "id": "Q-001",
            "patient_id": "P-0001",
            "patient_name": "สมปอง รักฟัน",
            "dentist": "ทพ. วรวัฒน์",
            "date": "2026-11-01",
            "time": "10:00",
            "status": "เสร็จสิ้น",
        }
    ]

    # 1. ออกใบนัดหมายครั้งถัดไป
    state.open_next_appt("P-0001 · สมปอง รักฟัน")
    assert state.next_appt_open is True

    state.create_next_appt({
        "patient": "P-0001 · สมปอง รักฟัน",
        "date": "2026-11-20",
        "time": "11:00",
        "purpose": "ตัดไหมและตรวจแผล",
        "note": "ห้ามเคี้ยวของแข็ง",
    })
    assert state.next_appt_open is False
    assert state.slip_open is True
    slip_code = state.slip["id"]
    assert slip_code == "AP-0001"
    assert state.slip["dentist"] == "ทพ. วรวัฒน์"  # ดึงหมอเดิมมาให้อัตโนมัติ

    # 2. เลื่อนนัดหมาย (open_reschedule -> reschedule)
    state.open_reschedule(slip_code)
    assert state.resched_open is True

    state.reschedule({"date": "2026-11-25", "time": "15:30"})
    assert state.resched_open is False

    integration_session.expire_all()
    appt_db = integration_session.exec(
        select(Appointment).where(Appointment.appointment_slip_code == slip_code)
    ).first()
    assert appt_db.appointment_date == dt.date(2026, 11, 25)
    assert appt_db.appointment_time == dt.time(15, 30)
    assert appt_db.rescheduled_from_date == dt.date(2026, 11, 20)
    assert appt_db.status == "เลื่อนนัด"

    # 3. ยกเลิกนัดหมาย (cancel_appt)
    state.cancel_appt(slip_code)
    integration_session.expire_all()
    assert integration_session.exec(
        select(Appointment).where(Appointment.appointment_slip_code == slip_code)
    ).first() is None


# ===========================================================================
# 4. ทดสอบการบันทึกประวัติผังฟัน และการตรวจจับเคสเด็กอัตโนมัติ
# ===========================================================================

def test_save_treatment_entry_and_child_case_detection(integration_session):
    """ทดสอบการบันทึกการรักษาลงผังฟัน และการสลับเป็นโหมดฟันน้ำนมเมื่อคนไข้อายุ <= 12 ปี"""
    # สร้างคนไข้เด็ก (เกิดปี 2018 -> อายุ 8 ปี) ใน Database
    child_patient = Patient(
        hn_code="P-0001",
        first_name="ด.ช. ต้นกล้า",
        last_name="สดใส",
        phone_number="0890001111",
        birth_date=dt.date(2018, 5, 10),
    )
    integration_session.add(child_patient)
    integration_session.commit()

    state = AppState()
    state.load_patients_data()
    assert len(state.patients) == 1
    assert state.patients[0]["id"] == "P-0001"

    # 1. ทดสอบตรวจจับเคสเด็กอัตโนมัติจากอายุคนไข้ (8 ปี <= 12 ปี)
    state.set_selected_pid("P-0001")
    assert state.chart_mode == "child"
    assert state.is_child_case is True

    # 2. ทดสอบบันทึกประวัติการรักษาซี่ฟันน้ำนม '51'
    state.select_tooth("51")
    state.set_entry_icd("K02.1")
    state.set_entry_procedure("อุดฟันน้ำนม")
    state.set_entry_note("เด็กให้ความร่วมมือดีมาก")
    state.save_entry()

    # หลังบันทึก ฟอร์มต้องถูกล้างค่า และข้อมูลต้องโหลดเข้า state.entries
    assert state.entry_tooth == ""
    assert len(state.entries) == 1
    assert state.entries[0]["tooth"] == "51"
    assert state.entries[0]["icd"] == "K02.1"

    # ตรวจสอบใน Database
    db_entry = integration_session.exec(select(TreatmentEntry)).first()
    assert db_entry is not None
    assert db_entry.patient_id == "P-0001"
    assert db_entry.tooth_number == "51"


# ===========================================================================
# 5. ทดสอบการบันทึกและโหลดตารางเวรหมอประจำเดือน (DoctorSchedule)
# ===========================================================================

def test_save_and_load_doctor_schedule(integration_session):
    """ทดสอบการโหลดข้อมูลทันตแพทย์ การแก้ไขวันทำงาน/วันลา และการบันทึกลงตาราง DoctorSchedule"""
    # 1. สร้างบัญชีทันตแพทย์ในระบบ
    dentist_user = User(
        username="dr_somchai@dental.com",
        password_hash="pass1234",
        full_name="ทพ. สมชาย ใจดี",
        role="dentist",
    )
    integration_session.add(dentist_user)
    integration_session.commit()
    integration_session.refresh(dentist_user)
    doc_id = str(dentist_user.id)

    state = AppState()
    state.schedule_selected_month = "2026-11"
    state.load_schedule_data()

    # ตรวจสอบว่าโหลดหมอเข้ามาใน state.dentists แล้ว
    assert len(state.dentists) == 1
    assert state.schedule_dentist_id == doc_id

    # 2. แก้ไขเวลาเริ่มงาน เพิ่มวันลา และกดบันทึกตารางเวร (save_schedule)
    state.set_sched_start("10:00")
    state.set_sched_end("19:00")
    state.set_new_leave_date("2026-11-20")
    state.set_new_leave_reason("อบรมทันตกรรม")
    state.add_leave()
    state.save_schedule()

    # 3. ตรวจสอบในตาราง DoctorSchedule ว่าบันทึกสำเร็จ
    sched_db = integration_session.exec(
        select(DoctorSchedule).where(
            DoctorSchedule.dentist_id == doc_id,
            DoctorSchedule.schedule_month == "2026-11",
        )
    ).first()
    assert sched_db is not None
    assert sched_db.start_time == "10:00"
    assert sched_db.end_time == "19:00"
    assert "2026-11-20" in sched_db.leaves


# ===========================================================================
# 6. ทดสอบการแก้ไขโปรไฟล์ เปลี่ยนรหัสผ่าน และรีเซ็ตรหัสผ่านผ่าน AppState
# ===========================================================================

def test_profile_update_change_password_and_reset_flow(integration_session):
    """ทดสอบการจัดการบัญชีสมาชิกผ่าน AppState:

    - สมัครและล็อกอิน
    - แก้ไขข้อมูลส่วนตัว (save_profile)
    - เปลี่ยนรหัสผ่าน (change_password)
    - ลืมรหัสผ่านและตั้งรหัสใหม่ (request_reset -> confirm_reset)
    """
    state = AppState()
    email = "member_flow@example.com"

    # 1. สมัครสมาชิกและล็อกอิน
    state.register({
        "first_name": "นพดล",
        "last_name": "คนเดิม",
        "phone": "0810001111",
        "email": email,
        "password": "InitialPassword123",
        "confirm": "InitialPassword123",
    })
    state.login_role = "patient"
    state.login({"email": email, "password": "InitialPassword123"})
    assert state.is_logged_in is True

    # 2. แก้ไขข้อมูลส่วนตัว (save_profile)
    state.save_profile({
        "first_name": "นพดล",
        "last_name": "คนใหม่",
        "phone": "0899990000",
        "address": "88 เชียงใหม่",
        "disease": "ภูมิแพ้",
        "allergy": "ไม่มี",
    })
    assert state.user_name == "นพดล คนใหม่"

    integration_session.expire_all()
    pt_db = integration_session.exec(select(Patient).where(Patient.email == email)).first()
    assert pt_db.last_name == "คนใหม่"
    assert pt_db.phone_number == "0899990000"
    assert pt_db.address == "88 เชียงใหม่"

    # 3. เปลี่ยนรหัสผ่าน (change_password)
    state.change_password({
        "current": "InitialPassword123",
        "new": "ChangedPassword456",
        "confirm": "ChangedPassword456",
    })
    assert state.password_error == ""

    # 4. ทดสอบลืมรหัสผ่าน (request_reset -> confirm_reset)
    state.request_reset({"email": email})
    assert state.reset_step == 2
    assert state.reset_email == email

    state.confirm_reset({
        "otp": "999999",
        "password": "ResetPassword789",
        "confirm": "ResetPassword789",
    })
    assert state.reset_step == 3
    assert state.reset_error == ""

    integration_session.expire_all()
    user_db = integration_session.exec(select(User).where(User.username == email)).first()
    assert user_db.password_hash == "ResetPassword789"


# ===========================================================================
# 7. ทดสอบการคำนวณคิวว่าง (available_slots) และวันเปิดทำการ 14 วัน (booking_days)
# ===========================================================================

def test_available_slots_and_booking_days_capacity(integration_session):
    """ทดสอบการคำนวณช่วงเวลาว่าง (available_slots) และการตัดโควตาเมื่อคิวเต็ม (MAX_CAPACITY = 2):

    - เวลาพักมาตรฐาน (เช่น 12:00) ต้องแสดง 'นอกเวลาทำการ' และ available == '0'
    - เวลาปกติ (เช่น 09:00) เริ่มต้นต้อง 'ว่าง 2 คิว'
    - เมื่อจองไป 1 คิวที่เวลา 09:00 -> ต้องเหลือ 'ว่าง 1 คิว'
    - เมื่อจองครบ 2 คิวที่เวลา 09:00 -> ต้องแสดง 'เต็ม' และ available == '0'
    """
    state = AppState()
    target_date = "2026-11-16"  # วันจันทร์
    state.booking_date = target_date
    state.booking_dentist = "ไม่ระบุ"

    # 1. ตรวจสอบตาราง 14 วันข้างหน้า (booking_days)
    days = state.booking_days
    assert len(days) == 14

    # 2. ตรวจสอบสถานะเริ่มต้นของช่วงเวลา 09:00 และเวลาพัก 12:00
    initial_slots = state.available_slots
    slot_0900 = next(s for s in initial_slots if s["time"] == "09:00")
    slot_1200 = next(s for s in initial_slots if s["time"] == "12:00")

    assert slot_0900["available"] == "1"
    assert "ว่าง 2 คิว" in slot_0900["label"]
    assert slot_1200["available"] == "0"
    assert slot_1200["label"] == "นอกเวลาทำการ"

    # 3. จองคิวที่ 1 เวลา 09:00 -> ต้องเหลือว่าง 1 คิว
    state.booking_time = "09:00"
    state.submit_booking_details({"name": "คนไข้คิว 1", "phone": "0811111111"})
    state.confirm_booking()

    slots_after_1 = state.available_slots
    slot_0900_after_1 = next(s for s in slots_after_1 if s["time"] == "09:00")
    assert slot_0900_after_1["available"] == "1"
    assert "ว่าง 1 คิว" in slot_0900_after_1["label"]

    # 4. จองคิวที่ 2 เวลา 09:00 -> โควตาครบ 2 คิว ต้องขึ้นว่า 'เต็ม' และปิดไม่ให้จอง
    state.booking_time = "09:00"
    state.submit_booking_details({"name": "คนไข้คิว 2", "phone": "0822222222"})
    state.confirm_booking()

    slots_after_2 = state.available_slots
    slot_0900_after_2 = next(s for s in slots_after_2 if s["time"] == "09:00")
    assert slot_0900_after_2["available"] == "0"
    assert slot_0900_after_2["label"] == "เต็ม"

