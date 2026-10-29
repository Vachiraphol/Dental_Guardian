from datetime import date, time, datetime, timezone
from typing import Optional
import reflex as rx
from sqlmodel import Field

def get_utc_now():
    """ฟังก์ชันคืนค่าเวลาปัจจุบันแบบมี Timezone UTC"""
    return datetime.now(timezone.utc)

class QueueBooking(rx.Model, table=True):
    """ตารางเก็บข้อมูลการจองคิวของผู้ป่วย (SRS 5.3)"""
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: Optional[str] = Field(default=None, index=True)
    patient_name: str
    phone_number: str
    booking_date: date
    booking_time: time
    service_type: str
    underlying_disease: Optional[str] = "ไม่มี"
    drug_allergy: Optional[str] = "ไม่มี"
    status: str = Field(default="รออนุมัติ")
    booking_code: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=get_utc_now)

class Appointment(rx.Model, table=True):
    """ตารางเก็บข้อมูลการนัดหมายครั้งถัดไป (SRS 5.3)"""
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: Optional[str] = Field(default=None, index=True)
    patient_name: str
    contact_info: str
    appointment_date: date
    appointment_time: time
    purpose: str
    status: str = Field(default="ยืนยันแล้ว")
    appointment_slip_code: str = Field(unique=True)
    rescheduled_from_date: Optional[date] = None
    rescheduled_from_time: Optional[time] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=get_utc_now)

class TreatmentEntry(rx.Model, table=True):
    """ตารางเก็บประวัติการรักษาและผังฟัน (SRS 5.4)"""
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: str = Field(index=True)
    tooth_number: str
    icd_code: str
    procedure_name: str
    notes: Optional[str] = None
    dentist_name: Optional[str] = "ทันตแพทย์ผู้ตรวจ"
    created_at: datetime = Field(default_factory=get_utc_now)