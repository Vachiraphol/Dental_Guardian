"""Unit Tests: ทดสอบ Pure Logic และการจัดการตัวแปรภายใน AppState (ไม่เชื่อมต่อ Database)

ครอบคลุมส่วนที่เหลือของ Unit Test ใน state.py:
1. การจัดตารางเวรและวันทำงานของทันตแพทย์ (toggle_work_day, set_sched_start/end/lunch)
2. การเพิ่มและลบวันลาหยุดพิเศษของทันตแพทย์ (add_leave, remove_leave, schedule_leaves)
3. การคำนวณตารางปฏิทินรายเดือน (monthly_calendar_days) แยกวันทำงานและวันลา
4. การเลื่อนวันที่ใน Dashboard และตัวกรองนัดหมาย (shift_dashboard_date, managed_appointments, daily_stats)
5. การเลือกซี่ฟันและดึงข้อมูลรหัสโรค ICD-10 (select_my_tooth, entry_icd_info)
6. การตั้งค่าความเป็นส่วนตัวและการออกจากระบบ (toggle_privacy, logout)
"""

import json
from dental_clinic_system.state import AppState


# ===========================================================================
# 1. ทดสอบการจัดตารางเวลาทำงานของหมอ (Work Days & Hours Logic)
# ===========================================================================

def test_toggle_work_day_adds_and_removes_days():
    """ทดสอบการคลิกเปิด/ปิดวันทำงานของทันตแพทย์:

    - หากวันนั้นมีอยู่แล้ว ต้องลบออก
    - หากยังไม่มี ต้องเพิ่มเข้าไปและเรียงลำดับจากน้อยไปมาก
    """
    state = AppState()
    state.dentists = [
        {
            "id": "1",
            "name": "ทพ. สมชาย",
            "days": "1,2,3",  # จันทร์, อังคาร, พุธ
            "start": "09:00",
            "end": "17:00",
            "lunch": "12:00",
            "leaves": "[]",
        }
    ]
    state.schedule_dentist_id = "1"

    # 1. กดปิดวันอังคาร ("2") -> ต้องเหลือ "1,3"
    state.toggle_work_day("2")
    assert state.dentists[0]["days"] == "1,3"

    # 2. กดเปิดวันศุกร์ ("5") -> ต้องได้ "1,3,5"
    state.toggle_work_day("5")
    assert state.dentists[0]["days"] == "1,3,5"

    # 3. กดเปิดวันอังคาร ("2") กลับมา -> ต้องเรียงลำดับเป็น "1,2,3,5"
    state.toggle_work_day("2")
    assert state.dentists[0]["days"] == "1,2,3,5"


def test_set_schedule_hours_and_lunch():
    """ทดสอบการตั้งเวลาเริ่มงาน เวลาเลิกงาน และเวลาพักเที่ยงของหมอ"""
    state = AppState()
    state.dentists = [
        {
            "id": "1",
            "name": "ทพ. สมชาย",
            "days": "1,2,3,4,5",
            "start": "09:00",
            "end": "18:00",
            "lunch": "12:00",
            "leaves": "[]",
        }
    ]
    state.schedule_dentist_id = "1"

    # เปลี่ยนเวลาเริ่มและเลิกงาน
    state.set_sched_start("10:00")
    state.set_sched_end("19:00")
    assert state.dentists[0]["start"] == "10:00"
    assert state.dentists[0]["end"] == "19:00"

    # เปลี่ยนเวลาพักเที่ยงเป็น 13:00
    state.set_sched_lunch("13:00")
    assert state.dentists[0]["lunch"] == "13:00"

    # กรณีเลือก "ไม่มีพัก" ต้องถูกแปลงเป็นสตริงว่าง ""
    state.set_sched_lunch("ไม่มีพัก")
    assert state.dentists[0]["lunch"] == ""


# ===========================================================================
# 2. ทดสอบการเพิ่มและลบวันลาหยุดพิเศษของหมอ (Leave Management Logic)
# ===========================================================================

def test_add_and_remove_doctor_leave():
    """ทดสอบการเพิ่มวันลา ป้องกันวันลาซ้ำ และการลบวันลาของทันตแพทย์"""
    state = AppState()
    state.dentists = [
        {
            "id": "1",
            "name": "ทพ. สมชาย",
            "days": "1,2,3,4,5",
            "start": "09:00",
            "end": "18:00",
            "lunch": "12:00",
            "leaves": "[]",
        }
    ]
    state.schedule_dentist_id = "1"

    # 1. กรณีไม่ได้เลือกวันที่ จะต้องไม่เพิ่มรายการวันลา
    state.set_new_leave_date("")
    state.add_leave()
    assert state.schedule_leaves == []

    # 2. เพิ่มวันลาวันที่ 2026-10-15 พร้อมระบุเหตุผล
    state.set_new_leave_date("2026-10-15")
    state.set_new_leave_reason("ไปประชุมวิชาการ")
    state.add_leave()

    leaves = state.schedule_leaves
    assert len(leaves) == 1
    assert leaves[0]["date"] == "2026-10-15"
    assert leaves[0]["reason"] == "ไปประชุมวิชาการ"
    # หลังเพิ่มเสร็จ ฟอร์มกรอกวันลาต้องถูกล้างค่า
    assert state.new_leave_date == ""
    assert state.new_leave_reason == ""

    # 3. พยายามเพิ่มวันลาซ้ำในวันที่เดิม (2026-10-15) ระบบต้องป้องกันไม่ให้ซ้ำ
    state.set_new_leave_date("2026-10-15")
    state.add_leave()
    assert len(state.schedule_leaves) == 1

    # 4. ลบวันลาออก
    state.remove_leave("2026-10-15")
    assert state.schedule_leaves == []


# ===========================================================================
# 3. ทดสอบการสร้างตารางปฏิทินรายเดือน (Monthly Calendar Calculation)
# ===========================================================================

def test_monthly_calendar_days_calculation():
    """ทดสอบการสร้างเซลล์ปฏิทินรายเดือนว่าคำนวณวันเข้าเวรและวันลาได้ถูกต้อง"""
    state = AppState()
    state.schedule_selected_month = "2026-10"  # ตุลาคม 2026 มี 31 วัน
    state.dentists = [
        {
            "id": "1",
            "name": "ทพ. สมชาย",
            "days": "1,2,3,4,5",  # จันทร์ - ศุกร์
            "start": "09:00",
            "end": "17:00",
            "lunch": "12:00",
            "leaves": json.dumps([
                {"date": "2026-10-05", "reason": "ลาพักร้อน", "label": "2026-10-05: ลาพักร้อน"}
            ]),
        }
    ]
    state.schedule_dentist_id = "1"

    cells = state.monthly_calendar_days
    actual_days = [c for c in cells if not c["is_empty"]]
    assert len(actual_days) == 31

    # วันที่ 2026-10-05 เป็นวันจันทร์ แต่หมอลา -> is_leave ต้องเป็น True และ is_work ต้องเป็น "0"
    day_5 = next(c for c in actual_days if c["date_iso"] == "2026-10-05")
    assert day_5["is_leave"] is True
    assert day_5["is_work"] == "0"

    # วันที่ 2026-10-06 เป็นวันอังคาร และหมอไม่ได้ลา -> is_work ต้องเป็น "1"
    day_6 = next(c for c in actual_days if c["date_iso"] == "2026-10-06")
    assert day_6["is_leave"] is False
    assert day_6["is_work"] == "1"


# ===========================================================================
# 4. ทดสอบการเลื่อนวันและตัวกรองนัดหมาย (Dashboard Date & Filtering)
# ===========================================================================

def test_shift_dashboard_date_and_filtering():
    """ทดสอบการเลื่อนวันดูข้อมูล Dashboard และการกรองสถิติประจำวัน"""
    state = AppState()
    state.set_dashboard_date("2026-11-10")
    assert state.dashboard_date == "2026-11-10"

    # เลื่อนไปข้างหน้า 5 วัน -> 2026-11-15
    state.shift_dashboard_date(5)
    assert state.dashboard_date == "2026-11-15"

    # เลื่อนย้อนกลับ 2 วัน -> 2026-11-13
    state.shift_dashboard_date(-2)
    assert state.dashboard_date == "2026-11-13"

    # ทดสอบคำนวณสถิติประจำวัน (daily_stats) และตัวกรองนัดหมาย (managed_appointments)
    state.appointments = [
        {"id": "Q-001", "patient_name": "สมชาย", "phone": "0811111111", "date": "2026-11-13", "time": "09:00", "status": "มาตามนัด"},
        {"id": "Q-002", "patient_name": "สมหญิง", "phone": "0822222222", "date": "2026-11-13", "time": "10:00", "status": "ยืนยันแล้ว"},
        {"id": "Q-003", "patient_name": "วิชัย", "phone": "0833333333", "date": "2026-11-13", "time": "11:00", "status": "รออนุมัติ"},
    ]

    stats = state.daily_stats
    assert stats["total"] == 3
    assert stats["arrived"] == 1
    assert stats["waiting"] == 1
    assert stats["pending"] == 1

    # ทดสอบฟิลเตอร์ค้นหาเฉพาะคำว่า "สมหญิง"
    state.set_appt_filter("ทั้งหมด")
    state.set_appt_search("สมหญิง")
    filtered = state.managed_appointments
    assert len(filtered) == 1
    assert filtered[0]["id"] == "Q-002"


# ===========================================================================
# 5. ทดสอบการเลือกซี่ฟันของคนไข้ ข้อมูล ICD-10 และการตั้งค่าส่วนตัว
# ===========================================================================

def test_select_my_tooth_and_icd_info_and_logout():
    """ทดสอบการกดเลือก/ยกเลิกซี่ฟันของคนไข้ การดึงข้อมูล ICD-10 และการ Logout"""
    state = AppState()

    # 1. กดเลือกซี่ฟัน 24 ครั้งแรก -> เลือกซี่ 24
    state.select_my_tooth("24")
    assert state.my_selected_tooth == "24"
    assert "24" in state.my_selected_tooth_label

    # กดซ้ำที่ซี่ 24 อีกครั้ง -> ยกเลิกการเลือก (กลายเป็นค่าว่าง)
    state.select_my_tooth("24")
    assert state.my_selected_tooth == ""

    # 2. ทดสอบการดึงรายละเอียดรหัสโรค ICD-10
    state.set_entry_icd("K02.1")
    assert state.has_entry_icd is True
    icd_info = state.entry_icd_info
    assert icd_info["code"] == "K02.1"
    assert "ฟันผุ" in icd_info["th"]

    # 3. ทดสอบการสลับค่าความเป็นส่วนตัว (toggle_privacy)
    initial_share = state.privacy["share_history"]
    state.toggle_privacy("share_history")
    assert state.privacy["share_history"] is (not initial_share)

    # 4. ทดสอบการออกจากระบบ (logout) ต้องล้างค่าผู้ใช้ทั้งหมด
    state.user_role = "patient"
    state.user_name = "สมชาย ใจดี"
    state.user_email = "somchai@example.com"
    state.current_patient_id = "P-0001"

    state.logout()
    assert state.user_role == ""
    assert state.user_name == ""
    assert state.user_email == ""
    assert state.current_patient_id == ""
    assert state.is_logged_in is False
