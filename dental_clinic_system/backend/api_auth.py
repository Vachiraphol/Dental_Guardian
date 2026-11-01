import uuid
import random
import datetime as dt
from typing import Optional, Dict
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select
from passlib.context import CryptContext
import reflex as rx

from .models import User, Patient, get_utc_now

# ---------------------------------------------------------------------------
# Password Hashing Configuration (bcrypt)
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """แฮชรหัสผ่านด้วย bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """ตรวจสอบความถูกต้องของรหัสผ่าน plain text กับ hash ในฐานข้อมูล"""
    return pwd_context.verify(plain_password, hashed_password)

# ---------------------------------------------------------------------------
# In-Memory OTP Storage for Password Reset (Key: email -> Dict)
# ---------------------------------------------------------------------------
OTP_STORAGE: Dict[str, dict] = {}

def generate_numeric_otp(length: int = 6) -> str:
    """สุ่มรหัสตัวเลข OTP ตามความยาวที่กำหนด"""
    return "".join([str(random.randint(0, 9)) for _ in range(length)])

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


class PatientCreateRequest(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    national_id: Optional[str] = None
    email: Optional[str] = None
    birth_date: Optional[str] = None  # Format: YYYY-MM-DD
    gender: Optional[str] = "ไม่ระบุ"
    address: Optional[str] = None
    underlying_disease: Optional[str] = "ไม่มี"
    drug_allergy: Optional[str] = "ไม่มี"


# ---------------------------------------------------------------------------
# SRS 5.2: Password Reset via OTP (Email / Phone)
# ---------------------------------------------------------------------------

@router_auth.post("/forgot-password/request")
def request_password_reset_otp(payload: dict):
    """ขอรหัส OTP สำหรับรีเซ็ตรหัสผ่าน (รองรับทั้งอีเมล หรือ หมายเลขโทรศัพท์)"""
    identifier = payload.get("phone_or_email", "").strip()
    if not identifier:
        raise HTTPException(status_code=400, detail="กรุณาระบุอีเมลหรือหมายเลขโทรศัพท์")

    with rx.session() as session:
        # 1. ลองค้นหาด้วยอีเมลในตาราง User
        user = session.exec(
            select(User).where(User.username == identifier.lower())
        ).first()

        # 2. ถ้าไม่พบ ให้ลองค้นหาด้วยเบอร์โทรศัพท์ในตาราง Patient แล้วดึง User ที่เชื่อมโยงกัน
        if not user:
            patient = session.exec(
                select(Patient).where(Patient.phone_number == identifier)
            ).first()
            if patient and patient.user_id:
                user = session.exec(select(User).where(User.id == patient.user_id)).first()
            elif patient and patient.email:
                user = session.exec(select(User).where(User.username == patient.email)).first()

        if not user:
            raise HTTPException(status_code=404, detail="ไม่พบบัญชีผู้ใช้งานในระบบ")

        # สร้าง OTP 6 หลัก และกำหนดเวลาหมดอายุ 5 นาที
        otp_code = generate_numeric_otp(6)
        expires_at = dt.datetime.now() + dt.timedelta(minutes=5)
        
        # บันทึกลงหน่วยความจำ (ผูกกับ username/email จริงของ user เสมอ)
        storage_key = user.username.lower()
        OTP_STORAGE[storage_key] = {
            "code": otp_code,
            "expires_at": expires_at,
            "user_id": user.id,
        }

        # แสดง OTP ในคอนโซลฝั่ง Backend เพื่อใช้ในการตรวจสอบ
        print(f"\n[SECURITY OTP SERVICE] Target: {user.username} (Input: {identifier}) | OTP: {otp_code} | Expires: {expires_at.strftime('%H:%M:%S')}\n")

        return {
            "status": "success",
            "message": "รหัส OTP ถูกสร้างเรียบร้อยแล้ว มีอายุ 5 นาที",
            "account_identifier": user.username,
        }


@router_auth.post("/forgot-password/confirm")
def confirm_password_reset(payload: dict):
    """ตรวจสอบความถูกต้องของ OTP และทำการแฮชรหัสผ่านใหม่ลงฐานข้อมูล"""
    identifier = payload.get("phone_or_email", "").strip()
    otp_code = payload.get("otp_code", "").strip()
    new_password = payload.get("new_password", "").strip()

    if not identifier or not otp_code or not new_password:
        raise HTTPException(status_code=400, detail="กรุณากรอกข้อมูลให้ครบถ้วน")
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="รหัสผ่านใหม่ต้องมีความยาวอย่างน้อย 8 ตัวอักษร")

    with rx.session() as session:
        # ค้นหาผู้ใช้จากอีเมลหรือเบอร์โทร
        user = session.exec(
            select(User).where(User.username == identifier.lower())
        ).first()

        if not user:
            patient = session.exec(
                select(Patient).where(Patient.phone_number == identifier)
            ).first()
            if patient and patient.user_id:
                user = session.exec(select(User).where(User.id == patient.user_id)).first()
            elif patient and patient.email:
                user = session.exec(select(User).where(User.username == patient.email)).first()

        if not user:
            raise HTTPException(status_code=404, detail="ไม่พบข้อมูลผู้ใช้งานในระบบ")

        storage_key = user.username.lower()
        record = OTP_STORAGE.get(storage_key)

        if not record or record.get("code") != otp_code:
            raise HTTPException(status_code=400, detail="รหัส OTP ไม่ถูกต้อง")
        if dt.datetime.now() > record.get("expires_at"):
            OTP_STORAGE.pop(storage_key, None)
            raise HTTPException(status_code=400, detail="รหัส OTP หมดอายุแล้ว กรุณาขอใหม่อีกครั้ง")

        # แฮชรหัสผ่านใหม่ด้วย bcrypt และอัปเดตลงฐานข้อมูล
        user.password_hash = hash_password(new_password)
        session.add(user)
        session.commit()

        # เคลียร์ OTP ทิ้งหลังใช้งานสำเร็จ
        OTP_STORAGE.pop(storage_key, None)

        return {
            "status": "success",
            "message": "เปลี่ยนรหัสผ่านสำเร็จเรียบร้อยแล้ว สามารถเข้าสู่ระบบด้วยรหัสผ่านใหม่ได้ทันที",
        }

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
    """สร้างเวชระเบียนผู้ป่วยใหม่ พร้อมออกรหัส P-XXXX อัตโนมัติ"""
    with rx.session() as session:
        total_patients = len(session.exec(select(Patient)).all())
        hn_code = f"P-{total_patients + 1:04d}"

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
    """ค้นหาและดึงข้อมูลเวชระเบียนผู้ป่วยรายบุคคลตามรหัสผู้ป่วย"""
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

        if p.user_id:
            u = session.exec(select(User).where(User.id == p.user_id)).first()
            if u:
                u.full_name = f"{p.first_name} {p.last_name}"
                session.add(u)

        session.add(p)
        session.commit()
        session.refresh(p)

        return {"message": "อัปเดตเวชระเบียนผู้ป่วยเรียบร้อยแล้ว", "hn_code": p.hn_code}