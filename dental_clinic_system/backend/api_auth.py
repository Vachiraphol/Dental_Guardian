import uuid
import datetime as dt
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select
import reflex as rx

from .models import User, Patient, get_utc_now

# ---------------------------------------------------------------------------
# Router Definitions
# ---------------------------------------------------------------------------
router_auth = APIRouter(prefix="/auth", tags=["SRS 5.2: Authentication & Member"])
router_patient = APIRouter(prefix="/patients", tags=["SRS 5.1: Patient Records"])


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: str
    password: str
    confirm: str
    national_id: Optional[str] = None
    dob: Optional[str] = None  # Format: YYYY-MM-DD
    gender: Optional[str] = "ไม่ระบุ"
    address: Optional[str] = None
    disease: Optional[str] = "ไม่มี"
    allergy: Optional[str] = "ไม่มี"


class LoginRequest(BaseModel):
    username: str
    password: str
    role: str = "patient"  # "patient" or "staff"


class ChangePasswordRequest(BaseModel):
    email: str
    current_password: str
    new_password: str
    confirm_password: str


class RequestResetRequest(BaseModel):
    email: str


class ConfirmResetRequest(BaseModel):
    email: str
    otp: str
    new_password: str
    confirm_password: str


class PatientUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    underlying_disease: Optional[str] = None
    drug_allergy: Optional[str] = None


# เพิ่มคลาสนี้เพื่อแก้ NameError: name 'PatientCreateRequest' is not defined
class PatientCreateRequest(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    national_id: Optional[str] = None
    email: Optional[str] = None
    birth_date: Optional[str] = None  # รูปแบบ YYYY-MM-DD
    gender: Optional[str] = "ไม่ระบุ"
    address: Optional[str] = None
    underlying_disease: Optional[str] = "ไม่มี"
    drug_allergy: Optional[str] = "ไม่มี"


# ===========================================================================
# SRS 5.2: User Authentication & Member Management
# ===========================================================================

@router_auth.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest):
    """สมัครสมาชิกผู้ป่วยใหม่: สร้างบัญชีใน User และเปิดเวชระเบียนใน Patient"""
    first_name = payload.first_name.strip()
    last_name = payload.last_name.strip()
    phone = payload.phone.strip()
    email = payload.email.strip().lower()

    if not first_name or not last_name or not phone or not email or not payload.password:
        raise HTTPException(status_code=400, detail="กรุณากรอกข้อมูลสำคัญให้ครบถ้วน")
    if payload.password != payload.confirm:
        raise HTTPException(status_code=400, detail="รหัสผ่านและการยืนยันรหัสผ่านไม่ตรงกัน")
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร")

    with rx.session() as session:
        existing_user = session.exec(select(User).where(User.username == email)).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="อีเมลนี้ถูกใช้งานในระบบแล้ว")

        new_user = User(
            username=email,
            password_hash=payload.password,
            full_name=f"{first_name} {last_name}",
            role="patient",
            is_active=True,
            created_at=get_utc_now(),
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        dob_val = None
        if payload.dob:
            try:
                dob_val = dt.date.fromisoformat(payload.dob)
            except ValueError:
                pass

        # รันรหัสผู้ป่วย P-0001, P-0002 เรียงตามลำดับจำนวนคนไข้
        patient_count = len(session.exec(select(Patient)).all())
        hn_code = f"P-{patient_count + 1:04d}"

        new_patient = Patient(
            user_id=new_user.id,
            hn_code=hn_code,
            national_id=payload.national_id or None,
            first_name=first_name,
            last_name=last_name,
            email=email,
            birth_date=dob_val,
            gender=payload.gender or "ไม่ระบุ",
            phone_number=phone,
            address=payload.address or None,
            underlying_disease=payload.disease or "ไม่มี",
            drug_allergy=payload.allergy or "ไม่มี",
            created_at=get_utc_now(),
        )
        session.add(new_patient)
        session.commit()
        session.refresh(new_patient)

        return {
            "message": "สมัครสมาชิกสำเร็จ",
            "user_id": new_user.id,
            "hn_code": new_patient.hn_code,
        }


@router_auth.post("/login")
def login_user(payload: LoginRequest):
    """เข้าสู่ระบบพร้อมตรวจสอบสิทธิ์ (Role-based Authentication)"""
    email = payload.username.strip().lower()
    with rx.session() as session:
        user = session.exec(select(User).where(User.username == email)).first()
        if not user or user.password_hash != payload.password:
            raise HTTPException(status_code=401, detail="อีเมลหรือรหัสผ่านไม่ถูกต้อง")

        if payload.role == "staff" and user.role not in ("staff", "dentist", "admin"):
            raise HTTPException(status_code=403, detail="บัญชีนี้ไม่มีสิทธิ์เข้าใช้งานในส่วนทันตแพทย์/เจ้าหน้าที่")
        if payload.role == "patient" and user.role != "patient":
            raise HTTPException(status_code=403, detail="บัญชีนี้ไม่ใช่บัญชีผู้ป่วย")

        patient_info = None
        if user.role == "patient":
            patient = session.exec(
                select(Patient).where(
                    (Patient.user_id == user.id) | (Patient.email == user.username)
                )
            ).first()
            if patient:
                patient_info = {
                    "hn_code": patient.hn_code,
                    "first_name": patient.first_name,
                    "last_name": patient.last_name,
                    "phone": patient.phone_number,
                }

        return {
            "message": "เข้าสู่ระบบสำเร็จ",
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role,
            },
            "patient": patient_info,
        }


@router_auth.post("/change-password")
def change_password(payload: ChangePasswordRequest):
    """เปลี่ยนรหัสผ่านผู้ใช้งาน"""
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="รหัสผ่านใหม่ต้องมีอย่างน้อย 8 ตัวอักษร")
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="รหัสผ่านใหม่และการยืนยันไม่ตรงกัน")
    if payload.new_password == payload.current_password:
        raise HTTPException(status_code=400, detail="รหัสผ่านใหม่ต้องไม่ซ้ำกับรหัสผ่านเดิม")

    with rx.session() as session:
        user = session.exec(select(User).where(User.username == payload.email.lower())).first()
        if not user or user.password_hash != payload.current_password:
            raise HTTPException(status_code=400, detail="รหัสผ่านปัจจุบันไม่ถูกต้อง")

        user.password_hash = payload.new_password
        session.add(user)
        session.commit()

        return {"message": "เปลี่ยนรหัสผ่านเรียบร้อยแล้ว"}


@router_auth.post("/forgot-password/request")
def request_password_reset(payload: RequestResetRequest):
    """ขอรีเซ็ตรหัสผ่านผ่านอีเมล"""
    with rx.session() as session:
        user = session.exec(select(User).where(User.username == payload.email.lower())).first()
        if not user:
            raise HTTPException(status_code=404, detail="ไม่พบบัญชีผู้ใช้งานที่ใช้อีเมลนี้")
        return {"message": "ระบบได้จำลองการส่งรหัสยืนยัน OTP ไปยังอีเมลของท่านแล้ว", "email": payload.email}


@router_auth.post("/forgot-password/confirm")
def confirm_password_reset(payload: ConfirmResetRequest):
    """ยืนยันการตั้งรหัสผ่านใหม่ด้วย OTP"""
    if len(payload.new_password) < 8 or payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="รหัสผ่านใหม่ต้องมีอย่างน้อย 8 ตัวอักษรและตรงกัน")

    with rx.session() as session:
        user = session.exec(select(User).where(User.username == payload.email.lower())).first()
        if not user:
            raise HTTPException(status_code=404, detail="ไม่พบข้อมูลบัญชีผู้ใช้")

        user.password_hash = payload.new_password
        session.add(user)
        session.commit()
        return {"message": "ตั้งรหัสผ่านใหม่เรียบร้อยแล้ว"}


# ===========================================================================
# SRS 5.1: Patient Records Management
# ===========================================================================

@router_patient.get("/")
def list_all_patients(search: Optional[str] = None):
    """ดึงรายชื่อและเวชระเบียนของผู้ป่วยทั้งหมดในระบบ (รองรับการค้นหาตามชื่อ/เบอร์/รหัส)"""
    with rx.session() as session:
        query = select(Patient)
        if search:
            s = f"%{search.strip()}%"
            query = query.where(
                (Patient.hn_code.like(s))
                | (Patient.first_name.like(s))
                | (Patient.last_name.like(s))
                | (Patient.phone_number.like(s))
            )
        patients = session.exec(query.order_by(Patient.id.desc())).all()
        return [
            {
                "id": p.id,
                "hn_code": p.hn_code,
                "full_name": f"{p.first_name} {p.last_name}",
                "national_id": p.national_id or "-",
                "phone_number": p.phone_number,
                "email": p.email or "-",
                "birth_date": p.birth_date.isoformat() if p.birth_date else None,
                "gender": p.gender or "-",
                "address": p.address or "-",
                "underlying_disease": p.underlying_disease or "ไม่มี",
                "drug_allergy": p.drug_allergy or "ไม่มี",
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in patients
        ]


@router_patient.post("/", status_code=status.HTTP_201_CREATED)
def create_patient_record(payload: PatientCreateRequest):
    """สร้างเวชระเบียนผู้ป่วยใหม่ พร้อมออกรหัส P-0001 อัตโนมัติ"""
    with rx.session() as session:
        # คำนวณรหัส P-0001, P-0002 เรียงตามลำดับจำนวนคนไข้
        total_patients = len(session.exec(select(Patient)).all())
        hn_code = f"P-{total_patients + 1:04d}"

        # แปลงสตริงวันเกิดถ้ามีส่งมา
        dob = None
        if payload.birth_date:
            try:
                dob = dt.date.fromisoformat(payload.birth_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="รูปแบบวันเกิดไม่ถูกต้อง (ต้องเป็น YYYY-MM-DD)")

        new_patient = Patient(
            hn_code=hn_code,
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            national_id=payload.national_id.strip() if payload.national_id else None,
            phone_number=payload.phone_number.strip(),
            email=payload.email.strip() if payload.email else None,
            birth_date=dob,
            gender=payload.gender or "ไม่ระบุ",
            address=payload.address.strip() if payload.address else None,
            underlying_disease=payload.underlying_disease.strip() if payload.underlying_disease else "ไม่มี",
            drug_allergy=payload.drug_allergy.strip() if payload.drug_allergy else "ไม่มี",
            created_at=get_utc_now(),
        )
        session.add(new_patient)
        session.commit()
        session.refresh(new_patient)

        return {
            "message": "สร้างเวชระเบียนผู้ป่วยสำเร็จ",
            "hn_code": new_patient.hn_code,
            "patient_id": new_patient.id,
        }


@router_patient.get("/{hn_code}")
def get_patient_by_hn(hn_code: str):
    """ค้นหาและดึงข้อมูลเวชระเบียนผู้ป่วยรายบุคคลตามรหัสผู้ป่วย (เช่น P-0001)"""
    with rx.session() as session:
        p = session.exec(select(Patient).where(Patient.hn_code == hn_code.upper())).first()
        if not p:
            raise HTTPException(status_code=404, detail=f"ไม่พบข้อมูลผู้ป่วยรหัส {hn_code}")
        return {
            "id": p.id,
            "hn_code": p.hn_code,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "full_name": f"{p.first_name} {p.last_name}",
            "national_id": p.national_id or "-",
            "phone_number": p.phone_number,
            "email": p.email or "-",
            "birth_date": p.birth_date.isoformat() if p.birth_date else None,
            "gender": p.gender or "-",
            "address": p.address or "-",
            "underlying_disease": p.underlying_disease or "ไม่มี",
            "drug_allergy": p.drug_allergy or "ไม่มี",
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }


@router_patient.put("/{hn_code}")
def update_patient_record(hn_code: str, payload: PatientUpdateRequest):
    """อัปเดตข้อมูลเวชระเบียนและประวัติสุขภาพของผู้ป่วย"""
    with rx.session() as session:
        p = session.exec(select(Patient).where(Patient.hn_code == hn_code.upper())).first()
        if not p:
            raise HTTPException(status_code=404, detail=f"ไม่พบข้อมูลผู้ป่วยรหัส {hn_code}")

        if payload.first_name:
            p.first_name = payload.first_name.strip()
        if payload.last_name:
            p.last_name = payload.last_name.strip()
        if payload.phone_number:
            p.phone_number = payload.phone_number.strip()
        if payload.address is not None:
            p.address = payload.address.strip() or None
        if payload.underlying_disease is not None:
            p.underlying_disease = payload.underlying_disease.strip() or "ไม่มี"
        if payload.drug_allergy is not None:
            p.drug_allergy = payload.drug_allergy.strip() or "ไม่มี"

        # อัปเดตชื่อในตาราง User ด้วยหากผูกบัญชีไว้
        if p.user_id:
            u = session.exec(select(User).where(User.id == p.user_id)).first()
            if u:
                u.full_name = f"{p.first_name} {p.last_name}"
                session.add(u)

        session.add(p)
        session.commit()
        session.refresh(p)

        return {"message": "อัปเดตเวชระเบียนผู้ป่วยเรียบร้อยแล้ว", "hn_code": p.hn_code}