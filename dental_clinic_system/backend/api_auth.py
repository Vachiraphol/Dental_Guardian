from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select
from datetime import date
from typing import Optional

from .database import get_session
from .models import User, PatientProfile, UserRole, Gender
from .auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# --- Schemas ---
class RegisterPatientRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    id_card: str
    phone: str
    gender: Gender = Gender.OTHER
    birth_date: Optional[date] = None
    address: Optional[str] = None
    congenital_disease: Optional[str] = "ไม่มี"
    drug_allergy: Optional[str] = "ไม่มี"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    full_name: str


class UserProfileResponse(BaseModel):
    id: int
    email: str
    role: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    hn: Optional[str] = None


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_patient(payload: RegisterPatientRequest, session: Session = Depends(get_session)):
    # 1. ตรวจสอบ Email ซ้ำ
    existing_user = session.exec(select(User).where(User.email == payload.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="อีเมลนี้ถูกใช้งานในระบบแล้ว")

    # 2. ตรวจสอบเลขบัตรประชาชนซ้ำ
    clean_id = payload.id_card.strip().replace("-", "")
    existing_id = session.exec(select(PatientProfile).where(PatientProfile.id_card == clean_id)).first()
    if existing_id:
        raise HTTPException(status_code=400, detail="หมายเลขบัตรประชาชนนี้มีข้อมูลในระบบแล้ว")

    # 3. สร้าง User
    new_user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        role=UserRole.PATIENT,
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    # 4. สร้าง Running Number HN (เช่น HN0001)
    hn_count = len(session.exec(select(PatientProfile)).all()) + 1
    new_hn = f"HN{hn_count:04d}"

    # 5. สร้าง Patient Profile
    new_profile = PatientProfile(
        user_id=new_user.id,
        hn=new_hn,
        first_name=payload.first_name,
        last_name=payload.last_name,
        id_card=clean_id,
        phone=payload.phone.strip().replace("-", ""),
        gender=payload.gender,
        birth_date=payload.birth_date,
        address=payload.address,
        congenital_disease=payload.congenital_disease,
        drug_allergy=payload.drug_allergy,
    )
    session.add(new_profile)
    session.commit()

    token = create_access_token({"sub": str(new_user.id), "role": new_user.role.value})
    return TokenResponse(
        access_token=token,
        role=new_user.role.value,
        user_id=new_user.id,
        full_name=f"{new_profile.first_name} {new_profile.last_name}",
    )


@router.post("/token", response_model=TokenResponse)
@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="อีเมลหรือรหัสผ่านไม่ถูกต้อง")

    profile = session.exec(select(PatientProfile).where(PatientProfile.user_id == user.id)).first()
    full_name = f"{profile.first_name} {profile.last_name}" if profile else user.email

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(
        access_token=token,
        role=user.role.value,
        user_id=user.id,
        full_name=full_name,
    )


@router.get("/me", response_model=UserProfileResponse)
def get_me(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    profile = session.exec(select(PatientProfile).where(PatientProfile.user_id == current_user.id)).first()
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role.value,
        first_name=profile.first_name if profile else None,
        last_name=profile.last_name if profile else None,
        phone=profile.phone if profile else None,
        hn=profile.hn if profile else None,
    )