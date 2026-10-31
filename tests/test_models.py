"""Unit tests for SQLModel database models."""

import datetime as dt
from sqlmodel import select
from dental_clinic_system.backend.models import (
    User,
    Patient,
    QueueBooking,
    Appointment,
    TreatmentEntry,
    DoctorSchedule,
)


def test_create_user(session):
    user = User(
        username="dentist_somchai",
        password_hash="hashed_pw_xyz",
        full_name="นพ.สมชาย ใจดี",
        role="dentist",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    assert user.id is not None
    assert user.username == "dentist_somchai"
    assert user.role == "dentist"
    assert user.is_active is True
    assert user.created_at is not None


def test_create_patient(session):
    patient = Patient(
        hn_code="HN20261001",
        first_name="สมหญิง",
        last_name="รักดี",
        phone_number="0891234567",
        email="somying@example.com",
    )
    session.add(patient)
    session.commit()
    session.refresh(patient)

    assert patient.id is not None
    assert patient.hn_code == "HN20261001"
    assert patient.gender == "ไม่ระบุ"
    assert patient.underlying_disease == "ไม่มี"
    assert patient.drug_allergy == "ไม่มี"


def test_create_queue_booking(session):
    booking = QueueBooking(
        patient_id="HN20261001",
        patient_name="สมหญิง รักดี",
        phone_number="0891234567",
        booking_date=dt.date(2026, 11, 1),
        booking_time=dt.time(10, 0),
        service_type="ตรวจสุขภาพฟัน",
        booking_code="QB-20261101-001",
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)

    assert booking.id is not None
    assert booking.status == "รออนุมัติ"
    assert booking.dentist_name == "ไม่ระบุ"
    assert booking.booking_code == "QB-20261101-001"


def test_create_appointment(session):
    appointment = Appointment(
        patient_id="HN20261001",
        patient_name="สมหญิง รักดี",
        contact_info="0891234567",
        appointment_date=dt.date(2026, 11, 10),
        appointment_time=dt.time(14, 30),
        appointment_slip_code="SLIP-9999",
    )
    session.add(appointment)
    session.commit()
    session.refresh(appointment)

    assert appointment.id is not None
    assert appointment.status == "ยืนยันแล้ว"
    assert appointment.purpose == "นัดติดตามอาการ"


def test_create_treatment_entry(session):
    entry = TreatmentEntry(
        patient_id="HN20261001",
        tooth_number="18",
        icd_code="K02.1",
        procedure_name="อุดฟันด้วยคอมโพสิต",
        dentist_name="ทพ. สมหมาย",
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)

    assert entry.id is not None
    assert entry.tooth_number == "18"
    assert entry.icd_code == "K02.1"


def test_query_patient_by_hn(session):
    p1 = Patient(
        hn_code="HN001",
        first_name="A",
        last_name="B",
        phone_number="0800000001",
    )
    p2 = Patient(
        hn_code="HN002",
        first_name="C",
        last_name="D",
        phone_number="0800000002",
    )
    session.add_all([p1, p2])
    session.commit()

    statement = select(Patient).where(Patient.hn_code == "HN002")
    result = session.exec(statement).first()

    assert result is not None
    assert result.first_name == "C"
    assert result.last_name == "D"

