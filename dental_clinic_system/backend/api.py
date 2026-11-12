from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import reflex as rx
from sqlmodel import select

from dental_clinic_system.backend.models import TreatmentEntry, get_utc_now

router = APIRouter(prefix="/api", tags=["SRS 5.4 - Dental Chart & Treatments"])

# Schema สำหรับรับข้อมูลเข้า
class TreatmentCreate(BaseModel):
    patient_id: str
    tooth_number: str
    icd_code: str
    procedure_name: str
    notes: Optional[str] = None
    dentist_name: Optional[str] = "ทันตแพทย์ผู้ตรวจ"

class TreatmentUpdate(BaseModel):
    icd_code: Optional[str] = None
    procedure_name: Optional[str] = None
    notes: Optional[str] = None
    dentist_name: Optional[str] = None


# 1. GET: ดึงรายการประวัติการรักษาทั้งหมด หรือกรองตามคนไข้ / ซี่ฟัน
@router.get("/treatments")
def get_treatments(patient_id: Optional[str] = Query(None), tooth: Optional[str] = Query(None)):
    with rx.session() as session:
        query = select(TreatmentEntry)
        if patient_id:
            query = query.where(TreatmentEntry.patient_id == patient_id)
        if tooth:
            query = query.where(TreatmentEntry.tooth_number == tooth)
        return session.exec(query).all()

# 2. GET: ดึงประวัติการรักษาตาม ID
@router.get("/treatments/{entry_id}")
def get_treatment_by_id(entry_id: int):
    with rx.session() as session:
        entry = session.get(TreatmentEntry, entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="ไม่พบข้อมูลประวัติการรักษา")
        return entry

# 3. POST: สร้าง/บันทึกรายการรักษาใหม่
@router.post("/treatments", status_code=201)
def create_treatment(payload: TreatmentCreate):
    with rx.session() as session:
        new_entry = TreatmentEntry(
            patient_id=payload.patient_id,
            tooth_number=payload.tooth_number,
            icd_code=payload.icd_code,
            procedure_name=payload.procedure_name,
            notes=payload.notes,
            dentist_name=payload.dentist_name,
            created_at=get_utc_now(),
        )
        session.add(new_entry)
        session.commit()
        session.refresh(new_entry)
        return {"status": "success", "data": new_entry}

# 4. PUT: แก้ไขประวัติการรักษา
@router.put("/treatments/{entry_id}")
def update_treatment(entry_id: int, payload: TreatmentUpdate):
    with rx.session() as session:
        entry = session.get(TreatmentEntry, entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="ไม่พบข้อมูลประวัติการรักษา")
        
        if payload.icd_code is not None:
            entry.icd_code = payload.icd_code
        if payload.procedure_name is not None:
            entry.procedure_name = payload.procedure_name
        if payload.notes is not None:
            entry.notes = payload.notes
        if payload.dentist_name is not None:
            entry.dentist_name = payload.dentist_name

        session.add(entry)
        session.commit()
        session.refresh(entry)
        return {"status": "success", "data": entry}

# 5. DELETE: ลบรายการรักษา
@router.delete("/treatments/{entry_id}")
def delete_treatment(entry_id: int):
    with rx.session() as session:
        entry = session.get(TreatmentEntry, entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="ไม่พบข้อมูลประวัติการรักษา")
        session.delete(entry)
        session.commit()
        return {"status": "success", "message": f"ลบประวัติการรักษารหัส {entry_id} เรียบร้อยแล้ว"}