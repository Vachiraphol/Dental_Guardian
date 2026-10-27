import reflex as rx
from sqlmodel import Field
from datetime import date, time, datetime
from typing import Optional

class QueueBooking(rx.Model, table=True):
    """ตารางเก็บข้อมูลการจองคิวของผู้ป่วย"""
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_name: str                                  # ชื่อ-นามสกุล[cite: 1]
    phone_number: str                                  # เบอร์โทร[cite: 1]
    booking_date: date                                 # วันที่รับบริการ[cite: 1]
    booking_time: time                                 # เวลาที่รับบริการ[cite: 1]
    service_type: str                                  # บริการทันตกรรม[cite: 1]
    underlying_disease: Optional[str] = "ไม่มี"        # โรคประจำตัว[cite: 1]
    drug_allergy: Optional[str] = "ไม่มี"              # ยาที่แพ้[cite: 1]
    status: str = Field(default="รออนุมัติ")            # สถานะ: รออนุมัติ / ยืนยันการจองคิว[cite: 1]
    booking_code: str = Field(unique=True, index=True) # รหัสสำหรับใบสรุปคิวยื่นหน้าร้าน[cite: 1]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Appointment(rx.Model, table=True):
    """ตารางเก็บข้อมูลการนัดหมายครั้งถัดไป"""
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_name: str                                  # ชื่อบัญชีผู้ป่วย[cite: 1]
    contact_info: str                                  # ข้อมูลติดต่อ[cite: 1]
    appointment_date: date                             # วันที่นัดหมาย[cite: 1]
    appointment_time: time                             # เวลาที่นัดหมาย[cite: 1]
    purpose: str                                       # วัตถุประสงค์ เช่น การนัดหมายครั้งถัดไปเพื่ออะไร[cite: 1]
    status: str = Field(default="มาตามเวลานัด")         # มาตามเวลานัด / ยกเลิกนัด / เลื่อนนัด[cite: 1]
    appointment_slip_code: str = Field(unique=True)    # รหัสใบนัดครั้งถัดไป[cite: 1]
    rescheduled_from_date: Optional[date] = None
    rescheduled_from_time: Optional[time] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)