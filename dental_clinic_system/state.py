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

import datetime as dt
import uuid
import reflex as rx
from sqlmodel import select

from dental_clinic_system.backend.models import QueueBooking, Appointment, TreatmentEntry, get_utc_now

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

# Tooth numbers 1–32, laid out as seen when facing the patient. Both rows read
# left → right (patient's right → left): upper 1 → 16, lower 17 → 32, so each
# lower tooth sits directly under the upper tooth with number - 16.
PERMANENT_UPPER = [str(n) for n in range(1, 17)]
PERMANENT_LOWER = [str(n) for n in range(17, 33)]
ALL_TEETH = PERMANENT_UPPER + PERMANENT_LOWER  # the chart shows exactly these 32 teeth
MOLARS = {"1", "2", "3", "14", "15", "16", "17", "18", "19", "30", "31", "32"}

# position counted from the back of each half-arch: 1st = third molar ... 8th = central incisor
_TOOTH_NAMES = ["ฟันกรามซี่ที่ 3", "ฟันกรามซี่ที่ 2", "ฟันกรามซี่ที่ 1", "ฟันกรามน้อยซี่ที่ 2",
                "ฟันกรามน้อยซี่ที่ 1", "ฟันเขี้ยว", "ฟันตัดซี่ข้าง", "ฟันตัดซี่กลาง"]


def tooth_label(tooth: str) -> str:
    """'19' -> 'ซี่ 19 · ฟันกรามซี่ที่ 1 ล่างขวา'."""
    if tooth not in ALL_TEETH:
        return tooth or "-"
    n = int(tooth)
    if n <= 8:
        name, side = _TOOTH_NAMES[n - 1], "บนขวา"
    elif n <= 16:
        name, side = _TOOTH_NAMES[16 - n], "บนซ้าย"
    elif n <= 24:
        name, side = _TOOTH_NAMES[n - 17], "ล่างขวา"
    else:
        name, side = _TOOTH_NAMES[32 - n], "ล่างซ้าย"
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

def generate_default_slots() -> list[dict[str, str]]:
    morning_slots = [f"{h:02d}:{m:02d}" for h in range(9, 12) for m in (0, 30)] + ["12:00"]
    afternoon_slots = [f"{h:02d}:{m:02d}" for h in range(13, 20) for m in (0, 30)] + ["20:00"]
    all_times = morning_slots + afternoon_slots
    return [
        {"time": t, "left": "2", "available": "1", "period": "เช้า" if int(t[:2]) < 13 else "บ่าย"}
        for t in all_times
    ]


class AppState(rx.State):
    # ---- data: TODO(backend) load these from the database (rows go through format_*)
    patients: list[dict[str, str]] = []
    dentists: list[dict[str, str]] = [
        {
            "id": "D-001",
            "name": "ทพ. สมศักดิ์ รักฟัน",
            "days": "1,2,3,4,5",  # ทำงาน จันทร์-ศุกร์ (หยุด เสาร์-อาทิตย์)
            "start": "09:00",
            "end": "17:00",
            "lunch": "12:00",
            "leaves": "2026-11-05",  # วันลาตัวอย่าง
        },
        {
            "id": "D-002",
            "name": "ทพญ. วารี สดใส",
            "days": "2,3,4,5,6",  # ทำงาน อังคาร-เสาร์ (หยุด อาทิตย์-จันทร์)
            "start": "10:00",
            "end": "19:00",
            "lunch": "13:00",
            "leaves": "",
        },
    ]
    appointments: list[dict[str, str]] = []
    entries: list[dict[str, str]] = []
    # free time slots for booking_date: [{"time": "09:00", "left": "2", "available": "1"}]
    available_slots: list[dict[str, str]] = generate_default_slots()

    # ---- session (5.1) ----
    user_role: str = "patient"
    user_name: str = "ปทิตญา ภูภิจคุณาเดชากร"
    user_email: str = "thakon.phukit@gmail.com"
    current_patient_id: str = "1"
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

    # ---- treatment (5.4) ----
    selected_patient_id: str = ""
    selected_tooth: str = ""
    entry_tooth: str = ""
    tooth_input_mode: str = "dropdown"
    entry_icd: str = ""
    entry_procedure: str = PROCEDURES[0]
    entry_note: str = ""
    my_selected_tooth: str = ""

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
        """รายชื่อคนไข้สำหรับ Dropdown ในฟอร์มออกใบนัดหมาย"""
        return [
            "P-001 · ปทิตญา ภูภิจคุณาเดชากร",
            "P-002 · ทดสอบ สมชาย",
            "P-003 · สมศรี มีฟันดี",
        ]

    @rx.var
    def next_appt_option(self) -> str:
        p = next((p for p in self.patients if p["id"] == self.next_appt_patient), None)
        return f"{p['id']} · {p['full_name']}" if p else ""

    @rx.var
    def dentist_names(self) -> list[str]:
        """รายชื่อทันตแพทย์สำหรับ Dropdown ในฟอร์มออกใบนัดหมาย"""
        return [
            "ทพ. สมศักดิ์ รักฟัน",
            "ทพญ. วารี สดใส",
            "ทันตแพทย์เวร",
        ]
    
    @rx.var
    def booking_dentist_options(self) -> list[str]:
        return ["ไม่ระบุ"] + self.dentist_names

    # ======================================================================
    # computed: booking (customer)
    # ======================================================================
    @rx.var
    def booking_days(self) -> list[dict[str, str]]:
        """สร้างรายการ 14 วันข้างหน้า พร้อมตรวจสอบวันปิดทำการและวันลาของทันตแพทย์"""
        days = []
        chosen_dentist = next((d for d in self.dentists if d["name"] == self.booking_dentist), None)

        for offset in range(0, 14):
            d = today() + dt.timedelta(days=offset)
            iso_str = d.isoformat()
            weekday_num = str(d.isoweekday())  # 1 = จันทร์ ... 7 = อาทิตย์

            is_closed = False

            if chosen_dentist:
                # 1. เช็คว่าแพทย์คนนี้ทำงานวันนั้นหรือไม่
                work_days = [x for x in chosen_dentist.get("days", "").split(",") if x]
                if work_days and weekday_num not in work_days:
                    is_closed = True

                # 2. เช็คว่าตรงกับวันลาของแพทย์หรือไม่
                leaves = [x for x in chosen_dentist.get("leaves", "").split(",") if x]
                if iso_str in leaves:
                    is_closed = True
            else:
                # หากเลือก "ไม่ระบุ" ให้เช็คว่ามีแพทย์คนใดเข้าเวรในวันนั้นบ้างหรือไม่
                any_working = any(weekday_num in d.get("days", "").split(",") for d in self.dentists) if self.dentists else True
                if not any_working:
                    is_closed = True

            days.append({
                "iso": iso_str,
                "weekday": THAI_DAYS[d.isoweekday() - 1],
                "day": str(d.day),
                "month": THAI_MONTHS[d.month - 1],
                "free": "เต็ม" if is_closed else "",
                "closed": "1" if is_closed else "0",
            })
        return days

    @rx.var
    def booking_slots(self) -> list[dict[str, str]]:
        return self.available_slots

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
        return self.schedule_dentist.get("days", "").split(",")

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
        return f"{p['id']} · {p['full_name']}" if p else ""

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
        return sorted((e for e in self.entries if e["patient_id"] == self.current_patient_id), key=lambda e: e["timestamp"], reverse=True)

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
    def login(self, form: dict):
        # TODO(backend): check email/password for self.login_role ("patient" or "staff").
        # On success set user_role, user_name, user_email (+ current_patient_id for patients)
        # and redirect to "/profile" (patient) or "/dashboard" (staff).
        # On failure set self.login_error.
        self.login_error = ""
        return not_connected("เข้าสู่ระบบ")

    @rx.event
    def set_login_role(self, value: str | list[str]):
        self.login_role = value if isinstance(value, str) else value[0]
        self.login_error = ""

    @rx.event
    def register(self, form: dict):
        if (form.get("password") or "") != (form.get("confirm") or ""):
            self.register_error = "รหัสผ่านและการยืนยันรหัสผ่านไม่ตรงกัน"
            return
        if len(form.get("password") or "") < 8:
            self.register_error = "รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร"
            return
        self.register_error = ""
        # TODO(backend): create the patient account from `form` (first_name, last_name, gender, dob,
        # national_id, phone, address, disease, allergy, email, password), reject duplicate emails,
        # then log the patient in and redirect to "/profile".
        return not_connected("สมัครสมาชิก")

    @rx.event
    def request_reset(self, form: dict):
        # TODO(backend): look up the email and send a 6-digit code; set self.reset_error if not found.
        self.reset_email, self.reset_error, self.reset_step = (form.get("email") or "").strip().lower(), "", 2

    @rx.event
    def confirm_reset(self, form: dict):
        pw = form.get("password") or ""
        if len(pw) < 8 or pw != (form.get("confirm") or ""):
            self.reset_error = "รหัสผ่านใหม่ต้องมีอย่างน้อย 8 ตัวและตรงกับการยืนยัน"
            return
        # TODO(backend): verify form["otp"] for self.reset_email and save the new password,
        # then move to step 3; set self.reset_error if the code is wrong.
        self.reset_error = ""
        return not_connected("ตั้งรหัสผ่านใหม่")

    @rx.event
    def restart_reset(self):
        self.reset_step, self.reset_error, self.reset_email = 1, "", ""

    @rx.event
    def logout(self):
        # TODO(backend): end the server-side session
        self.user_role = self.user_name = self.user_email = self.current_patient_id = ""
        return [rx.toast.info("ออกจากระบบแล้ว"), rx.redirect("/")]

    # ======================================================================
    # 5.2 member management
    # ======================================================================
    @rx.event
    def save_profile(self, form: dict):
        # TODO(backend): save first_name, last_name, gender, dob, national_id, phone, email,
        # address, disease, allergy for the logged-in patient, reload self.patients, redirect "/profile".
        return not_connected("บันทึกข้อมูลส่วนตัว")

    @rx.event
    def change_password(self, form: dict):
        new = form.get("new") or ""
        if len(new) < 8:
            self.password_error = "รหัสผ่านใหม่ต้องมีอย่างน้อย 8 ตัวอักษร"
            return
        if new != (form.get("confirm") or ""):
            self.password_error = "รหัสผ่านใหม่และการยืนยันไม่ตรงกัน"
            return
        if new == (form.get("current") or ""):
            self.password_error = "รหัสผ่านใหม่ต้องไม่ซ้ำกับรหัสผ่านเดิม"
            return
        self.password_error = ""
        # TODO(backend): check form["current"] and save the new password; set self.password_error on failure.
        return not_connected("เปลี่ยนรหัสผ่าน")

    @rx.event
    def set_privacy(self, key: str, value: bool):
        self.privacy = {**self.privacy, key: value}

    @rx.event
    def toggle_privacy(self, key: str):
        self.privacy = {**self.privacy, key: not self.privacy.get(key, False)}
        # TODO(backend): save self.privacy for the logged-in patient

    @rx.event
    def download_my_data(self):
        # TODO(backend): export the patient's data (profile + treatment history) as a file
        return not_connected("ดาวน์โหลดข้อมูล")

    # ======================================================================
    # 5.3 booking (customer)
    # ======================================================================
    @rx.event
    def pick_date(self, value: str):
        self.booking_date = value
        self.booking_time = ""

        # ตรวจสอบว่าวันที่เลือกเป็นวันปิดหรือวันลาหรือไม่
        day_info = next((d for d in self.booking_days if d["iso"] == value), None)
        if day_info and day_info.get("closed") == "1":
            self.available_slots = []
            return rx.toast.warning("วันที่เลือกคลินิกปิดทำการ หรือทันตแพทย์ลาหยุด")

        # สล็อตเวลาปกติ
        morning_slots = [f"{h:02d}:{m:02d}" for h in range(9, 12) for m in (0, 30)] + ["12:00"]
        afternoon_slots = [f"{h:02d}:{m:02d}" for h in range(13, 20) for m in (0, 30)] + ["20:00"]
        all_times = morning_slots + afternoon_slots

        self.available_slots = [
            {
                "time": t,
                "left": "2",
                "available": "1",
                "period": "เช้า" if int(t[:2]) < 13 else "บ่าย",
            }
            for t in all_times
        ]

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
        # คำนวณช่วงเวลาใหม่ตามวันที่เลือกอยู่ ณ ขณะนั้น
        return self.pick_date(self.booking_date)

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
        code = f"Q-{target_date.strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"

        # ดึง patient_id จาก session ถ้ายังไม่ได้ล็อกอินให้เป็น None หรือ Fallback เป็น "1"
        pid = self.current_patient_id if self.is_logged_in and self.current_patient_id else "1"

        with rx.session() as session:
            new_booking = QueueBooking(
                patient_id=pid,  # ผูกกับ ID คนไข้
                patient_name=draft["patient_name"],
                phone_number=draft["phone"],
                booking_date=target_date,
                booking_time=target_time,
                service_type=draft["service"],
                underlying_disease=draft.get("disease", "ไม่มี"),
                drug_allergy=draft.get("allergy", "ไม่มี"),
                status="รออนุมัติ",
                booking_code=code,
                created_at=get_utc_now(),
            )
            session.add(new_booking)
            session.commit()
            session.refresh(new_booking)

            saved_draft = dict(draft)
            saved_draft["id"] = code
            saved_draft["patient_id"] = pid
            self.booking_slip = saved_draft
            self.booking_draft = {}
            self.booking_time = ""

        self.load_schedule_data()
        return rx.toast.success("บันทึกการจองคิวเรียบร้อยแล้ว")

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
    def load_schedule_data(self):
        """โหลดข้อมูลคิว, การนัดหมาย และประวัติผังฟันจากฐานข้อมูล"""
        with rx.session() as session:
            bookings = session.exec(select(QueueBooking)).all()
            appts = session.exec(select(Appointment)).all()
            db_entries = session.exec(select(TreatmentEntry)).all()
            
            loaded_list = []

            for b in bookings:
                loaded_list.append(format_appointment({
                    "id": b.booking_code,
                    "db_id": str(b.id),
                    "kind": "จองคิว",
                    "patient_id": str(getattr(b, "patient_id", "") or "1"),
                    "patient_name": b.patient_name,
                    "phone": b.phone_number,
                    "date": b.booking_date.isoformat(),
                    "time": b.booking_time.strftime("%H:%M"),
                    "service": b.service_type,
                    "dentist": "ไม่ระบุ",
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
                    "dentist": "ทันตแพทย์เวร",
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
        """ดึงรายการนัดหมายทั้งหมด เรียงลำดับจากล่าสุดขึ้นก่อน"""
        return list(reversed(self.appointments))

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
            booking = session.exec(select(QueueBooking).where(QueueBooking.booking_code == self.reject_target)).first()
            if booking:
                booking.status = "ปฏิเสธ"
                # ถ้าในโมเดล QueueBooking มีฟิลด์ reason หรือ note ให้บันทึกไว้
                if hasattr(booking, "notes"):
                    booking.notes = reason
                session.add(booking)
                session.commit()
        self.reject_open = False
        self.load_schedule_data()
        return rx.toast.info(f"ปฏิเสธคำขอการจองเรียบร้อย: {reason}")

    @rx.event
    def set_appt_search(self, value: str):
        self.appt_search = value

    @rx.event
    def set_appt_filter(self, value: str | list[str]):
        self.appt_filter = value if isinstance(value, str) else value[0]

    @rx.event
    def cancel_appt(self, aid: str):
        with rx.session() as session:
            # 1. เช็คใน Appointment ก่อน
            appt = session.exec(select(Appointment).where(Appointment.appointment_slip_code == aid)).first()
            if appt:
                appt.status = "ยกเลิกนัด"
                session.add(appt)
            # 2. ถ้าไม่พบ ให้เช็คใน QueueBooking
            booking = session.exec(select(QueueBooking).where(QueueBooking.booking_code == aid)).first()
            if booking:
                booking.status = "ยกเลิกนัด"
                session.add(booking)
            session.commit()

        self.load_schedule_data()
        return rx.toast.info(f"ยกเลิกนัดหมายรหัส {aid} เรียบร้อย")

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
        self.next_appt_patient = pid or "P-001 · ปทิตญา ภูภิจคุณาเดชากร"
        self.next_appt_open = True

    @rx.event
    def set_next_appt_open(self, value: bool):
        self.next_appt_open = value

    @rx.event
    def create_next_appt(self, form: dict):
        target_date = dt.date.fromisoformat(form.get("date") or iso(7))
        target_time = dt.datetime.strptime(form.get("time") or "10:00", "%H:%M").time()
        slip_code = f"AP-{target_date.strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"

        patient_field = form.get("patient") or self.next_appt_patient or "ผู้ป่วยทั่วไป"
        patient_name = patient_field.split(" · ")[-1]
        dentist_name = form.get("dentist") or "ทันตแพทย์ประจำคลินิก"
        purpose = form.get("purpose") or "นัดติดตามอาการ"
        contact_info = form.get("contact") or "0924073094"

        with rx.session() as session:
            new_appt = Appointment(
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

        # แสดงป๊อปอัปใบนัดหมายทันทีหลังจากสร้างเสร็จ
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
        return rx.toast.success("ออกใบนัดหมายสำเร็จและบันทึกลงระบบแล้ว")

    @rx.event
    def select_schedule_dentist(self, did: str):
        self.schedule_dentist_id = did

    def _update_dentist(self, **changes: str):
        self.dentists = [{**d, **changes} if d.get("id") == self.schedule_dentist_id else d for d in self.dentists]

    @rx.event
    def toggle_work_day(self, day: str):
        days = [x for x in self.schedule_days if x]
        days = [x for x in days if x != day] if day in days else sorted(days + [day])
        self._update_dentist(days=",".join(days))

    @rx.event
    def set_sched_start(self, value: str):
        self._update_dentist(start=value)

    @rx.event
    def set_sched_end(self, value: str):
        self._update_dentist(end=value)

    @rx.event
    def set_sched_lunch(self, value: str):
        self._update_dentist(lunch="" if value == "ไม่มีพัก" else value)

    @rx.event
    def set_new_leave_date(self, value: str):
        self.new_leave_date = value

    @rx.event
    def add_leave(self):
        if not self.new_leave_date:
            return rx.toast.error("กรุณาเลือกวันที่")
        leaves = [x for x in self.schedule_dentist.get("leaves", "").split(",") if x]
        if self.new_leave_date not in leaves:
            leaves.append(self.new_leave_date)
        self._update_dentist(leaves=",".join(sorted(leaves)))
        self.new_leave_date = ""

    @rx.event
    def remove_leave(self, value: str):
        leaves = [x for x in self.schedule_dentist.get("leaves", "").split(",") if x and x != value]
        self._update_dentist(leaves=",".join(leaves))

    @rx.event
    def save_schedule(self):
        return rx.toast.success("บันทึกตารางเวลาเรียบร้อยแล้ว")

    # ======================================================================
    # 5.4 treatment records & dental chart
    # ======================================================================
    @rx.event
    def select_patient(self, option: str):
        self.selected_patient_id = option.split(" · ")[0].strip()
        self.selected_tooth = self.entry_tooth = ""

    @rx.event
    def open_patient_record(self, pid: str, page: str):
        self.selected_patient_id = pid
        self.selected_tooth = self.entry_tooth = ""
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
        target_pid = self.selected_pid or "P-001"
        if not target_pid:
            return rx.toast.error("ยังไม่ได้เลือกผู้ป่วย")
        if not self.entry_tooth:
            return rx.toast.error("กรุณาเลือกซี่ฟัน (คลิกที่ผังฟัน เลือกจาก Dropdown หรือพิมพ์เลขซี่ฟัน)")
        if self.entry_tooth not in ALL_TEETH:
            return rx.toast.error(f"ไม่มีซี่ฟันหมายเลข {self.entry_tooth} — ใช้เลข 1–32")
        if not self.entry_icd:
            return rx.toast.error("กรุณาเลือกรหัสการวินิจฉัย (ICD-10)")

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
