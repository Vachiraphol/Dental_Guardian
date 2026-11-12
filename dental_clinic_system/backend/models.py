"""Database models for Dental Guardian."""

import datetime as dt
from typing import Optional
from sqlmodel import Field, SQLModel


def get_utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    full_name: str
    role: str = "patient"
    is_active: bool = True
    created_at: dt.datetime = Field(default_factory=get_utc_now)


class Patient(SQLModel, table=True):
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
    id: Optional[int] = Field(default=None, primary_key=True)
    dentist_id: str = Field(index=True)
    dentist_name: str
    schedule_month: str = "2026-10"
    work_days: str = "1,2,3,4,5"
    start_time: str = "09:00"
    end_time: str = "18:00"
    lunch_time: str = "12:00"
    leaves: str = "[]"


class QueueBooking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: Optional[str] = Field(default=None, index=True)
    patient_name: str
    phone_number: str
    booking_date: dt.date
    booking_time: dt.time
    service_type: str
    dentist_name: Optional[str] = "ไม่ระบุ"
    underlying_disease: Optional[str] = "ไม่มี"
    drug_allergy: Optional[str] = "ไม่มี"
    status: str = "รออนุมัติ"
    booking_code: str = Field(index=True, unique=True)
    notes: Optional[str] = None
    created_at: dt.datetime = Field(default_factory=get_utc_now)


class Appointment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: Optional[str] = Field(default=None, index=True)
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
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: str = Field(index=True)
    tooth_number: str
    icd_code: str
    procedure_name: str
    dentist_name: str = "ทันตแพทย์ผู้ตรวจ"
    notes: Optional[str] = None
    created_at: dt.datetime = Field(default_factory=get_utc_now)

# ========================================================
# JWT AUTHENTICATION & PATIENT PROFILE MODELS
# ========================================================
from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import field_validator
from sqlmodel import Field, SQLModel, Relationship


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, Enum):
    PATIENT = "patient"
    DENTIST = "dentist"
    STAFF = "staff"
    ADMIN = "admin"


class Gender(str, Enum):
    MALE = "ชาย"
    FEMALE = "หญิง"
    OTHER = "ไม่ระบุ"


class AuthUser(SQLModel, table=True):
    __tablename__ = "auth_users"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    role: UserRole = Field(default=UserRole.PATIENT, nullable=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)

    profile: Optional["PatientProfile"] = Relationship(back_populates="user")


class PatientProfile(SQLModel, table=True):
    __tablename__ = "patient_profiles"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="auth_users.id", index=True)
    hn: str = Field(unique=True, index=True)
    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)
    id_card: str = Field(unique=True, index=True, max_length=13, nullable=False)
    phone: str = Field(index=True, max_length=10, nullable=False)
    gender: Gender = Field(default=Gender.OTHER)
    birth_date: Optional[date] = Field(default=None)
    address: Optional[str] = Field(default=None)
    congenital_disease: Optional[str] = Field(default="ไม่มี")
    drug_allergy: Optional[str] = Field(default="ไม่มี")
    created_at: datetime = Field(default_factory=get_utc_now)

    user: Optional[AuthUser] = Relationship(back_populates="profile")

    @field_validator("id_card")
    @classmethod
    def validate_id_card(cls, v: str) -> str:
        v_clean = v.strip().replace("-", "")
        if len(v_clean) != 13 or not v_clean.isdigit():
            raise ValueError("หมายเลขบัตรประชาชนต้องเป็นตัวเลข 13 หลักเท่านั้น")
        return v_clean

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v_clean = v.strip().replace("-", "")
        if len(v_clean) != 10 or not v_clean.isdigit():
            raise ValueError("เบอร์โทรศัพท์ต้องเป็นตัวเลข 10 หลักเท่านั้น")
        return v_clean