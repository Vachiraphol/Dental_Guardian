"""Unit tests for Pydantic request/response schemas in api_auth.py."""

import pytest
from pydantic import ValidationError
from dental_clinic_system.backend.api_auth import (
    LoginRequest,
    RegisterRequest,
    PatientCreateRequest,
)


def test_login_request_valid():
    req = LoginRequest(username="dentist_01", password="secure_password", role="staff")
    assert req.username == "dentist_01"
    assert req.role == "staff"


def test_login_request_missing_required_field():
    with pytest.raises(ValidationError):
        # Missing password
        LoginRequest(username="dentist_01", role="staff")  # type: ignore


def test_register_request_defaults():
    req = RegisterRequest(
        first_name="กานต์",
        last_name="ใจดี",
        phone="0812345678",
        email="karn@example.com",
        password="PassWord123!",
        confirm="PassWord123!",
    )
    assert req.first_name == "กานต์"
    assert req.gender == "ไม่ระบุ"
    assert req.disease == "ไม่มี"
    assert req.allergy == "ไม่มี"
    assert req.national_id is None


def test_patient_create_request_valid():
    req = PatientCreateRequest(
        first_name="มานะ",
        last_name="อดทน",
        phone_number="0899998888",
    )
    assert req.first_name == "มานะ"
    assert req.gender == "ไม่ระบุ"
    assert req.underlying_disease == "ไม่มี"

