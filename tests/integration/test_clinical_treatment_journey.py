"""Integration Test: วงจรการตรวจรักษาและการออกใบนัดหมาย (Clinical Treatment & Appointment Journey)

Scenario:
1. เจ้าหน้าที่เปิดดูคิวประจำวันที่มีผู้ป่วยจองเข้ามา
2. เจ้าหน้าที่เรียกคิวและเปลี่ยนสถานะเป็น 'กำลังรับบริการ'
3. ทันตแพทย์ตรวจช่องปากและทำการผ่าฟันคุดที่ซี่ 18 พร้อมบันทึกประวัติการรักษา (POST /api/treatments)
4. ทันตแพทย์อุดฟันกรามซี่ 16 เพิ่มเติม และบันทึกประวัติซี่ที่สอง
5. ตรวจสอบว่าประวัติการรักษาทั้ง 2 รายการถูกผูกกับรหัสคนไข้อย่างถูกต้อง และสามารถดึงดูแยกตามซี่ฟันได้
6. เจ้าหน้าที่ปรับสถานะคิวเป็น 'เสร็จสิ้น'
7. ทันตแพทย์ออกใบนัดหมายติดตามอาการอีก 7 วันข้างหน้า (POST /api/appointments)
8. คนไข้ติดต่อขอเลื่อนนัดหมายออกไปอีก 3 วัน (PUT /api/appointments/{id}/reschedule)
9. ตรวจสอบว่าระบบบันทึกประวัติวันเดิมไว้ใน rescheduled_from_date และปรับวันนัดหมายใหม่สำเร็จ
"""

import datetime as dt
from dental_clinic_system.backend.api_auth import (
    register_user,
    RegisterRequest,
)
from dental_clinic_system.backend.api_queue import (
    create_queue_booking,
    update_queue_status,
    create_appointment,
    reschedule_appointment,
    QueueCreate,
    QueueStatusUpdate,
    AppointmentCreate,
    AppointmentReschedule,
)
from dental_clinic_system.backend.api import (
    create_treatment,
    get_treatments,
    TreatmentCreate,
)


def test_clinical_treatment_and_appointment_lifecycle(integration_session):
    """ทดสอบวงจรการรักษาตั้งแต่เรียกคิว -> ลงผังฟัน -> ออกใบนัด -> เลื่อนนัดหมาย"""

    # -----------------------------------------------------------------------
    # Step 1: เตรียมคนไข้และคำขอคิวตรวจ
    # -----------------------------------------------------------------------
    reg_res = register_user(RegisterRequest(
        first_name="ณัฐพล",
        last_name="รักษาดี",
        phone="0851112233",
        email="nattapon@example.com",
        password="Password123!",
        confirm="Password123!",
    ))
    hn_code = reg_res["hn_code"]

    today = dt.date(2026, 11, 15)
    booking_res = create_queue_booking(
        QueueCreate(
            patient_name="ณัฐพล รักษาดี",
            phone_number="0851112233",
            booking_date=today,
            booking_time=dt.time(9, 30),
            service_type="ปวดฟันคุดและตรวจฟัน",
        ),
        session=integration_session,
    )
    queue_id = booking_res["data"].id
    assert booking_res["data"].status == "รออนุมัติ"

    # -----------------------------------------------------------------------
    # Step 2: เจ้าหน้าที่เรียกคิวคนไข้เข้าห้องตรวจ
    # -----------------------------------------------------------------------
    status_res = update_queue_status(
        queue_id=queue_id,
        payload=QueueStatusUpdate(status="กำลังรับบริการ"),
        session=integration_session,
    )
    assert status_res["data"].status == "กำลังรับบริการ"

    # -----------------------------------------------------------------------
    # Step 3: ทันตแพทย์ผ่าฟันคุดซี่ 18 และบันทึกประวัติ
    # -----------------------------------------------------------------------
    t1 = create_treatment(TreatmentCreate(
        patient_id=hn_code,
        tooth_number="18",  # ฟันคุด บนขวา
        icd_code="K01.1",   # ฟันคุด
        procedure_name="ผ่าฟันคุดและเย็บแผล",
        notes="แผลลึกเล็กน้อย ให้ยาแก้ปวดและนัดตัดไหม 7 วัน",
        dentist_name="ทพ. วรวัฒน์ ทันตแพทย์เฉพาะทาง",
    ))
    assert t1["status"] == "success"

    # -----------------------------------------------------------------------
    # Step 4: ทันตแพทย์อุดฟันกรามซี่ 16 เพิ่มเติม
    # -----------------------------------------------------------------------
    t2 = create_treatment(TreatmentCreate(
        patient_id=hn_code,
        tooth_number="16",  # ฟันกรามใหญ่ บนขวา
        icd_code="K02.1",   # ฟันผุถึงเนื้อฟัน
        procedure_name="อุดฟันด้วยเรซินคอมโพสิต 1 ด้าน",
        notes="อุดเรียบร้อยดี",
        dentist_name="ทพ. วรวัฒน์ ทันตแพทย์เฉพาะทาง",
    ))
    assert t2["status"] == "success"

    # ตรวจสอบว่าในประวัติของคนไข้ HN นี้มีรายการรักษาครบ 2 รายการ
    patient_treatments = get_treatments(patient_id=hn_code)
    assert len(patient_treatments) == 2

    # ตรวจสอบการฟิลเตอร์เฉพาะซี่ 18
    tooth_18_treatments = get_treatments(patient_id=hn_code, tooth="18")
    assert len(tooth_18_treatments) == 1
    assert tooth_18_treatments[0].procedure_name == "ผ่าฟันคุดและเย็บแผล"

    # -----------------------------------------------------------------------
    # Step 5: การรักษาเสร็จสิ้น ปรับสถานะคิว
    # -----------------------------------------------------------------------
    done_res = update_queue_status(
        queue_id=queue_id,
        payload=QueueStatusUpdate(status="เสร็จสิ้น"),
        session=integration_session,
    )
    assert done_res["data"].status == "เสร็จสิ้น"

    # -----------------------------------------------------------------------
    # Step 6: ออกใบนัดหมายตัดไหมอีก 7 วันข้างหน้า
    # -----------------------------------------------------------------------
    original_appt_date = today + dt.timedelta(days=7)
    original_appt_time = dt.time(10, 0)

    appt_res = create_appointment(
        AppointmentCreate(
            patient_name="ณัฐพล รักษาดี",
            contact_info="0851112233",
            appointment_date=original_appt_date,
            appointment_time=original_appt_time,
            purpose="ตัดไหมหลังผ่าฟันคุดซี่ 18",
            notes="คนไข้สะดวกช่วงเช้า",
        ),
        session=integration_session,
    )
    appt = appt_res["data"]
    appt_id = appt.id
    assert appt.appointment_slip_code.startswith("APP-")
    assert appt.status == "มาตามเวลานัด"

    # -----------------------------------------------------------------------
    # Step 7: คนไข้ขอเลื่อนนัดหมายออกไปอีก 3 วัน
    # -----------------------------------------------------------------------
    rescheduled_date = original_appt_date + dt.timedelta(days=3)
    rescheduled_time = dt.time(14, 0)

    resched_res = reschedule_appointment(
        appointment_id=appt_id,
        payload=AppointmentReschedule(
            new_date=rescheduled_date,
            new_time=rescheduled_time,
            notes="คนไข้ติดสอบ ขอเลื่อนเป็นช่วงบ่ายของอีก 3 วันถัดไป",
        ),
        session=integration_session,
    )
    rescheduled_appt = resched_res["data"]

    # ตรวจสอบประวัติการเลื่อนนัด (Audit trail)
    assert rescheduled_appt.rescheduled_from_date == original_appt_date
    assert rescheduled_appt.rescheduled_from_time == original_appt_time
    assert rescheduled_appt.appointment_date == rescheduled_date
    assert rescheduled_appt.appointment_time == rescheduled_time
    assert rescheduled_appt.status == "เลื่อนนัดหมาย"

