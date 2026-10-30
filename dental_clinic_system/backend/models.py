"""Database models for Dental Guardian."""

import datetime as dt
from typing import Optional
from sqlmodel import Field, SQLModel


def get_utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class User(SQLModel, table=True):
    """ตารางเก็บข้อมูลบัญชีผู้ใช้งาน (คนไข้, หมอ, เจ้าหน้าที่, แอดมิน)"""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    full_name: str
    role: str = "patient"  # "patient", "dentist", "staff", "admin"
    is_active: bool = True
    created_at: dt.datetime = Field(default_factory=get_utc_now)


class Patient(SQLModel, table=True):
    """ตารางเก็บข้อมูลเวชระเบียนผู้ป่วย"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    hn_code: str = Field(index=True, unique=True)
    national_id: Optional[str] = None
    first_name: str
    last_name: str
    email: Optional[str] = None
    birth_date: Optional[dt.date] = None
    gender: Optional[str] = "ไม่ระบุ"
    phone_number: str
    address: Optional[str] = None
    underlying_disease: Optional[str] = "ไม่มี"
    drug_allergy: Optional[str] = "ไม่มี"
    created_at: dt.datetime = Field(default_factory=get_utc_now)


class DoctorSchedule(SQLModel, table=True):
    """ตารางเก็บตารางงานของแพทย์ แยกตามแพทย์และรายเดือน"""
    id: Optional[int] = Field(default=None, primary_key=True)
    dentist_id: str
    dentist_name: str
    schedule_month: str = "2026-10"
    work_days: str = "1,2,3,4,5"
    start_time: str = "09:00"
    end_time: str = "18:00"
    lunch_time: str = "12:00"
    leaves: str = "[]"  # เก็บ JSON string ของวันหยุดพิเศษและรายละเอียด


class QueueBooking(SQLModel, table=True):
    """ตารางเก็บคำขอจองคิวออนไลน์"""
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: Optional[str] = None
    patient_name: str
    phone_number: str
    booking_date: dt.date
    booking_time: dt.time
    service_type: str
    underlying_disease: Optional[str] = "ไม่มี"
    drug_allergy: Optional[str] = "ไม่มี"
    status: str = "รออนุมัติ"  # รออนุมัติ, ยืนยันแล้ว, ยกเลิกนัด, ปฏิเสธ, มาตามนัด
    booking_code: str = Field(index=True, unique=True)
    notes: Optional[str] = None
    created_at: dt.datetime = Field(default_factory=get_utc_now)


class Appointment(SQLModel, table=True):
    """ตารางเก็บการนัดหมายที่ยืนยันแล้ว / นัดติดตามอาการ"""
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_name: str
    contact_info: str
    appointment_date: dt.date
    appointment_time: dt.time
    rescheduled_from_date: Optional[dt.date] = None
    rescheduled_from_time: Optional[dt.time] = None
    purpose: str = "นัดติดตามอาการ"
    status: str = "ยืนยันแล้ว"
    appointment_slip_code: str = Field(index=True, unique=True)
    notes: Optional[str] = None
    created_at: dt.datetime = Field(default_factory=get_utc_now)


class TreatmentEntry(SQLModel, table=True):
    """ตารางบันทึกประวัติการรักษาในผังฟัน"""
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: str
    tooth_number: str
    icd_code: str
    procedure_name: str
    dentist_name: str
    notes: Optional[str] = None
    created_at: dt.datetime = Field(default_factory=get_utc_now)