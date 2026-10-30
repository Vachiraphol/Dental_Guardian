"""Frontend state for Dental Guardian (SRS-3, sections 5.1–5.4).

This file holds only what the UI needs: option lists, display formatting,
UI flags (dialogs, tabs, selections), form validation, and filtering/sorting
for display. It has no data and no business logic.

Every place the backend must plug in is marked `TODO(backend)`. The data lists
(patients, dentists, appointments, entries) start empty; the backend loads rows
into them, passing each row through format_patient / format_appointment /
format_entry so the pages get the display fields they expect.
See BACKEND_HANDOFF.md for the field list of each row.
"""

import json
import calendar
import datetime
import datetime as dt
import uuid
import reflex as rx
from sqlmodel import select
from dental_clinic_system.backend.models import (
    QueueBooking,
    Appointment,
    TreatmentEntry,
    User,
    Patient,
    DoctorSchedule,
    get_utc_now,
)

THAI_MONTHS = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
THAI_DAYS = ["จ.", "อ.", "พ.", "พฤ.", "ศ.", "ส.", "อา."]  # isoweekday 1..7
THAI_DAYS_FULL = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]

SERVICES = [
    "ตรวจสุขภาพช่องปาก",
    "ขูดหินปูน & ขัดฟัน",
    "อุดฟัน",
    "ถอนฟัน",
    "รักษารากฟัน",
    "ผ่าฟันคุด",
    "จัดฟัน (ปรับลวด)",
    "ฟอกสีฟัน",
    "ทันตกรรมสำหรับเด็ก",
]
PROCEDURES = [
    "ตรวจและวินิจฉัย", "ขูดหินปูน", "อุดฟัน", "ถอนฟัน", "รักษารากฟัน", "ครอบฟัน",
    "ผ่าฟันคุด", "เคลือบฟลูออไรด์", "เคลือบหลุมร่องฟัน", "ติดตามอาการ",
]
GENDERS = ["ชาย", "หญิง", "ไม่ระบุ"]

# ICD-10 dental codes mapped to plain-language terms for patients (SRS 5.4)
ICD10 = [
    ("Z01.2", "ตรวจสุขภาพช่องปาก", "Dental examination"),
    ("K02.0", "ฟันผุระยะเริ่มต้น (ผิวเคลือบฟัน)", "Caries limited to enamel"),
    ("K02.1", "ฟันผุถึงชั้นเนื้อฟัน", "Caries of dentine"),
    ("K03.0", "ฟันสึกจากการบดเคี้ยว", "Excessive attrition of teeth"),
    ("K03.6", "หินปูนเกาะฟัน", "Deposits [accretions] on teeth"),
    ("K04.0", "โพรงประสาทฟันอักเสบ", "Pulpitis"),
    ("K04.7", "ฝีรอบปลายรากฟัน", "Periapical abscess without sinus"),
    ("K05.1", "เหงือกอักเสบเรื้อรัง", "Chronic gingivitis"),
    ("K05.3", "โรคปริทันต์อักเสบ (เหงือกร่น ฟันโยก)", "Chronic periodontitis"),
    ("K01.1", "ฟันคุด", "Impacted teeth"),
    ("K07.3", "ฟันซ้อนเก", "Anomalies of tooth position"),
    ("K08.1", "สูญเสียฟัน", "Loss of teeth due to accident, extraction"),
    ("S02.5", "ฟันแตก / ฟันหัก", "Fracture of tooth"),
]
ICD10_TH = {code: th for code, th, _ in ICD10}


# รายการซี่ฟันแท้ (32 ซี่)
PERMANENT_TEETH_UPPER = ["18", "17", "16", "15", "14", "13", "12", "11", "21", "22", "23", "24", "25", "26", "27", "28"]
PERMANENT_TEETH_LOWER = ["48", "47", "46", "45", "44", "43", "42", "41", "31", "32", "33", "34", "35", "36", "37", "38"]
PERMANENT_UPPER = PERMANENT_TEETH_UPPER
PERMANENT_LOWER = PERMANENT_TEETH_LOWER

# รายการซี่ฟันน้ำนม (20 ซี่)
PRIMARY_TEETH_UPPER = ["55", "54", "53", "52", "51", "61", "62", "63", "64", "65"]
PRIMARY_TEETH_LOWER = ["85", "84", "83", "82", "81", "71", "72", "73", "74", "75"]

ALL_TEETH = PERMANENT_TEETH_UPPER + PERMANENT_TEETH_LOWER + PRIMARY_TEETH_UPPER + PRIMARY_TEETH_LOWER

# ฟันกรามในระบบ FDI (ฟันแท้ลงท้ายด้วย 6, 7, 8 และฟันน้ำนมลงท้ายด้วย 4, 5)
MOLARS = {
    # ฟันกรามแท้
    "16", "17", "18",
    "26", "27", "28",
    "36", "37", "38",
    "46", "47", "48",
    # ฟันกรามน้ำนม
    "54", "55",
    "64", "65",
    "74", "75",
    "84", "85",
}

# ทิศทาง/จตุภาค (เลขหลักแรกของ FDI)
FDI_QUADRANTS = {
    "1": ("บนขวา", False),
    "2": ("บนซ้าย", False),
    "3": ("ล่างซ้าย", False),
    "4": ("ล่างขวา", False),
    "5": ("บนขวา", True),
    "6": ("บนซ้าย", True),
    "7": ("ล่างซ้าย", True),
    "8": ("ล่างขวา", True),
}

# ตำแหน่งซี่ฟันแท้ (เลขหลักที่สอง: 1-8 นับจากฟันหน้าตรงกลางไปด้านใน)
PERMANENT_POSITION_NAMES = {
    "1": "ฟันหน้าตรงกลาง",
    "2": "ฟันหน้าด้านข้าง",
    "3": "ฟันเขี้ยว",
    "4": "ฟันกรามน้อยซี่หน้า",
    "5": "ฟันกรามน้อยซี่หลัง",
    "6": "ฟันกรามใหญ่",
    "7": "ฟันกรามในสุด",
    "8": "ฟันคุด",
}

# ตำแหน่งซี่ฟันน้ำนม (เลขหลักที่สอง: 1-5 นับจากฟันหน้าตรงกลางไปด้านใน)
PRIMARY_POSITION_NAMES = {
    "1": "ฟันหน้าตรงกลาง",
    "2": "ฟันหน้าด้านข้าง",
    "3": "ฟันเขี้ยว",
    "4": "ฟันกรามซี่แรก",
    "5": "ฟันกรามในสุด",
}


def tooth_label(tooth: str) -> str:
    """แปลงรหัส FDI สองหลัก เป็นป้ายชื่อแสดงผล เช่น:
    - '48' -> 'ซี่ 48 · ฟันคุด ล่างขวา'
    - '11' -> 'ซี่ 11 · ฟันหน้าตรงกลาง บนขวา'
    - '51' -> 'ซี่ 51 · ฟันหน้าตรงกลาง บนขวา (ฟันน้ำนม)'
    - '85' -> 'ซี่ 85 · ฟันกรามในสุด ล่างขวา (ฟันน้ำนม)'
    """
    if tooth not in ALL_TEETH:
        return tooth or "-"

    quad_code = tooth[0]
    pos_code = tooth[1]

    side, is_primary = FDI_QUADRANTS.get(quad_code, ("-", False))

    if is_primary:
        name = PRIMARY_POSITION_NAMES.get(pos_code, "ฟันน้ำนม")
        return f"ซี่ {tooth} · {name} {side} (ฟันน้ำนม)"
    else:
        name = PERMANENT_POSITION_NAMES.get(pos_code, "ฟันแท้")
        return f"ซี่ {tooth} · {name} {side}"


APPT_STATUSES = ["รออนุมัติ", "ยืนยันแล้ว", "มาตามนัด", "เลื่อนนัด", "ยกเลิกนัด", "ปฏิเสธ"]
ACTIVE_STATUSES = ("รออนุมัติ", "ยืนยันแล้ว", "เลื่อนนัด")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def today() -> dt.date:
    return dt.date.today()


def iso(offset_days: int = 0) -> str:
    return (today() + dt.timedelta(days=offset_days)).isoformat()


def th_date(value: str) -> str:
    try:
        d = dt.date.fromisoformat(value[:10])
    except ValueError:
        return value or "-"
    return f"{d.day} {THAI_MONTHS[d.month - 1]} {d.year + 543}"


def th_datetime(value: str) -> str:
    return f"{th_date(value)} {value[11:16]} น." if len(value) >= 16 else th_date(value)


def calc_age(dob: str) -> int:
    try:
        b = dt.date.fromisoformat(dob)
    except ValueError:
        return 0
    t = today()
    return t.year - b.year - ((t.month, t.day) < (b.month, b.day))


def format_patient(p: dict[str, str]) -> dict[str, str]:
    """Add display fields (full_name, age, dob_th, registered_th) to a patient row."""
    age = calc_age(p.get("dob", ""))
    return {
        **p,
        "full_name": f"{p['first_name']} {p['last_name']}".strip(),
        "age": str(age) if p.get("dob") else "-",
        "dob_th": th_date(p["dob"]) if p.get("dob") else "-",
        "registered_th": th_date(p.get("registered", "")),
    }


def format_appointment(a: dict[str, str]) -> dict[str, str]:
    """Add display fields (date_th, weekday) to an appointment row."""
    return {**a, "date_th": th_date(a["date"]), "weekday": THAI_DAYS_FULL[dt.date.fromisoformat(a["date"]).isoweekday() - 1]}


def format_entry(e: dict[str, str]) -> dict[str, str]:
    """Add display fields (icd_th, tooth_label, ts_th) to a treatment entry row."""
    return {**e, "icd_th": ICD10_TH.get(e["icd"], "-"), "tooth_label": tooth_label(e["tooth"]), "ts_th": th_datetime(e["timestamp"])}


TIME_OPTIONS = [f"{h:02d}:{m:02d}" for h in range(7, 21) for m in (0, 30)]


# ---------------------------------------------------------------------------
# state
# ---------------------------------------------------------------------------
def not_connected(action: str):
    """Shown wherever a backend call is still missing."""
    return rx.toast.info(f"{action}: รอเชื่อมต่อระบบหลังบ้าน (backend)")

SLOT_TIMES = [
    "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
    "12:00", "12:30", "13:00", "13:30", "14:00", "14:30", "15:00",
    "15:30", "16:00", "16:30", "17:00", "17:30", "18:00",
    "18:30", "19:00", "19:30", "20:00"
]

def generate_default_slots() -> list[dict[str, str]]:
    return [
        {"time": t, "left": "2", "available": "1", "period": "เช้า" if int(t[:2]) < 13 else "บ่าย"}
        for t in SLOT_TIMES
    ]

class AppState(rx.State):
    patients: list[dict[str, str]] = []
    dentists: list[dict[str, str]] = []
    appointments: list[dict[str, str]] = []
    entries: list[dict[str, str]] = []

    @rx.event
    def check_staff_access(self):
        """ตรวจสอบสิทธิ์: ถ้าไม่ใช่เจ้าหน้าที่/หมอ ให้เด้งกลับหน้าโปรไฟล์"""
        if not self.is_logged_in:
            return rx.redirect("/login")
        if self.user_role not in ("staff", "dentist", "admin"):
            return [
                rx.toast.error("คุณไม่มีสิทธิ์เข้าถึงหน้านี้"),
                rx.redirect("/profile"),
            ]

    # ---- session (5.1) ----
    user_role: str = ""
    user_name: str = ""
    user_email: str = ""
    current_patient_id: str = ""
    login_role: str = "patient"
    login_error: str = ""
    register_error: str = ""
    reset_step: int = 1
    reset_email: str = ""
    reset_error: str = ""

    # ---- member (5.2) ----
    password_error: str = ""
    privacy: dict[str, bool] = {
        "share_history": True,
        "mask_name": True,
        "research": False,
    }

    # ---- booking (5.3 customer) ----
    booking_date: str = iso(1)
    booking_time: str = ""
    booking_service: str = SERVICES[0]
    booking_dentist: str = "ไม่ระบุ"
    booking_draft: dict[str, str] = {}
    booking_slip: dict[str, str] = {}
    my_appt_tab: str = "upcoming"
    slip: dict[str, str] = {}
    slip_open: bool = False

    # ---- staff (5.3) ----
    dashboard_date: str = iso()
    reject_target: str = ""
    reject_open: bool = False
    appt_filter: str = "ทั้งหมด"
    appt_search: str = ""
    resched_target: dict[str, str] = {}
    resched_open: bool = False
    next_appt_open: bool = False
    next_appt_patient: str = ""
    schedule_dentist_id: str = ""
    new_leave_date: str = ""
    new_leave_reason: str = ""                   
    schedule_selected_month: str = "2026-10"

    # ---- treatment (5.4) ----
    selected_patient_id: str = ""
    selected_tooth: str = ""
    entry_tooth: str = ""
    tooth_input_mode: str = "dropdown"
    entry_icd: str = ""
    entry_procedure: str = PROCEDURES[0]
    entry_note: str = ""
    my_selected_tooth: str = ""

    # --- ตัวแปรสำหรับผังฟัน (Dental Chart) ---
    chart_mode: str = "adult"        # 'adult' (ฟันแท้) หรือ 'child' (ฟันน้ำนม)
    selected_tooth: str = ""         # ซี่ฟันที่เลือก
    my_selected_tooth: str = ""      # ซี่ฟันที่คนไข้เลือกดูในหน้า my_history

    @rx.event
    def set_chart_mode(self, mode: str):
        """สลับระหว่างผังฟันแท้และผังฟันน้ำนมด้วยตนเองผ่าน Dropdown."""
        self.chart_mode = mode
        self.selected_tooth = ""
        self.entry_tooth = ""

    @rx.event
    def select_tooth(self, tooth_num: str):
        if self.selected_tooth == tooth_num:
            self.selected_tooth = ""
        else:
            self.selected_tooth = tooth_num

    @rx.event
    def select_my_tooth(self, tooth_num: str):
        if self.my_selected_tooth == tooth_num:
            self.my_selected_tooth = ""
        else:
            self.my_selected_tooth = tooth_num

    @rx.var
    def active_teeth_upper(self) -> list[str]:
        if self.chart_mode == "child":
            return PRIMARY_TEETH_UPPER
        return PERMANENT_TEETH_UPPER

    @rx.var
    def active_teeth_lower(self) -> list[str]:
        if self.chart_mode == "child":
            return PRIMARY_TEETH_LOWER
        return PERMANENT_TEETH_LOWER

    @rx.var
    def selected_tooth_label(self) -> str:
        """แปลงรหัสฟันที่หมอ/สตาฟเลือก เป็นข้อความอ่านง่าย"""
        if not self.selected_tooth:
            return ""
        return tooth_label(self.selected_tooth)

    @rx.var
    def my_selected_tooth_label(self) -> str:
        """แปลงรหัสฟันที่คนไข้เลือกใน my_history เป็นข้อความอ่านง่าย"""
        if not self.my_selected_tooth:
            return ""
        return tooth_label(self.my_selected_tooth)

    @rx.event
    def set_selected_pid(self, pid: str):
        self.selected_pid = pid
        self.selected_tooth = ""
        self.entry_tooth = ""
        self.update_chart_mode_for_patient(pid)

    def update_chart_mode_for_patient(self, pid: str):
        """ตรวจสอบว่าคนไข้เป็นเคสเด็กหรือไม่ (จากอายุ < 12 ปี หรือมีการจองทันตกรรมเด็ก)"""
        with rx.session() as session:
            # 1. ตรวจสอบข้อมูลคนไข้ (อายุ)
            pt = session.exec(
                select(Patient).where(Patient.pid == pid)
            ).first()
            
            is_kid = False
            if pt and hasattr(pt, "age") and pt.age is not None:
                try:
                    if int(pt.age) <= 12:  # อายุไม่เกิน 12 ปี ให้เป็นฟันน้ำนม
                        is_kid = True
                except Exception:
                    pass

            # 2. ตรวจสอบจากประวัติการจองคิวล่าสุด
            booking = session.exec(
                select(QueueBooking)
                .where(QueueBooking.patient_id == pid)
                .order_by(QueueBooking.id.desc())
            ).first()

            if booking:
                svc = str(booking.service or "")
                note_text = str(booking.purpose or "") + str(booking.note or "")
                if "เด็ก" in svc or "ฟันน้ำนม" in svc or "เด็ก" in note_text:
                    is_kid = True

            # สลับโหมด
            if is_kid:
                self.chart_mode = "child"
            else:
                self.chart_mode = "adult"

    @rx.var
    def is_child_case(self) -> bool:
        """ตรวจสอบว่าคนไข้ปัจจุบันเป็นเคสเด็กหรือไม่ (จากอายุ <= 12 ปี หรือจองคิวทันตกรรมเด็ก)."""
        pid = getattr(self, "selected_pid", "")
        if not pid:
            return False

        try:
            with rx.session() as session:
                # 1. เช็กอายุจากตาราง Patient โดยตรง
                pt = session.exec(
                    select(Patient).where(Patient.pid == pid)
                ).first()
                if pt and hasattr(pt, "age") and pt.age is not None:
                    try:
                        if int(pt.age) <= 12:
                            return True
                    except (ValueError, TypeError):
                        pass

                # 2. เช็กจากการจองคิวใน QueueBooking ของคนไข้รายนี้
                booking = session.exec(
                    select(QueueBooking)
                    .where(QueueBooking.patient_id == pid)
                    .order_by(QueueBooking.id.desc())
                ).first()
                if booking:
                    svc = str(getattr(booking, "service", "") or "")
                    purpose = str(getattr(booking, "purpose", "") or "")
                    note = str(getattr(booking, "note", "") or "")
                    text = f"{svc} {purpose} {note}"
                    if "เด็ก" in text or "ฟันน้ำนม" in text:
                        return True
        except Exception:
            pass

        return False

    @rx.var
    def my_weekly_schedule(self) -> list[dict]:
        """ดึงตารางเวร 7 วัน (จันทร์-อาทิตย์) ของทันตแพทย์ พร้อมวันที่จริง คืนค่าเป็น list[dict]"""
        import datetime

        # หาวันจันทร์ของสัปดาห์ปัจจุบัน (Monday = 0)
        today = datetime.date.today()
        start_of_week = today - datetime.timedelta(days=today.weekday())

        thai_months = [
            "", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
            "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."
        ]

        days_info = [
            {"day": "จันทร์", "day_num": "1", "bg": "#FEFCE8", "border": "#EAB308", "text_color": "#854D0E"},
            {"day": "อังคาร", "day_num": "2", "bg": "#FDF2F8", "border": "#EC4899", "text_color": "#9D174D"},
            {"day": "พุธ", "day_num": "3", "bg": "#F0FDF4", "border": "#22C55E", "text_color": "#166534"},
            {"day": "พฤหัสบดี", "day_num": "4", "bg": "#FFF7ED", "border": "#F97316", "text_color": "#9A3412"},
            {"day": "ศุกร์", "day_num": "5", "bg": "#F0F9FF", "border": "#0EA5E9", "text_color": "#075985"},
            {"day": "เสาร์", "day_num": "6", "bg": "#FAF5FF", "border": "#A855F7", "text_color": "#6B21A8"},
            {"day": "อาทิตย์", "day_num": "7", "bg": "#FEF2F2", "border": "#EF4444", "text_color": "#991B1B"},
        ]

        d = self.schedule_dentist
        work_days = d.get("days", []) if isinstance(d, dict) else getattr(d, "days", [])
        time_str = f"{d.get('start', '09:00')} - {d.get('end', '15:00')} น." if isinstance(d, dict) else f"{getattr(d, 'start', '09:00')} - {getattr(d, 'end', '15:00')} น."

        result: list[dict] = []
        for i, info in enumerate(days_info):
            current_date = start_of_week + datetime.timedelta(days=i)
            date_label = f"{current_date.day} {thai_months[current_date.month]}"
            is_work = "1" if info["day_num"] in work_days else "0"

            result.append({
                "day": info["day"],
                "date_label": date_label,
                "is_work": is_work,
                "time": time_str,
                "bg": info["bg"],
                "border": info["border"],
                "text_color": info["text_color"],
            })

        return result

    # ======================================================================
    # computed: session
    # ======================================================================
    @rx.var
    def is_logged_in(self) -> bool:
        return self.user_role != ""

    @rx.var
    def is_patient(self) -> bool:
        return self.user_role == "patient"

    @rx.var
    def is_staff(self) -> bool:
        return self.user_role == "staff"

    @rx.var
    def user_initials(self) -> str:
        name = self.user_name.replace("ทพญ. ", "").replace("ทพ. ", "").replace("พย. ", "")
        return name[:2] if name else "?"

    @rx.var
    def today_iso(self) -> str:
        return iso()

    @rx.var
    def today_th(self) -> str:
        return th_date(iso())

    @rx.var
    def me(self) -> dict[str, str]:
        return next((p for p in self.patients if p["id"] == self.current_patient_id), {})

    @rx.var
    def patient_options(self) -> list[str]:
        if not self.patients:
            return ["ยังไม่มีข้อมูลผู้ป่วยในระบบ"]
        return [f"{p['id']} · {p.get('full_name', '')}" for p in self.patients]

    @rx.var
    def next_appt_option(self) -> str:
        p = next((p for p in self.patients if p["id"] == self.next_appt_patient), None)
        return f"{p['id']} · {p['full_name']}" if p else ""

    @rx.var
    def dentist_names(self) -> list[str]:
        """รายชื่อทันตแพทย์จริง (ตัดทันตแพทย์เวรออก)"""
        if self.dentists:
            return [d["name"] for d in self.dentists]
        return [
            "ทพ. สมศักดิ์ รักฟัน",
            "ทพญ. วารี สดใส",
        ]

    @rx.var
    def active_dentists_for_selected_date(self) -> list[str]:
        """กรองเฉพาะหมอที่เข้าเวรในวันที่คนไข้เลือก"""
        try:
            target_d = dt.date.fromisoformat(self.booking_date)
            weekday_str = str(target_d.isoweekday())
        except Exception:
            weekday_str = "1"

        active = []
        for d in self.dentists:
            work_days = [x for x in d.get("days", "").split(",") if x]
            # ตรวจสอบวันลา
            leaves = []
            try:
                leaves_data = json.loads(d.get("leaves", "[]"))
                leaves = [x.get("date") for x in leaves_data if isinstance(x, dict)]
            except Exception:
                leaves = [x for x in d.get("leaves", "").split(",") if x]

            if weekday_str in work_days and self.booking_date not in leaves:
                active.append(d["name"])
        return active if active else ["ไม่มีแพทย์เข้าเวรในวันนี้"]

    @rx.var
    def booking_dentist_options(self) -> list[str]:
        """แสดงตัวเลือก 'ไม่ระบุ' พร้อมรายชื่อทันตแพทย์ทุกคนในระบบ"""
        names = []

        # 1. ดึงจากรายการทันตแพทย์ใน state
        if self.dentists:
            names = [d["name"] for d in self.dentists if d.get("name")]

        # 2. หากยังไม่ถูกโหลด ให้ดึงตรงจากตาราง User ที่มี role เป็น 'dentist'
        if not names:
            with rx.session() as session:
                docs = session.exec(select(User).where(User.role == "dentist")).all()
                names = [u.full_name for u in docs if u.full_name]

        # 3. กำจัดชื่อซ้ำ (ถ้ามี)
        unique_names = list(dict.fromkeys(names))

        return ["ไม่ระบุ"] + unique_names

    # ======================================================================
    # computed: booking (customer)
    # ======================================================================
    @rx.var
    def booking_days(self) -> list[dict[str, str]]:
        """คำนวณสถานะ 14 วันข้างหน้าโดยแยกตารางตรวจตามเดือนจริงของแต่ละวัน"""
        days = []
        target_dentist = self.booking_dentist if self.booking_dentist != "ไม่ระบุ" else None

        with rx.session() as session:
            # ดึงตารางงานทั้งหมดมาเตรียมไว้เพื่อคำนวณข้ามเดือน
            all_schedules = session.exec(select(DoctorSchedule)).all()

            for offset in range(0, 14):
                d = today() + dt.timedelta(days=offset)
                iso_str = d.isoformat()
                weekday_num = str(d.isoweekday())  # 1=จันทร์ ... 7=อาทิตย์
                month_str = d.strftime("%Y-%m")    # เช่น "2026-10" หรือ "2026-11"

                is_closed = False

                # กรองตารางของเดือนนั้นๆ
                month_scheds = [s for s in all_schedules if s.schedule_month == month_str]

                if target_dentist:
                    # กรณีระบุแพทย์
                    doc_sched = next((s for s in month_scheds if s.dentist_name == target_dentist), None)
                    if doc_sched:
                        work_days = [x for x in doc_sched.work_days.split(",") if x]
                        leaves = []
                        try:
                            leaves_data = json.loads(doc_sched.leaves)
                            leaves = [x.get("date") for x in leaves_data if isinstance(x, dict)]
                        except Exception:
                            leaves = [x for x in doc_sched.leaves.split(",") if x]

                        if (weekday_num not in work_days) or (iso_str in leaves):
                            is_closed = True
                    else:
                        # ถ้าเดือนนั้นยังไม่เคยตั้งค่า ให้ใช้ค่าเริ่มต้น (จันทร์-ศุกร์)
                        if weekday_num in ["6", "7"]:
                            is_closed = True
                else:
                    # กรณี "ไม่ระบุ" แพทย์ (เปิดตามวันทำการของคลินิก)
                    if month_scheds:
                        # มีแพทย์คนใดคนหนึ่งเข้าเวรหรือไม่
                        any_working = False
                        for s in month_scheds:
                            w_days = [x for x in s.work_days.split(",") if x]
                            l_dates = []
                            try:
                                l_objs = json.loads(s.leaves)
                                l_dates = [x.get("date") for x in l_objs if isinstance(x, dict)]
                            except Exception:
                                l_dates = [x for x in s.leaves.split(",") if x]

                            if (weekday_num in w_days) and (iso_str not in l_dates):
                                any_working = True
                                break
                        if not any_working:
                            is_closed = True
                    else:
                        # ถ้าเดือนใหม่ยังไม่ได้ตั้งค่า คลินิกเปิดวันจันทร์-ศุกร์ เป็นค่าเริ่มต้น
                        if weekday_num in ["6", "7"]:
                            is_closed = True

                days.append({
                    "iso": iso_str,
                    "weekday": THAI_DAYS[d.isoweekday() - 1],
                    "day": str(d.day),
                    "month": THAI_MONTHS[d.month - 1],
                    "free": "",
                    "closed": "1" if is_closed else "0",
                })

        return days

    @rx.var
    def booking_slots(self) -> list[dict[str, str]]:
        return self.available_slots

    @rx.var
    def available_slots(self) -> list[dict[str, str]]:
        """คำนวณคิวว่างและช่วงเวลา โดยจะลดคิวลงเฉพาะเมื่อ 'ยืนยันการจอง' หรือ 'ออกใบนัดหมาย' แล้วเท่านั้น"""
        slots = []
        MAX_CAPACITY = 2  # คลินิกรองรับได้รอบละ 2 คิว

        STANDARD_BREAKS = {"12:00", "12:30", "17:30", "18:00"}

        try:
            target_d = dt.date.fromisoformat(self.booking_date)
            weekday_str = str(target_d.isoweekday())
            target_month = target_d.strftime("%Y-%m")
        except Exception:
            target_d = today()
            weekday_str = "1"
            target_month = "2026-10"

        with rx.session() as session:
            # 1. ดึงคิวออนไลน์เฉพาะรายการที่ได้รับการยืนยันแล้ว หรือคนไข้มาตามนัดแล้ว (ไม่รวม 'รออนุมัติ')
            confirmed_bookings = session.exec(
                select(QueueBooking).where(
                    QueueBooking.booking_date == target_d,
                    QueueBooking.status.in_(["ยืนยันแล้ว", "มาตามนัด", "มาตามเวลานัด"])
                )
            ).all()

            # 2. ดึงใบนัดหมาย (Appointment) ในวันเดียวกันที่ยังไม่ถูกยกเลิก
            confirmed_appointments = session.exec(
                select(Appointment).where(
                    Appointment.appointment_date == target_d,
                    Appointment.status.not_in(["ยกเลิก", "ยกเลิกนัด", "ปฏิเสธ"])
                )
            ).all()

            is_unspecified = (not self.booking_dentist) or (self.booking_dentist == "ไม่ระบุ")
            sched = None

            if not is_unspecified:
                sched = session.exec(
                    select(DoctorSchedule).where(
                        DoctorSchedule.dentist_name == self.booking_dentist,
                        DoctorSchedule.schedule_month == target_month,
                    )
                ).first()

            for slot_time in SLOT_TIMES:
                # นับคิวจากคำขอจองคิวออนไลน์ที่ได้รับการอนุมัติแล้ว
                count_from_queue = sum(
                    1 for b in confirmed_bookings
                    if (
                        (hasattr(b.booking_time, "strftime") and b.booking_time.strftime("%H:%M") == slot_time)
                        or str(b.booking_time)[:5] == slot_time
                    )
                    and (
                        is_unspecified 
                        or getattr(b, "dentist_name", "") in ("", "ไม่ระบุ") 
                        or getattr(b, "dentist_name", "") == self.booking_dentist
                    )
                )

                # นับคิวจากการออกใบนัดหมายล่วงหน้า (Appointment)
                count_from_appt = sum(
                    1 for a in confirmed_appointments
                    if (
                        (hasattr(a.appointment_time, "strftime") and a.appointment_time.strftime("%H:%M") == slot_time)
                        or str(a.appointment_time)[:5] == slot_time
                    )
                )

                booked_count = count_from_queue + count_from_appt
                remain = max(0, MAX_CAPACITY - booked_count)

                # ตรวจสอบเวลาทำการของคลินิกและตารางแพทย์
                in_working_hours = True
                if slot_time in STANDARD_BREAKS:
                    in_working_hours = False
                elif not is_unspecified and sched:
                    work_days = [x for x in sched.work_days.split(",") if x]
                    leaves = []
                    try:
                        leave_objs = json.loads(sched.leaves)
                        leaves = [x.get("date") for x in leave_objs if isinstance(x, dict)]
                    except Exception:
                        leaves = [x for x in sched.leaves.split(",") if x]

                    if (weekday_str not in work_days) or (self.booking_date in leaves):
                        in_working_hours = False
                    elif not (sched.start_time <= slot_time < sched.end_time):
                        in_working_hours = False

                is_available = (remain > 0) and in_working_hours

                if not in_working_hours:
                    label_text = "นอกเวลาทำการ"
                elif remain == 0:
                    label_text = "เต็ม"
                else:
                    label_text = f"ว่าง {remain} คิว"

                slots.append({
                    "time": slot_time,
                    "label": label_text,
                    "available": "1" if is_available else "0",
                })

        return slots
    
    @rx.var
    def booking_date_th(self) -> str:
        d = dt.date.fromisoformat(self.booking_date)
        return f"วัน{THAI_DAYS_FULL[d.isoweekday() - 1]}ที่ {th_date(self.booking_date)}"

    @rx.var
    def my_upcoming(self) -> list[dict[str, str]]:
        items = [a for a in self.appointments if a["patient_id"] == self.current_patient_id
                 and a["date"] >= iso() and a["status"] in ACTIVE_STATUSES]
        return sorted(items, key=lambda a: (a["date"], a["time"]))

    @rx.var
    def my_past(self) -> list[dict[str, str]]:
        items = [a for a in self.appointments if a["patient_id"] == self.current_patient_id
                 and not (a["date"] >= iso() and a["status"] in ACTIVE_STATUSES)]
        return sorted(items, key=lambda a: (a["date"], a["time"]), reverse=True)

    @rx.var
    def has_booking_slip(self) -> bool:
        return bool(self.booking_slip)

    @rx.var
    def has_booking_draft(self) -> bool:
        return bool(self.booking_draft)

    @rx.var
    def has_my_next(self) -> bool:
        return bool(self.my_upcoming)

    @rx.var
    def my_next(self) -> dict[str, str]:
        return self.my_upcoming[0] if self.my_upcoming else {}

    # ======================================================================
    # computed: staff (5.3)
    # ======================================================================
    @rx.var
    def dashboard_date_th(self) -> str:
        return th_date(self.dashboard_date)

    @rx.var
    def daily_patients(self) -> list[dict[str, str]]:
        items = [a for a in self.appointments if a["date"] == self.dashboard_date and a["status"] not in ("ปฏิเสธ",)]
        return sorted(items, key=lambda a: a["time"])

    @rx.var
    def daily_stats(self) -> dict[str, int]:
        rows = self.daily_patients
        return {
            "total": sum(1 for a in rows if a["status"] != "ยกเลิกนัด"),
            "arrived": sum(1 for a in rows if a["status"] in ("มาตามนัด", "มาตามเวลานัด")),
            "waiting": sum(1 for a in rows if a["status"] in ("ยืนยันแล้ว", "เลื่อนนัด")),
            "pending": sum(1 for a in rows if a["status"] == "รออนุมัติ"),
            "cancelled": sum(1 for a in rows if a["status"] == "ยกเลิกนัด"),
        }

    @rx.var
    def pending_requests(self) -> list[dict[str, str]]:
        return sorted((a for a in self.appointments if a["status"] == "รออนุมัติ"), key=lambda a: (a["date"], a["time"]))

    @rx.var
    def pending_count(self) -> int:
        return len(self.pending_requests)

    @rx.var
    def recent_decisions(self) -> list[dict[str, str]]:
        items = [a for a in self.appointments if a["kind"] == "จองคิว" and a["status"] in ("ยืนยันแล้ว", "ปฏิเสธ") and a["date"] >= iso()]
        return sorted(items, key=lambda a: (a["date"], a["time"]))

    @rx.var
    def managed_appointments(self) -> list[dict[str, str]]:
        items = [a for a in self.appointments if a["status"] not in ("รออนุมัติ", "ปฏิเสธ")]
        if self.appt_filter == "วันนี้":
            items = [a for a in items if a["date"] == iso()]
        elif self.appt_filter == "ที่จะถึง":
            items = [a for a in items if a["date"] >= iso() and a["status"] in ACTIVE_STATUSES]
        elif self.appt_filter in APPT_STATUSES:
            items = [a for a in items if a["status"] == self.appt_filter]
        q = self.appt_search.strip().lower()
        if q:
            items = [a for a in items if q in a["patient_name"].lower() or q in a["phone"] or q in a["id"].lower()]
        return sorted(items, key=lambda a: (a["date"], a["time"]))

    @rx.var
    def schedule_dentist(self) -> dict[str, str]:
        return next((d for d in self.dentists if d["id"] == self.schedule_dentist_id), {})

    @rx.var
    def schedule_days(self) -> list[str]:
        doc = self.schedule_dentist
        if not doc:
            return []
        return [x for x in doc.get("days", "").split(",") if x]
    
    @rx.var
    def schedule_leaves(self) -> list[dict[str, str]]:
        leaves = [x for x in self.schedule_dentist.get("leaves", "").split(",") if x]
        return [{"iso": x, "th": th_date(x)} for x in sorted(leaves)]

    @rx.var
    def schedule_preview(self) -> list[str]:
        d = self.schedule_dentist
        if not d:
            return []
        lunch_end = f"{int(d['lunch'][:2]) + 1:02d}{d['lunch'][2:]}" if d.get("lunch") else ""
        return [t for t in TIME_OPTIONS if d["start"] <= t < d["end"] and not (lunch_end and d["lunch"] <= t < lunch_end)]

    @rx.var
    def week_overview(self) -> list[dict[str, str]]:
        rows = []
        for i, name in enumerate(THAI_DAYS_FULL, start=1):
            working = [d["name"] for d in self.dentists if str(i) in d["days"].split(",")]
            rows.append({"day": name, "dentists": ", ".join(working) if working else "ปิดทำการ", "open": "1" if working else "0"})
        return rows

    # ======================================================================
    # computed: treatment (5.4)
    # ======================================================================
    @rx.var
    def selected_patient(self) -> dict[str, str]:
        # fall back to the first registered patient so staff pages always show someone
        match = next((p for p in self.patients if p["id"] == self.selected_patient_id), None)
        return match or (self.patients[0] if self.patients else {})

    @rx.var
    def has_patients(self) -> bool:
        return bool(self.patients)

    @rx.var
    def selected_pid(self) -> str:
        return self.selected_patient.get("id", "")

    @rx.var
    def selected_patient_option(self) -> str:
        p = self.selected_patient
        if not p:
            return ""
        name = p.get("full_name") or f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
        return f"{p.get('id', '')} · {name}" if name else p.get("id", "")

    @rx.var
    def sel_entries(self) -> list[dict[str, str]]:
        return sorted((e for e in self.entries if e["patient_id"] == self.selected_pid), key=lambda e: e["timestamp"], reverse=True)

    @rx.var
    def sel_treated_teeth(self) -> list[str]:
        return list({e["tooth"] for e in self.sel_entries})

    @rx.var
    def sel_tooth_entries(self) -> list[dict[str, str]]:
        return [e for e in self.sel_entries if e["tooth"] == self.selected_tooth]

    @rx.var
    def selected_tooth_label(self) -> str:
        return tooth_label(self.selected_tooth)

    @rx.var
    def entry_tooth_label(self) -> str:
        return tooth_label(self.entry_tooth) if self.entry_tooth else "ยังไม่ได้เลือกซี่ฟัน"

    @rx.var
    def has_entry_icd(self) -> bool:
        return self.entry_icd != ""

    @rx.var
    def entry_icd_info(self) -> dict[str, str]:
        for code, th, en in ICD10:
            if code == self.entry_icd:
                return {"code": code, "th": th, "en": en}
        return {}

    @rx.var
    def sel_appointments(self) -> list[dict[str, str]]:
        return sorted((a for a in self.appointments if a["patient_id"] == self.selected_pid), key=lambda a: (a["date"], a["time"]), reverse=True)

    @rx.var
    def sel_summary(self) -> dict[str, str]:
        entries = self.sel_entries
        appts = self.sel_appointments
        return {
            "visits": str(len({e["timestamp"][:10] for e in entries})),
            "teeth": str(len(self.sel_treated_teeth)),
            "entries": str(len(entries)),
            "last_visit": th_date(entries[0]["timestamp"]) if entries else "-",
            "no_show": str(sum(1 for a in appts if a["status"] == "ยกเลิกนัด")),
            "next": next((f"{a['date_th']} {a['time']}" for a in sorted(appts, key=lambda a: (a["date"], a["time"]))
                          if a["date"] >= iso() and a["status"] in ACTIVE_STATUSES), "-"),
        }

    @rx.var
    def sel_diagnoses(self) -> list[dict[str, str]]:
        seen: dict[str, dict[str, str]] = {}
        for e in self.sel_entries:
            seen.setdefault(e["icd"], {"code": e["icd"], "th": e["icd_th"], "count": "0"})
            seen[e["icd"]]["count"] = str(int(seen[e["icd"]]["count"]) + 1)
        return list(seen.values())

    # customer side of the chart
    @rx.var
    def my_entries(self) -> list[dict[str, str]]:
        valid_pids = {self.current_patient_id, self.current_patient_id.replace("P-00", "").replace("P-0", "").replace("P-", "")}
        return sorted(
            (e for e in self.entries if e["patient_id"] in valid_pids or e["patient_id"] == self.current_patient_id),
            key=lambda e: e["timestamp"],
            reverse=True,
        )

    @rx.var
    def my_treated_teeth(self) -> list[str]:
        return list({e["tooth"] for e in self.my_entries})

    @rx.var
    def my_tooth_entries(self) -> list[dict[str, str]]:
        return [e for e in self.my_entries if e["tooth"] == self.my_selected_tooth]

    @rx.var
    def my_selected_tooth_label(self) -> str:
        return tooth_label(self.my_selected_tooth)

    # ======================================================================
    # internal helpers
    # ======================================================================
    def _find_appt(self, aid: str) -> dict[str, str]:
        for a in self.appointments:
            if a.get("id") == aid:
                return a
        return {}

    # ======================================================================
    # 5.1 register / login / forgot password / logout
    # ======================================================================
    @rx.event
    def set_login_role(self, value: str | list[str]):
        self.login_role = value if isinstance(value, str) else value[0]
        self.login_error = ""

    @rx.event
    def login(self, form: dict):
        """ตรวจสอบผู้ใช้ตาม Role และดึงเวชระเบียนของผู้ป่วยมาเก็บใน State"""
        self.login_error = ""
        email = (form.get("email") or form.get("username") or "").strip().lower()
        password = form.get("password") or ""

        if not email or not password:
            self.login_error = "กรุณากรอกอีเมลและรหัสผ่าน"
            return

        with rx.session() as session:
            user = session.exec(select(User).where(User.username == email)).first()
            if not user or user.password_hash != password:
                self.login_error = "อีเมลหรือรหัสผ่านไม่ถูกต้อง"
                return

            if self.login_role == "staff" and user.role not in ("staff", "dentist", "admin"):
                self.login_error = "บัญชีนี้ไม่มีสิทธิ์เข้าใช้งานในส่วนทันตแพทย์/เจ้าหน้าที่"
                return
            if self.login_role == "patient" and user.role != "patient":
                self.login_error = "บัญชีนี้ไม่ใช่บัญชีผู้ป่วย กรุณาเลือกแท็บหมอฟัน / พยาบาล"
                return

            self.user_role = user.role
            self.user_name = user.full_name
            self.user_email = user.username

            if user.role == "patient":
                patient = session.exec(
                    select(Patient).where(
                        (Patient.user_id == user.id) | (Patient.email == user.username)
                    )
                ).first()

                if patient:
                    self.current_patient_id = patient.hn_code
                    self.patients = [format_patient({
                        "id": patient.hn_code,
                        "db_id": str(patient.id),
                        "first_name": patient.first_name,
                        "last_name": patient.last_name,
                        "phone": patient.phone_number,
                        "dob": patient.birth_date.isoformat() if patient.birth_date else "",
                        "gender": patient.gender or "-",
                        "national_id": patient.national_id or "-",
                        "address": patient.address or "-",
                        "disease": patient.underlying_disease or "ไม่มี",
                        "allergy": patient.drug_allergy or "ไม่มี",
                        "registered": patient.created_at.isoformat() if patient.created_at else "",
                    })]

            self.load_patients_data()
            self.load_schedule_data()
            self.load_treatment_entries()  # โหลดประวัติการรักษาทันทีหลังเข้าสู่ระบบ

            if user.role in ("staff", "dentist", "admin"):
                return rx.redirect("/dashboard")
            return rx.redirect("/profile")

    @rx.event
    def register(self, form: dict):
        """สมัครสมาชิก: บันทึกข้อมูลลงตาราง User และสร้างเวชระเบียนใน Patient"""
        self.register_error = ""
        first_name = (form.get("first_name") or "").strip()
        last_name = (form.get("last_name") or "").strip()
        phone = (form.get("phone") or "").strip()
        email = (form.get("email") or "").strip().lower()
        password = form.get("password") or ""
        confirm = form.get("confirm") or ""

        if not first_name or not last_name or not phone or not email or not password:
            self.register_error = "กรุณากรอกข้อมูลที่มีเครื่องหมาย * ให้ครบถ้วน"
            return
        if password != confirm:
            self.register_error = "รหัสผ่านและการยืนยันรหัสผ่านไม่ตรงกัน"
            return
        if len(password) < 8:
            self.register_error = "รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร"
            return

        with rx.session() as session:
            # เช็กอีเมลซ้ำ
            existing_user = session.exec(select(User).where(User.username == email)).first()
            if existing_user:
                self.register_error = "อีเมลนี้ถูกใช้งานในระบบแล้ว"
                return

            # 1. บันทึกบัญชีผู้ใช้งาน
            new_user = User(
                username=email,
                password_hash=password,
                full_name=f"{first_name} {last_name}",
                role="patient",
                is_active=True,
                created_at=get_utc_now(),
            )
            session.add(new_user)
            session.commit()
            session.refresh(new_user)

            # แปลงวันเกิด
            dob_val = None
            if form.get("dob"):
                try:
                    dob_val = dt.date.fromisoformat(form.get("dob"))
                except ValueError:
                    pass

            # 2. บันทึกเวชระเบียนผู้ป่วย
            patient_count = len(session.exec(select(Patient)).all())
            hn_code = f"P-{patient_count + 1:04d}"

            new_patient = Patient(
                user_id=new_user.id,
                hn_code=hn_code,
                national_id=form.get("national_id") or None,
                first_name=first_name,
                last_name=last_name,
                email=email,
                birth_date=dob_val,
                gender=form.get("gender") or "ไม่ระบุ",
                phone_number=phone,
                address=form.get("address") or None,
                underlying_disease=form.get("disease") or "ไม่มี",
                drug_allergy=form.get("allergy") or "ไม่มี",
                created_at=get_utc_now(),
            )
            session.add(new_patient)
            session.commit()

        return [rx.toast.success("สมัครสมาชิกสำเร็จ กรุณาเข้าสู่ระบบ"), rx.redirect("/login")]

    @rx.event
    def request_reset(self, form: dict):
        """ขอรีเซ็ตรหัสผ่าน ตรวจสอบว่ามีอีเมลในฐานข้อมูลหรือไม่"""
        email = (form.get("email") or "").strip().lower()
        with rx.session() as session:
            user = session.exec(select(User).where(User.username == email)).first()
            if not user:
                self.reset_error = "ไม่พบบัญชีผู้ใช้งานที่ใช้อีเมลนี้"
                return
        self.reset_email = email
        self.reset_error = ""
        self.reset_step = 2
        return rx.toast.info("ระบบได้จำลองการส่งรหัสยืนยันไปยังอีเมลของท่านแล้ว")

    @rx.event
    def confirm_reset(self, form: dict):
        """ยืนยันการเปลี่ยนรหัสผ่านใหม่"""
        pw = form.get("password") or ""
        confirm = form.get("confirm") or ""
        otp = (form.get("otp") or "").strip()

        if len(pw) < 8 or pw != confirm:
            self.reset_error = "รหัสผ่านใหม่ต้องมีอย่างน้อย 8 ตัวอักษรและตรงกัน"
            return

        with rx.session() as session:
            user = session.exec(select(User).where(User.username == self.reset_email)).first()
            if not user:
                self.reset_error = "เกิดข้อผิดพลาด ไม่พบข้อมูลบัญชี"
                return
            user.password_hash = pw
            session.add(user)
            session.commit()

        self.reset_step = 3
        self.reset_error = ""
        return rx.toast.success("ตั้งรหัสผ่านใหม่เรียบร้อยแล้ว")

    @rx.event
    def restart_reset(self):
        self.reset_step = 1
        self.reset_error = ""
        self.reset_email = ""

    @rx.event
    def logout(self):
        """ออกจากระบบและล้างค่า Session ทั้งหมด"""
        self.user_role = ""
        self.user_name = ""
        self.user_email = ""
        self.current_patient_id = ""
        self.patients = []
        return [rx.toast.info("ออกจากระบบแล้ว"), rx.redirect("/")]

   # ======================================================================
    # 5.2 member management
    # ======================================================================
    @rx.event
    def save_profile(self, form: dict):
        """อัปเดตข้อมูลส่วนตัวและเวชระเบียนของผู้ป่วยที่ล็อกอินอยู่"""
        first_name = (form.get("first_name") or "").strip()
        last_name = (form.get("last_name") or "").strip()
        phone = (form.get("phone") or "").strip()

        with rx.session() as session:
            user = session.exec(select(User).where(User.username == self.user_email)).first()
            if not user:
                return rx.toast.error("ไม่พบบัญชีผู้ใช้งาน")

            patient = session.exec(select(Patient).where(
                (Patient.user_id == user.id) | (Patient.email == self.user_email)
            )).first()

            if patient:
                patient.first_name = first_name or patient.first_name
                patient.last_name = last_name or patient.last_name
                patient.phone_number = phone or patient.phone_number
                patient.address = form.get("address") or patient.address
                patient.underlying_disease = form.get("disease") or patient.underlying_disease
                patient.drug_allergy = form.get("allergy") or patient.drug_allergy
                session.add(patient)

            if first_name and last_name:
                user.full_name = f"{first_name} {last_name}"
                self.user_name = user.full_name
                session.add(user)

            session.commit()

        # อัปเดตข้อมูลบน State ทันที
        if self.patients:
            self.patients[0]["first_name"] = first_name
            self.patients[0]["last_name"] = last_name
            self.patients[0]["phone"] = phone
            self.patients[0]["address"] = form.get("address") or "-"
            self.patients[0]["disease"] = form.get("disease") or "ไม่มี"
            self.patients[0]["allergy"] = form.get("allergy") or "ไม่มี"
            self.patients[0]["full_name"] = f"{first_name} {last_name}".strip()

        return [rx.toast.success("บันทึกข้อมูลส่วนตัวสำเร็จ"), rx.redirect("/profile")]

    @rx.event
    def change_password(self, form: dict):
        """เปลี่ยนรหัสผ่านผู้ใช้งาน"""
        current_pw = form.get("current") or ""
        new_pw = form.get("new") or ""
        confirm_pw = form.get("confirm") or ""

        if len(new_pw) < 8:
            self.password_error = "รหัสผ่านใหม่ต้องมีอย่างน้อย 8 ตัวอักษร"
            return
        if new_pw != confirm_pw:
            self.password_error = "รหัสผ่านใหม่และการยืนยันไม่ตรงกัน"
            return
        if new_pw == current_pw:
            self.password_error = "รหัสผ่านใหม่ต้องไม่ซ้ำกับรหัสผ่านเดิม"
            return

        with rx.session() as session:
            user = session.exec(select(User).where(User.username == self.user_email)).first()
            if not user or user.password_hash != current_pw:
                self.password_error = "รหัสผ่านปัจจุบันไม่ถูกต้อง"
                return

            user.password_hash = new_pw
            session.add(user)
            session.commit()

        self.password_error = ""
        return rx.toast.success("เปลี่ยนรหัสผ่านเรียบร้อยแล้ว")

    @rx.event
    def set_privacy(self, key: str, value: bool):
        self.privacy = {**self.privacy, key: value}

    @rx.event
    def toggle_privacy(self, key: str):
        self.privacy = {**self.privacy, key: not self.privacy.get(key, False)}
        return rx.toast.info("อัปเดตการตั้งค่าความเป็นส่วนตัวแล้ว")

    @rx.event
    def download_my_data(self):
        """ส่งออกข้อมูลเวชระเบียนและประวัติการนัดหมายของผู้ป่วยเป็นไฟล์ JSON"""
        me_data = self.me
        my_history = self.my_upcoming + self.my_past
        export_payload = {
            "profile": me_data,
            "appointments": my_history,
            "exported_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        json_str = json.dumps(export_payload, ensure_ascii=False, indent=2)
        return rx.download(data=json_str, filename=f"patient_data_{self.current_patient_id}.json")

    # ======================================================================
    # 5.3 booking (customer)
    # ======================================================================
    @rx.event
    def pick_date(self, value: str):
        self.booking_date = value
        self.booking_time = ""

    @rx.event
    def pick_time(self, value: str):
        self.booking_time = value

    @rx.event
    def set_booking_service(self, value: str):
        self.booking_service = value

    @rx.event
    def set_booking_dentist(self, value: str):
        self.booking_dentist = value
        self.booking_time = ""

    @rx.event
    def submit_booking_details(self, form: dict):
        if not self.booking_time:
            return rx.toast.error("กรุณาเลือกช่วงเวลาที่ต้องการจอง")
        me = self.me
        self.booking_draft = format_appointment(dict(
            id="", kind="จองคิว", patient_id=me.get("id", ""),
            patient_name=(form.get("name") or me.get("full_name", "")).strip(),
            phone=(form.get("phone") or me.get("phone", "")).strip(),
            date=self.booking_date, time=self.booking_time, service=self.booking_service,
            dentist="" if self.booking_dentist == "ไม่ระบุ" else self.booking_dentist,
            status="รออนุมัติ", disease=(form.get("disease") or "").strip(), allergy=(form.get("allergy") or "").strip(),
            note=(form.get("note") or "").strip(), purpose="", reason="", created="",
        ))
        self.booking_slip = {}
        return rx.redirect("/booking/summary")

    @rx.event
    def confirm_booking(self):
        if not self.booking_draft:
            return rx.redirect("/booking")

        draft = self.booking_draft
        target_date = dt.date.fromisoformat(draft["date"])
        target_time = dt.datetime.strptime(draft["time"], "%H:%M").time()
        pid = self.current_patient_id if self.is_logged_in and self.current_patient_id else "1"

        with rx.session() as session:
            # ดึงรายการจองทั้งหมดในวันเดียวกัน
            day_bookings = session.exec(
                select(QueueBooking).where(
                    QueueBooking.booking_date == target_date,
                    QueueBooking.status.not_in(["ยกเลิก", "ยกเลิกนัด", "ปฏิเสธ"])
                )
            ).all()

            # บันทึกข้อมูลคิวใหม่ลงฐานข้อมูลชั่วคราว
           # บันทึกข้อมูลคิวใหม่ลงฐานข้อมูลชั่วคราว
            new_booking = QueueBooking(
                patient_id=pid,
                patient_name=draft["patient_name"],
                phone_number=draft["phone"],
                booking_date=target_date,
                booking_time=target_time,
                service_type=draft["service"],
                dentist_name=draft.get("dentist") or "ไม่ระบุ",  # <-- เพิ่มจุดนี้
                underlying_disease=draft.get("disease", "ไม่มี"),
                drug_allergy=draft.get("allergy", "ไม่มี"),
                status="รออนุมัติ",
                booking_code="",
                created_at=get_utc_now(),
            )
            session.add(new_booking)
            session.flush()

            # รวมคิวทั้งหมดในวันนั้น แล้วเรียงตามเวลาจอง
            all_today = list(day_bookings) + [new_booking]
            all_today.sort(key=lambda b: (b.booking_time, b.created_at))

            # ใช้รหัสที่มีวันที่กำกับ เช่น Q-20261102-001 เพื่อป้องกันการซ้ำกับวันอื่นในฐานข้อมูล
            date_prefix = target_date.strftime("%Y%m%d")
            assigned_code = ""
            for idx, booking_item in enumerate(all_today, start=1):
                queue_number_str = f"Q-{date_prefix}-{idx:03d}"
                booking_item.booking_code = queue_number_str
                session.add(booking_item)
                if booking_item.id == new_booking.id:
                    assigned_code = queue_number_str

            session.commit()
            session.refresh(new_booking)

            saved_draft = dict(draft)
            saved_draft["id"] = assigned_code
            saved_draft["patient_id"] = pid
            self.booking_slip = saved_draft
            self.booking_draft = {}
            self.booking_time = ""

        self.load_schedule_data()
        return rx.toast.success(f"จองคิวสำเร็จ (หมายเลขคิว: {assigned_code})")

    @rx.event
    def new_booking(self):
        self.booking_slip = {}
        return rx.redirect("/booking")

    @rx.event
    def set_my_appt_tab(self, value: str):
        self.my_appt_tab = value

    @rx.event
    def show_slip(self, aid: str):
        self.slip = self._find_appt(aid)
        self.slip_open = True

    @rx.event
    def set_slip_open(self, value: bool):
        self.slip_open = value

    @rx.event
    def cancel_my_appt(self, aid: str):
        """คนไข้ยกเลิกนัดหมายผ่านหน้า 'ตารางนัดหมายของฉัน'"""
        return self.cancel_appt(aid)

    @rx.event
    def download_ics(self, aid: str):
        a = self._find_appt(aid)
        if not a:
            return
        start = dt.datetime.strptime(f"{a['date']} {a['time']}", "%Y-%m-%d %H:%M")
        end = start + dt.timedelta(minutes=30)
        fmt = "%Y%m%dT%H%M%S"
        ics = "\r\n".join([
            "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Dental Guardian//TH", "BEGIN:VEVENT",
            f"UID:{a['id']}@dentalguardian", f"DTSTART:{start.strftime(fmt)}", f"DTEND:{end.strftime(fmt)}",
            f"SUMMARY:นัดทำฟัน - {a['service']}",
            f"DESCRIPTION:{a['id']} {a['dentist'] or 'Dental Guardian'} {a['purpose']}",
            "LOCATION:Dental Guardian", "BEGIN:VALARM", "TRIGGER:-P1D", "ACTION:DISPLAY",
            "DESCRIPTION:พรุ่งนี้มีนัดทำฟัน", "END:VALARM", "END:VEVENT", "END:VCALENDAR",
        ])
        return rx.download(data=ics, filename=f"{a['id']}.ics")

    @rx.event
    def export_ics(self):
        """ส่งออกไฟล์ .ics จากใบนัดหรือใบจองคิวที่กำลังเปิดดูอยู่"""
        target = self.slip if self.slip_open else self.booking_slip
        aid = target.get("id")
        if not aid:
            return rx.toast.error("ไม่พบนัดหมายที่จะส่งออกปฏิทิน")
        return self.download_ics(aid)

   # ======================================================================
    # 5.3 staff: dashboard, requests, appointments, schedule
    # ======================================================================
    @rx.event
    def set_dashboard_date(self, value: str):
        self.dashboard_date = value or iso()

    @rx.event
    def shift_dashboard_date(self, days: int):
        current = dt.date.fromisoformat(self.dashboard_date)
        self.dashboard_date = (current + dt.timedelta(days=days)).isoformat()

    @rx.event
    def load_patients_data(self):
        """ดึงข้อมูลผู้ป่วยทั้งหมดจากฐานข้อมูล SQLite เข้าสู่ State"""
        with rx.session() as session:
            db_patients = session.exec(select(Patient)).all()
            loaded = []
            for p in db_patients:
                loaded.append(format_patient({
                    "id": p.hn_code,
                    "db_id": str(p.id),
                    "first_name": p.first_name,
                    "last_name": p.last_name,
                    "phone": p.phone_number,
                    "dob": p.birth_date.isoformat() if p.birth_date else "",
                    "gender": p.gender or "-",
                    "national_id": p.national_id or "-",
                    "address": p.address or "-",
                    "disease": p.underlying_disease or "ไม่มี",
                    "allergy": p.drug_allergy or "ไม่มี",
                    "registered": p.created_at.isoformat() if p.created_at else "",
                }))
            self.patients = loaded

    @rx.event
    def set_schedule_selected_month(self, month_val: str):
        self.schedule_selected_month = month_val
        self.load_schedule_data()

    @rx.event
    def load_schedule_data(self):
        """โหลดข้อมูลหมอ ตารางงานประจำเดือน คิว และนัดหมายจากฐานข้อมูล SQLite"""
        with rx.session() as session:
            # 1. โหลดข้อมูลหมอและตารางงานประจำเดือนที่เลือก
            dentist_users = session.exec(select(User).where(User.role == "dentist")).all()
            loaded_dentists = []
            for u in dentist_users:
                uid = str(u.id)
                sched = session.exec(
                    select(DoctorSchedule).where(
                        DoctorSchedule.dentist_id == uid,
                        DoctorSchedule.schedule_month == self.schedule_selected_month,
                    )
                ).first()

                if sched:
                    days_val = sched.work_days
                    start_val = sched.start_time
                    end_val = sched.end_time
                    lunch_val = sched.lunch_time
                    leaves_val = sched.leaves
                else:
                    days_val = "1,2,3,4,5"
                    start_val = "09:00"
                    end_val = "18:00"
                    lunch_val = "12:00"
                    leaves_val = "[]"

                loaded_dentists.append({
                    "id": uid,
                    "name": u.full_name,
                    "specialty": "ทันตแพทย์ประจำคลินิก",
                    "month": self.schedule_selected_month,
                    "days": days_val,
                    "start": start_val,
                    "end": end_val,
                    "lunch": lunch_val,
                    "leaves": leaves_val,
                })

            self.dentists = loaded_dentists
            if not self.schedule_dentist_id and self.dentists:
                self.schedule_dentist_id = self.dentists[0]["id"]

            # 2. โหลด QueueBooking และ Appointment
            bookings = session.exec(select(QueueBooking)).all()
            appts = session.exec(select(Appointment)).all()
            db_entries = session.exec(select(TreatmentEntry)).all()
            
            loaded_list = []

            for b in bookings:
                loaded_list.append(format_appointment({
                    "id": b.booking_code,
                    "db_id": str(b.id),
                    "kind": "จองคิว",
                    "patient_id": getattr(b, "patient_id", "") or self.current_patient_id or "1",
                    "patient_name": b.patient_name,
                    "phone": b.phone_number,
                    "date": b.booking_date.isoformat(),
                    "time": b.booking_time.strftime("%H:%M") if hasattr(b.booking_time, "strftime") else str(b.booking_time)[:5],
                    "service": b.service_type,
                    "dentist": getattr(b, "dentist_name", "") or "ไม่ระบุ",  # <-- แก้ตรงนี้ให้ดึงจากฐานข้อมูล
                    "status": b.status,
                    "disease": b.underlying_disease or "-",
                    "allergy": b.drug_allergy or "-",
                    "note": "",
                    "purpose": "ตรวจฟัน/บริการทั่วไป",
                    "reason": "",
                    "created": b.created_at.isoformat() if b.created_at else "",
                }))

            for a in appts:
                loaded_list.append(format_appointment({
                    "id": a.appointment_slip_code,
                    "db_id": str(a.id),
                    "kind": "นัดหมาย",
                    "patient_id": str(a.id),
                    "patient_name": a.patient_name,
                    "phone": a.contact_info,
                    "date": a.appointment_date.isoformat(),
                    "time": a.appointment_time.strftime("%H:%M"),
                    "service": "ติดตามอาการ",
                    "dentist": "ทันตแพทย์ประจำคลินิก",
                    "status": a.status,
                    "disease": "-",
                    "allergy": "-",
                    "note": a.notes or "",
                    "purpose": a.purpose,
                    "reason": "",
                    "created": a.created_at.isoformat() if a.created_at else "",
                }))

            # โหลดประวัติการรักษาเข้าสู่ entries สำหรับแสดงบนผังฟัน
            loaded_entries = []
            for item in db_entries:
                loaded_entries.append(format_entry({
                    "id": str(item.id),
                    "patient_id": str(item.patient_id),
                    "tooth": str(item.tooth_number),
                    "icd": item.icd_code,
                    "procedure": item.procedure_name,
                    "note": item.notes or "",
                    "dentist": item.dentist_name or "ทันตแพทย์",
                    "timestamp": item.created_at.isoformat() if item.created_at else dt.datetime.now().isoformat(),
                }))

            self.appointments = loaded_list
            self.entries = loaded_entries

    @rx.var
    def monthly_calendar_days(self) -> list[dict]:
        """สร้างตารางปฏิทินรายเดือนเต็มรูปแบบ (มีช่องว่างต้นเดือน + วันที่ 1 ถึงสิ้นเดือน)."""
        import calendar
        import datetime

        month_str = getattr(self, "schedule_selected_month", "") or "2026-10"
        try:
            year, month = map(int, month_str.split("-"))
        except Exception:
            year, month = 2026, 10

        # วันแรกของเดือนเป็นวันอะไรในสัปดาห์ (0=Monday, 6=Sunday) และจำนวนวันในเดือนนั้น
        first_weekday, num_days = calendar.monthrange(year, month)

        # ข้อมูลทันตแพทย์ที่เลือก
        d = self.schedule_dentist
        work_days = d.get("days", []) if isinstance(d, dict) else getattr(d, "days", [])
        time_str = (
            f"{d.get('start', '09:00')} - {d.get('end', '15:00')} น."
            if isinstance(d, dict)
            else f"{getattr(d, 'start', '09:00')} - {getattr(d, 'end', '15:00')} น."
        )

        # ดึงรายการวันลาของเดือนนี้
        leave_map = {}
        for l in getattr(self, "schedule_leaves", []):
            ldate = l.get("date", "") if isinstance(l, dict) else getattr(l, "date", "")
            lreason = l.get("label", "ลาหยุด") if isinstance(l, dict) else getattr(l, "label", "ลาหยุด")
            if ldate:
                leave_map[ldate] = lreason

        # สีประจำวัน จันทร์-อาทิตย์ (1-7)
        day_styles = {
            1: {"border": "#EAB308", "bg": "#FEFCE8", "text": "#854D0E", "name": "จันทร์"},
            2: {"border": "#EC4899", "bg": "#FDF2F8", "text": "#9D174D", "name": "อังคาร"},
            3: {"border": "#22C55E", "bg": "#F0FDF4", "text": "#166534", "name": "พุธ"},
            4: {"border": "#F97316", "bg": "#FFF7ED", "text": "#9A3412", "name": "พฤหัสบดี"},
            5: {"border": "#0EA5E9", "bg": "#F0F9FF", "text": "#075985", "name": "ศุกร์"},
            6: {"border": "#A855F7", "bg": "#FAF5FF", "text": "#6B21A8", "name": "เสาร์"},
            7: {"border": "#EF4444", "bg": "#FEF2F2", "text": "#991B1B", "name": "อาทิตย์"},
        }

        calendar_cells = []

        # 1. ใส่ช่องว่างก่อนวันที่ 1 ของเดือนเพื่อให้ตรงกับวันในสัปดาห์
        for _ in range(first_weekday):
            calendar_cells.append({
                "day_num": "",
                "is_empty": True,
                "is_work": "0",
                "is_leave": False,
                "leave_reason": "",
                "time": "",
                "bg": "transparent",
                "border": "transparent",
                "text_color": "transparent",
            })

        # 2. ใส่ตั้งแต่วันที่ 1 จนถึงวันสุดท้ายของเดือน (28, 29, 30 หรือ 31)
        for day in range(1, num_days + 1):
            date_obj = datetime.date(year, month, day)
            # weekday: Monday=0, Sunday=6 -> แปลงเป็น 1-7
            day_num_week = date_obj.weekday() + 1
            date_iso = f"{year:04d}-{month:02d}-{day:02d}"

            st = day_styles.get(day_num_week, day_styles[1])
            is_work_regular = str(day_num_week) in work_days
            is_leave = date_iso in leave_map

            is_work_actual = "1" if (is_work_regular and not is_leave) else "0"

            calendar_cells.append({
                "day_num": str(day),
                "date_iso": date_iso,
                "is_empty": False,
                "is_work": is_work_actual,
                "is_leave": is_leave,
                "leave_reason": leave_map.get(date_iso, ""),
                "time": time_str,
                "bg": st["bg"] if is_work_actual == "1" else "#F8FAFC",
                "border": st["border"] if is_work_actual == "1" else "#E2E8F0",
                "text_color": st["text"] if is_work_actual == "1" else "var(--slate-9)",
            })

        return calendar_cells

    # ---- ช่วยค้นหานัดหมายตามรหัส ----
    def _find_appt(self, aid: str) -> dict[str, str]:
        for a in self.appointments:
            if a.get("id") == aid:
                return a
        return {}

    # ---- เปิดดูใบนัด (สำหรับปุ่ม "ใบนัด" สีม่วง) ----
    @rx.event
    def view_slip(self, aid: str):
        target = self._find_appt(aid)
        if target:
            self.slip = target
            self.slip_open = True

    @rx.event
    def set_slip_open(self, value: bool):
        self.slip_open = value

    # ---- รายการนัดหมายสำหรับหน้า "ตารางนัดหมายของฉัน" (/my-appointments) ----
    @rx.var
    def my_appointments(self) -> list[dict[str, str]]:
        """ดึงรายการนัดหมายเฉพาะของคนไข้ที่ล็อกอินอยู่ เรียงจากล่าสุดขึ้นก่อน"""
        user_appts = [
            a for a in self.appointments 
            if a.get("patient_id") == self.current_patient_id
        ]
        return list(reversed(user_appts))

    @rx.var
    def my_upcoming_appointments(self) -> list[dict[str, str]]:
        """ดึงนัดที่ยังไม่เสร็จสิ้น หรือรอตรวจ"""
        return [
            a for a in list(reversed(self.appointments))
            if a.get("status") in ["ยืนยันแล้ว", "รออนุมัติ", "เลื่อนนัด"]
        ]

    @rx.var
    def my_past_appointments(self) -> list[dict[str, str]]:
        return [
            a for a in self.appointments
            if a.get("status") in ["เสร็จสิ้น", "ยกเลิกนัด", "ปฏิเสธ"]
        ]

    @rx.event
    def approve_request(self, aid: str):
        with rx.session() as session:
            booking = session.exec(select(QueueBooking).where(QueueBooking.booking_code == aid)).first()
            if booking:
                booking.status = "ยืนยันแล้ว"
                session.add(booking)
                session.commit()
        self.load_schedule_data()
        return rx.toast.success(f"อนุมัติการจองรหัส {aid} สำเร็จ")

    @rx.event
    def open_reject(self, aid: str):
        self.reject_target = aid
        self.reject_open = True

    @rx.event
    def set_reject_open(self, value: bool):
        self.reject_open = value

    @rx.event
    def reject_request(self, form: dict):
        reason = form.get("reason", "ไม่ระบุเหตุผล")
        with rx.session() as session:
            booking = session.exec(
                select(QueueBooking).where(QueueBooking.booking_code == self.reject_target)
            ).first()
            if booking:
                session.delete(booking)
                session.commit()

        self.reject_open = False
        self.load_schedule_data()
        return rx.toast.info(f"ลบรายการที่ปฏิเสธเรียบร้อยแล้ว")

    @rx.event
    def set_appt_search(self, value: str):
        self.appt_search = value

    @rx.event
    def set_appt_filter(self, value: str | list[str]):
        self.appt_filter = value if isinstance(value, str) else value[0]

    @rx.event
    def cancel_booking(self, booking_id: str):
        """สำหรับคนไข้กดยกเลิกคิวตนเอง (ลบออกจากฐานข้อมูลทันที)"""
        with rx.session() as session:
            # ค้นหาด้วย booking_code หรือ id (เผื่อส่งค่ามาเป็นตัวเลข)
            booking = session.exec(
                select(QueueBooking).where(
                    (QueueBooking.booking_code == str(booking_id))
                    | (QueueBooking.id == (int(booking_id) if str(booking_id).isdigit() else -1))
                )
            ).first()

            if booking:
                target_date = booking.booking_date
                session.delete(booking)
                session.commit()

                # รันจัดเลขคิวใหม่ตามลำดับเวลาเช้าสุด โดยใส่วันที่กำกับป้องกันรหัสซ้ำ
                date_prefix = target_date.strftime("%Y%m%d")
                remaining = session.exec(
                    select(QueueBooking).where(QueueBooking.booking_date == target_date)
                ).all()
                all_rem = list(remaining)
                all_rem.sort(key=lambda b: (b.booking_time, b.created_at))
                for idx, item in enumerate(all_rem, start=1):
                    item.booking_code = f"Q-{date_prefix}-{idx:03d}"
                    session.add(item)
                session.commit()

        self.load_schedule_data()
        return rx.toast.info("ยกเลิกและลบคิวออกจากระบบเรียบร้อยแล้ว")

    @rx.event
    def cancel_appt(self, aid: str):
        """สำหรับเจ้าหน้าที่กดยกเลิกนัดหมายหรือคิว (ลบออกจากฐานข้อมูลทันที)"""
        with rx.session() as session:
            # 1. ค้นหาใน Appointment
            appt = session.exec(
                select(Appointment).where(
                    (Appointment.appointment_slip_code == str(aid))
                    | (Appointment.id == (int(aid) if str(aid).isdigit() else -1))
                )
            ).first()
            if appt:
                session.delete(appt)

            # 2. ค้นหาใน QueueBooking
            booking = session.exec(
                select(QueueBooking).where(
                    (QueueBooking.booking_code == str(aid))
                    | (QueueBooking.id == (int(aid) if str(aid).isdigit() else -1))
                )
            ).first()

            if booking:
                target_date = booking.booking_date
                session.delete(booking)
                session.commit()

                date_prefix = target_date.strftime("%Y%m%d")
                remaining = session.exec(
                    select(QueueBooking).where(QueueBooking.booking_date == target_date)
                ).all()
                all_rem = list(remaining)
                all_rem.sort(key=lambda b: (b.booking_time, b.created_at))
                for idx, item in enumerate(all_rem, start=1):
                    item.booking_code = f"Q-{date_prefix}-{idx:03d}"
                    session.add(item)
                session.commit()
            else:
                session.commit()

        self.load_schedule_data()
        return rx.toast.info("ยกเลิกและลบข้อมูลเรียบร้อยแล้ว")
    
    @rx.event
    def mark_arrived(self, aid: str):
        with rx.session() as session:
            appt = session.exec(select(Appointment).where(Appointment.appointment_slip_code == aid)).first()
            if appt:
                appt.status = "มาตามนัด"
                session.add(appt)
            booking = session.exec(select(QueueBooking).where(QueueBooking.booking_code == aid)).first()
            if booking:
                booking.status = "มาตามนัด"
                session.add(booking)
            session.commit()

        self.load_schedule_data()
        return rx.toast.success(f"บันทึกผู้ป่วยรหัส {aid} มาตามนัดแล้ว")

    @rx.event
    def open_reschedule(self, aid: str):
        self.resched_target = self._find_appt(aid)
        self.resched_open = True

    @rx.event
    def set_resched_open(self, value: bool):
        self.resched_open = value

    @rx.event
    def reschedule(self, form: dict):
        aid = self.resched_target.get("id")
        new_date_str = form.get("date")
        new_time_str = form.get("time")

        if not new_date_str or not new_time_str:
            return rx.toast.error("กรุณาระบุวันและเวลาใหม่")

        with rx.session() as session:
            appt = session.exec(select(Appointment).where(Appointment.appointment_slip_code == aid)).first()
            if appt:
                appt.rescheduled_from_date = appt.appointment_date
                appt.rescheduled_from_time = appt.appointment_time
                appt.appointment_date = dt.date.fromisoformat(new_date_str)
                appt.appointment_time = dt.datetime.strptime(new_time_str, "%H:%M").time()
                appt.status = "เลื่อนนัด"
                session.add(appt)
            
            booking = session.exec(select(QueueBooking).where(QueueBooking.booking_code == aid)).first()
            if booking:
                booking.booking_date = dt.date.fromisoformat(new_date_str)
                booking.booking_time = dt.datetime.strptime(new_time_str, "%H:%M").time()
                booking.status = "เลื่อนนัด"
                session.add(booking)

            session.commit()

        self.resched_open = False
        self.load_schedule_data()
        return rx.toast.success(f"เลื่อนนัดหมายรหัส {aid} เรียบร้อยแล้ว")

    @rx.event
    def open_next_appt(self, pid: str = ""):
        default_pid = pid
        if not default_pid and self.patients:
            default_pid = f"{self.patients[0]['id']} · {self.patients[0].get('full_name', '')}"
        self.next_appt_patient = default_pid or "ผู้ป่วยทั่วไป"
        self.next_appt_open = True

    @rx.event
    def set_next_appt_open(self, value: bool):
        self.next_appt_open = value

    @rx.event
    def create_next_appt(self, form: dict):
        target_date = dt.date.fromisoformat(form.get("date") or iso(7))
        target_time = dt.datetime.strptime(form.get("time") or "10:00", "%H:%M").time()

        patient_field = form.get("patient") or self.next_appt_patient or "ผู้ป่วยทั่วไป"
        patient_name = patient_field.split(" · ")[-1]
        dentist_name = form.get("dentist") or "ทันตแพทย์ประจำคลินิก"
        purpose = form.get("purpose") or "นัดติดตามอาการ"

        # 1. ค้นหาข้อมูลคนไข้จริงจาก self.patients เพื่อดึงเบอร์โทรและประวัติโรคประจำตัว/ยาที่แพ้
        matched_patient = next(
            (p for p in self.patients if p.get("full_name") == patient_name or p.get("id") in patient_field),
            None,
        )

        # 2. ใช้เบอร์จากฟอร์ม -> ถ้าไม่มีให้ใช้เบอร์จริงของคนไข้ -> ถ้าไม่มีให้เว้นว่างหรือขีด "-"
        contact_info = (
            form.get("contact")
            or (matched_patient.get("phone") if matched_patient else "")
            or "-"
        )
        patient_id = matched_patient.get("id") if matched_patient else None

        with rx.session() as session:
            total_appts = len(session.exec(select(Appointment)).all())
            slip_code = f"AP-{total_appts + 1:04d}"

            new_appt = Appointment(
                patient_id=patient_id,
                patient_name=patient_name,
                contact_info=contact_info,
                appointment_date=target_date,
                appointment_time=target_time,
                purpose=purpose,
                status="ยืนยันแล้ว",
                appointment_slip_code=slip_code,
                notes=form.get("note") or None,
                created_at=get_utc_now(),
            )
            session.add(new_appt)
            session.commit()
            session.refresh(new_appt)

        self.next_appt_open = False
        self.load_schedule_data()

        # แสดงป๊อปอัปใบนัดหมาย
        self.slip = format_appointment({
            "id": slip_code,
            "patient_name": patient_name,
            "date": target_date.isoformat(),
            "time": target_time.strftime("%H:%M"),
            "service": form.get("service") or purpose,
            "dentist": dentist_name,
            "purpose": purpose,
            "status": "ยืนยันแล้ว",
            "phone": contact_info,
        })
        self.slip_open = True
        return rx.toast.success(f"ออกใบนัดหมายสำเร็จ (รหัส: {slip_code})")

    @rx.event
    def select_schedule_dentist(self, did: str):
        self.schedule_dentist_id = did\

    @rx.event
    def set_new_leave_date(self, value: str):
        self.new_leave_date = value

    @rx.event
    def set_new_leave_reason(self, value: str):
        self.new_leave_reason = value

    @rx.event
    def add_leave(self):
        if not self.new_leave_date:
            return rx.toast.warning("กรุณาเลือกวันที่ต้องการหยุด")

        reason = self.new_leave_reason.strip() if self.new_leave_reason.strip() else "วันหยุดพิเศษ"
        doc = next((d for d in self.dentists if d.get("id") == self.schedule_dentist_id), None)
        if not doc:
            return rx.toast.error("กรุณาเลือกทันตแพทย์")

        try:
            leaves_list = json.loads(doc.get("leaves", "[]"))
        except Exception:
            leaves_list = []

        if any(item.get("date") == self.new_leave_date for item in leaves_list):
            return rx.toast.warning("มีรายการของวันนี้อยู่ในรายการแล้ว")

        leaves_list.append({
            "date": self.new_leave_date,
            "reason": reason,
            "label": f"{self.new_leave_date}: {reason}",
        })

        doc["leaves"] = json.dumps(leaves_list, ensure_ascii=False)
        self.new_leave_date = ""
        self.new_leave_reason = ""
        return rx.toast.info("เพิ่มวันหยุดพิเศษแล้ว อย่าลืมกดบันทึกตารางเวลา")

    @rx.event
    def remove_leave(self, target_date: str):
        doc = next((d for d in self.dentists if d.get("id") == self.schedule_dentist_id), None)
        if doc:
            try:
                leaves_list = json.loads(doc.get("leaves", "[]"))
                leaves_list = [x for x in leaves_list if x.get("date") != target_date]
                doc["leaves"] = json.dumps(leaves_list, ensure_ascii=False)
            except Exception:
                pass

    @rx.var
    def schedule_leaves(self) -> list[dict[str, str]]:
        doc = self.schedule_dentist
        if not doc:
            return []
        try:
            return json.loads(doc.get("leaves", "[]"))
        except Exception:
            return []

    @rx.event
    def save_schedule(self):
        """บันทึกลงฐานข้อมูล SQLite เฉพาะเมื่อกดปุ่มบันทึกตารางเวลา และผูกตามเดือน"""
        target_doc = next((d for d in self.dentists if d["id"] == self.schedule_dentist_id), None)
        if not target_doc:
            return rx.toast.error("กรุณาเลือกทันตแพทย์ก่อนบันทึก")

        doc_name = target_doc["name"]
        work_days_str = target_doc.get("days", "")
        leaves_json_str = target_doc.get("leaves", "[]")

        with rx.session() as session:
            sched = session.exec(
                select(DoctorSchedule).where(
                    DoctorSchedule.dentist_id == self.schedule_dentist_id,
                    DoctorSchedule.schedule_month == self.schedule_selected_month,
                )
            ).first()

            if not sched:
                sched = DoctorSchedule(
                    dentist_id=self.schedule_dentist_id,
                    dentist_name=doc_name,
                    schedule_month=self.schedule_selected_month,
                    work_days=work_days_str,
                    start_time=target_doc.get("start", "09:00"),
                    end_time=target_doc.get("end", "18:00"),
                    lunch_time=target_doc.get("lunch", "12:00"),
                    leaves=leaves_json_str,
                )
                session.add(sched)
            else:
                sched.work_days = work_days_str
                sched.start_time = target_doc.get("start", "09:00")
                sched.end_time = target_doc.get("end", "18:00")
                sched.lunch_time = target_doc.get("lunch", "12:00")
                sched.leaves = leaves_json_str
                session.add(sched)

            session.commit()

        return rx.toast.success(f"บันทึกตารางงานเดือน {self.schedule_selected_month} ของ {doc_name} สำเร็จ")

    @rx.event
    def toggle_work_day(self, day: str):
        """เปิด/ปิด วันเข้าเวรของทันตแพทย์ที่กำลังเลือกอยู่"""
        doc = next((d for d in self.dentists if d.get("id") == self.schedule_dentist_id), None)
        if not doc:
            return

        current_days = [x for x in doc.get("days", "").split(",") if x]
        if day in current_days:
            current_days.remove(day)
        else:
            current_days.append(day)
            current_days.sort()

        doc["days"] = ",".join(current_days)

    @rx.event
    def set_sched_start(self, value: str):
        """ตั้งเวลาเริ่มงานของแพทย์ที่เลือก"""
        doc = next((d for d in self.dentists if d.get("id") == self.schedule_dentist_id), None)
        if doc:
            doc["start"] = value

    @rx.event
    def set_sched_end(self, value: str):
        """ตั้งเวลาเลิกงานของแพทย์ที่เลือก"""
        doc = next((d for d in self.dentists if d.get("id") == self.schedule_dentist_id), None)
        if doc:
            doc["end"] = value

    @rx.event
    def set_sched_lunch(self, value: str):
        """ตั้งเวลาพักกลางวันของแพทย์ที่เลือก"""
        doc = next((d for d in self.dentists if d.get("id") == self.schedule_dentist_id), None)
        if doc:
            doc["lunch"] = "" if value == "ไม่มีพัก" else value

    # ======================================================================
    # 5.4 treatment records & dental chart
    # ======================================================================
    @rx.event
    def load_treatment_entries(self):
        """โหลดข้อมูลประวัติการรักษาทั้งหมดจากฐานข้อมูลเข้าสู่ State"""
        with rx.session() as session:
            db_entries = session.exec(select(TreatmentEntry)).all()
            loaded = []
            for e in db_entries:
                loaded.append(format_entry({
                    "id": str(e.id),
                    "patient_id": e.patient_id,
                    "tooth": e.tooth_number,
                    "icd": e.icd_code,
                    "procedure": e.procedure_name,
                    "note": e.notes or "",
                    "dentist": e.dentist_name,
                    "timestamp": e.created_at.isoformat() if e.created_at else "",
                }))
            self.entries = loaded

    @rx.event
    def select_patient(self, option: str):
        self.selected_patient_id = option.split(" · ")[0].strip()
        self.selected_tooth = self.entry_tooth = ""
        self.load_patients_data()
        self.load_treatment_entries()

    @rx.event
    def open_patient_record(self, pid: str, page: str):
        self.selected_patient_id = pid
        self.selected_tooth = self.entry_tooth = ""
        self.load_patients_data()
        self.load_treatment_entries()
        return rx.redirect(page)

    @rx.event
    def select_tooth(self, tooth: str):
        self.selected_tooth = tooth
        self.entry_tooth = tooth

    @rx.event
    def set_entry_tooth(self, value: str):
        self.entry_tooth = value.strip()
        self.selected_tooth = value.strip()

    @rx.event
    def set_tooth_input_mode(self, value: str | list[str]):
        self.tooth_input_mode = value if isinstance(value, str) else value[0]

    @rx.event
    def set_entry_icd(self, value: str):
        self.entry_icd = value

    @rx.event
    def set_entry_procedure(self, value: str):
        self.entry_procedure = value

    @rx.event
    def set_entry_note(self, value: str):
        self.entry_note = value

    @rx.event
    def save_entry(self):
        target_pid = self.selected_pid or (self.patients[0]["id"] if self.patients else "")
        if not target_pid:
            return rx.toast.error("ยังไม่ได้เลือกผู้ป่วย")
        if not self.entry_tooth:
            return rx.toast.error("กรุณาเลือกซี่ฟัน (คลิกที่ผังฟัน เลือกจาก Dropdown หรือพิมพ์เลขซี่ฟัน)")
        if self.entry_tooth not in ALL_TEETH:
            return rx.toast.error(f"ไม่มีซี่ฟันหมายเลข {self.entry_tooth} — ใช้เลข 1–32")
        if not self.entry_icd:
            return rx.toast.error("กรุณาเลือกรหัสการวินิจฉัย (ICD-10)")

        with rx.session() as session:
            new_entry = TreatmentEntry(
                patient_id=target_pid,
                tooth_number=self.entry_tooth,
                icd_code=self.entry_icd,
                procedure_name=self.entry_procedure,
                notes=self.entry_note.strip() if self.entry_note else None,
                dentist_name=self.user_name if (self.is_logged_in and self.user_name) else "ทันตแพทย์ผู้ตรวจ",
                created_at=get_utc_now(),
            )
            session.add(new_entry)
            session.commit()
            session.refresh(new_entry)

        saved_tooth = new_entry.tooth_number
        self.entry_note = ""
        self.entry_tooth = ""
        self.selected_tooth = ""
        self.entry_icd = ""

        self.load_treatment_entries()
        return rx.toast.success(f"บันทึกการรักษาซี่ {saved_tooth} เรียบร้อยแล้ว")

        # บันทึกข้อมูลการรักษาลงในตาราง TreatmentEntry
        with rx.session() as session:
            new_entry = TreatmentEntry(
                patient_id=target_pid,
                tooth_number=self.entry_tooth,
                icd_code=self.entry_icd,
                procedure_name=self.entry_procedure,
                notes=self.entry_note.strip() if self.entry_note else None,
                dentist_name=self.user_name if self.is_logged_in else "ทันตแพทย์ผู้ตรวจ",
                created_at=get_utc_now(),
            )
            session.add(new_entry)
            session.commit()
            session.refresh(new_entry)

        # เคลียร์ฟอร์มและโหลดข้อมูลผังฟันใหม่
        self.entry_note = ""
        self.load_schedule_data()
        return rx.toast.success(f"บันทึกการรักษาซี่ {self.entry_tooth} เรียบร้อยแล้ว")
    
    @rx.event
    def select_my_tooth(self, tooth: str):
        """เลือก/ยกเลิกเลือกซี่ฟันในหน้าประวัติการรักษาของคนไข้ (/my-history)"""
        if self.my_selected_tooth == tooth:
            self.my_selected_tooth = ""
        else:
            self.my_selected_tooth = tooth 