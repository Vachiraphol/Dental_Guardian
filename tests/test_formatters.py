"""Unit tests for formatting and helper functions in state.py."""

from dental_clinic_system.state import (
    calc_age,
    th_date,
    format_patient,
    format_appointment,
)


def test_calc_age_valid_date():
    # Born in 2000, current year 2026 -> age should be 26
    age = calc_age("2000-01-01")
    assert age == 26


def test_calc_age_invalid_date():
    assert calc_age("not-a-date") == 0
    assert calc_age("") == 0


def test_th_date_converts_year_to_buddhist_era():
    # 2026 -> 2569
    result = th_date("2026-10-15")
    assert "2569" in result
    assert "15" in result


def test_th_date_fallback_on_invalid():
    assert th_date("invalid") == "invalid"
    assert th_date("") == "-"


def test_format_patient_adds_computed_fields():
    patient = {
        "id": "1",
        "first_name": "สมชาย",
        "last_name": "ใจดี",
        "dob": "2000-01-01",
        "registered": "2026-01-01",
    }
    formatted = format_patient(patient)

    assert formatted["full_name"] == "สมชาย ใจดี"
    assert formatted["age"] == "26"
    assert "2543" in formatted["dob_th"]  # 2000 + 543 = 2543
    assert "2569" in formatted["registered_th"]  # 2026 + 543 = 2569


def test_format_patient_empty_dob():
    patient = {
        "id": "2",
        "first_name": "สมหญิง",
        "last_name": "มีสุข",
        "dob": "",
        "registered": "",
    }
    formatted = format_patient(patient)

    assert formatted["full_name"] == "สมหญิง มีสุข"
    assert formatted["age"] == "-"
    assert formatted["dob_th"] == "-"


def test_format_appointment():
    appt = {
        "id": "A001",
        "kind": "จองคิว",
        "patient_id": "P001",
        "date": "2026-10-15",
        "time": "10:00",
    }
    formatted = format_appointment(appt)

    assert "date_th" in formatted
    assert "2569" in formatted["date_th"]
    assert "weekday" in formatted

