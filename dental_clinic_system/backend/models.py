from datetime import date, datetime
from enum import Enum
from typing import Optional, List
from pydantic import field_validator
from sqlmodel import Field, SQLModel, Relationship


class UserRole(str, Enum):
    PATIENT = "patient"
    DENTIST = "dentist"
    STAFF = "staff"
    ADMIN = "admin"


class Gender(str, Enum):
    MALE = "ชาย"
    FEMALE = "หญิง"
    OTHER = "ไม่ระบุ"


# --- 1. User Account & Authentication Model ---
class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    role: UserRole = Field(default=UserRole.PATIENT, nullable=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    profile: Optional["PatientProfile"] = Relationship(back_populates="user")


# --- 2. Patient Profile & Medical Information Model ---
class PatientProfile(SQLModel, table=True):
    __tablename__ = "patient_profiles"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    hn: str = Field(unique=True, index=True, description="Hospital / Patient Number e.g. HN0001")
    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)
    id_card: str = Field(unique=True, index=True, max_length=13, nullable=False)
    phone: str = Field(index=True, max_length=10, nullable=False)
    gender: Gender = Field(default=Gender.OTHER)
    birth_date: Optional[date] = Field(default=None)
    address: Optional[str] = Field(default=None)
    
    # ข้อมูลประวัติการแพทย์ (Medical History)
    congenital_disease: Optional[str] = Field(default="ไม่มี", description="โรคประจำตัว")
    drug_allergy: Optional[str] = Field(default="ไม่มี", description="ประวัติแพ้ยา")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: Optional[User] = Relationship(back_populates="profile")

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


# --- 3. Clinical & Booking Models (คงไว้ตามระบบเดิม) ---
class QueueBooking(SQLModel, table=True):
    __tablename__ = "queue_bookings"

    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="patient_profiles.id")
    booking_date: date = Field(nullable=False)
    time_slot: str = Field(nullable=False)
    service_type: str = Field(nullable=False)
    dentist_id: Optional[int] = Field(default=None)
    status: str = Field(default="confirmed")  # pending, confirmed, cancelled, completed
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Appointment(SQLModel, table=True):
    __tablename__ = "appointments"

    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="patient_profiles.id")
    dentist_id: int = Field(foreign_key="users.id")
    appointment_date: datetime = Field(nullable=False)
    treatment_type: str = Field(nullable=False)
    notes: Optional[str] = Field(default=None)
    status: str = Field(default="scheduled")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TreatmentEntry(SQLModel, table=True):
    __tablename__ = "treatment_entries"

    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="patient_profiles.id", index=True)
    dentist_id: int = Field(foreign_key="users.id")
    tooth_number: str = Field(nullable=False, description="FDI tooth notation (e.g., 11-48, 51-85)")
    icd10_code: str = Field(nullable=False)
    icd10_name: str = Field(nullable=False)
    procedure_name: str = Field(nullable=False)
    note: Optional[str] = Field(default=None)
    recorded_at: datetime = Field(default_factory=datetime.utcnow)