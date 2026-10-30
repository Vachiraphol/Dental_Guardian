import uuid
from datetime import date, time
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from pydantic import BaseModel
import reflex as rx
from .models import QueueBooking, Appointment

router = APIRouter(prefix="/api", tags=["SRS 5.3 - Queue & Appointment"])

# เปลี่ยนฟังก์ชัน get_session ให้ใช้ rx.session() ของ Reflex
def get_session():
    with rx.session() as session:
        yield session

# --- Pydantic Schemas (สำหรับรับข้อมูลจาก Client) ---

class QueueCreate(BaseModel):
    patient_name: str
    phone_number: str
    booking_date: date
    booking_time: time
    service_type: str
    underlying_disease: Optional[str] = "ไม่มี"
    drug_allergy: Optional[str] = "ไม่มี"

class QueueStatusUpdate(BaseModel):
    status: str  # เช่น รออนุมัติ, กำลังรับบริการ, เสร็จสิ้น, ยกเลิก

class AppointmentCreate(BaseModel):
    patient_name: str
    contact_info: str
    appointment_date: date
    appointment_time: time
    purpose: str
    notes: Optional[str] = None

class AppointmentReschedule(BaseModel):
    new_date: date
    new_time: time
    notes: Optional[str] = None


# =================================================================
# 1. ระบบจัดการคิว (QueueBooking Endpoints)
# =================================================================

@router.post("/queues", status_code=201)
def create_queue_booking(payload: QueueCreate, session: Session = Depends(get_session)):
    """สร้างรายการจองคิวใหม่ พร้อมออกรหัสคิวอัตโนมัติ"""
    # สุ่มรหัสคิว เช่น Q-A1B2C3
    generated_code = f"Q-{uuid.uuid4().hex[:6].upper()}"
    
    queue_item = QueueBooking(
        **payload.model_dump(),
        booking_code=generated_code,
        status="รออนุมัติ"
    )
    session.add(queue_item)
    session.commit()
    session.refresh(queue_item)
    return {"status": "success", "data": queue_item}


@router.get("/queues")
def get_all_queues(
    booking_date: Optional[date] = None,
    status: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """ดึงรายการคิวทั้งหมด สามารถฟิลเตอร์ตามวันที่หรือสถานะได้"""
    query = select(QueueBooking)
    if booking_date:
        query = query.where(QueueBooking.booking_date == booking_date)
    if status:
        query = query.where(QueueBooking.status == status)
    
    return session.exec(query.order_by(QueueBooking.booking_time)).all()


@router.put("/queues/{queue_id}/status")
def update_queue_status(
    queue_id: int, 
    payload: QueueStatusUpdate, 
    session: Session = Depends(get_session)
):
    """อัปเดตสถานะคิว (เช่น เรียกคิว, เสร็จสิ้น)"""
    queue_item = session.get(QueueBooking, queue_id)
    if not queue_item:
        raise HTTPException(status_code=404, detail="Queue not found")
    
    queue_item.status = payload.status
    session.add(queue_item)
    session.commit()
    session.refresh(queue_item)
    return {"status": "success", "data": queue_item}


# =================================================================
# 2. ระบบจัดการนัดหมาย (Appointment Endpoints)
# =================================================================

@router.post("/appointments", status_code=201)
def create_appointment(payload: AppointmentCreate, session: Session = Depends(get_session)):
    """สร้างใบนัดหมายใหม่ พร้อมออกรหัสใบนัดอัตโนมัติ"""
    slip_code = f"APP-{uuid.uuid4().hex[:6].upper()}"
    
    appointment = Appointment(
        **payload.model_dump(),
        appointment_slip_code=slip_code,
        status="มาตามเวลานัด"
    )
    session.add(appointment)
    session.commit()
    session.refresh(appointment)
    return {"status": "success", "data": appointment}


@router.get("/appointments")
def get_all_appointments(
    appointment_date: Optional[date] = None,
    session: Session = Depends(get_session)
):
    """ดึงรายการนัดหมายทั้งหมด"""
    query = select(Appointment)
    if appointment_date:
        query = query.where(Appointment.appointment_date == appointment_date)
    return session.exec(query.order_by(Appointment.appointment_time)).all()


@router.put("/appointments/{appointment_id}/reschedule")
def reschedule_appointment(
    appointment_id: int,
    payload: AppointmentReschedule,
    session: Session = Depends(get_session)
):
    """เลื่อนวัน/เวลานัดหมาย พร้อมเก็บบันทึกประวัติวันเดิม"""
    appointment = session.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # บันทึกวันและเวลาเดิมไว้ก่อนเปลี่ยน
    appointment.rescheduled_from_date = appointment.appointment_date
    appointment.rescheduled_from_time = appointment.appointment_time
    
    # อัปเดตวันและเวลาใหม่
    appointment.appointment_date = payload.new_date
    appointment.appointment_time = payload.new_time
    appointment.status = "เลื่อนนัดหมาย"
    if payload.notes:
        appointment.notes = payload.notes

    session.add(appointment)
    session.commit()
    session.refresh(appointment)
    return {"status": "success", "data": appointment}