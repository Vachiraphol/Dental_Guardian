from datetime import date, time, datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field

def get_utc_now():
    return datetime.now(timezone.utc)

# -------------------------------------------------------------
# SRS 5.2: ระบบผู้ใช้งานและการยืนยันตัวตน
# -------------------------------------------------------------
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)  # อีเมลสำหรับล็อกอิน
    password_hash: str
    full_name: str
    role: str = Field(default="patient")  # "patient", "staff", "dentist"
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=get_utc_now)

# -------------------------------------------------------------
# SRS 5.1: เวชระเบียนผู้ป่วย
# -------------------------------------------------------------
class Patient(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    hn_code: str = Field(unique=True, index=True)
    national_id: Optional[str] = Field(default=None, index=True)
    first_name: str
    last_name: str
    email: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    phone_number: str
    address: Optional[str] = None
    underlying_disease: Optional[str] = "ไม่มี"
    drug_allergy: Optional[str] = "ไม่มี"
    created_at: datetime = Field(default_factory=get_utc_now)

# -------------------------------------------------------------
# SRS 5.3: การจองคิวออนไลน์
# -------------------------------------------------------------
class QueueBooking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    booking_code: str = Field(unique=True, index=True)
    patient_id: Optional[str] = Field(default=None, index=True)
    patient_name: str
    phone_number: str
    booking_date: date
    booking_time: time
    service_type: str
    underlying_disease: Optional[str] = "ไม่มี"
    drug_allergy: Optional[str] = "ไม่มี"
    status: str = Field(default="รออนุมัติ")  # "รออนุมัติ", "ยืนยันแล้ว", "ปฏิเสธ", "ยกเลิกนัด"
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=get_utc_now)

# -------------------------------------------------------------
# SRS 5.3: ใบนัดหมาย
# -------------------------------------------------------------
class Appointment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    appointment_slip_code: str = Field(unique=True, index=True)
    patient_name: str
    contact_info: str
    appointment_date: date
    appointment_time: time
    purpose: str
    status: str = Field(default="ยืนยันแล้ว")
    rescheduled_from_date: Optional[date] = None
    rescheduled_from_time: Optional[time] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=get_utc_now)

# -------------------------------------------------------------
# SRS 5.4: ประวัติการรักษาและผังฟัน
# -------------------------------------------------------------
class TreatmentEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: str = Field(index=True)
    tooth_number: str
    icd_code: str
    procedure_name: str
    notes: Optional[str] = None
    dentist_name: str = "ทันตแพทย์ประจำคลินิก"
    created_at: datetime = Field(default_factory=get_utc_now)