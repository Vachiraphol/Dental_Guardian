"""conftest.py - การตั้งค่า Fixture ส่วนกลางสำหรับ Pytest.

ไฟล์นี้ทำหน้าที่:
1. เตรียม In-Memory SQLite Database สำหรับทดสอบ (ไม่ต้องเปิด PostgreSQL จริง)
2. Mock ฟังก์ชัน rx.session() ของ Reflex ให้ชี้มาที่ In-Memory Database ของเทสต์
"""

import pytest
from sqlmodel import SQLModel, create_engine, Session
import reflex as rx

# ต้อง Import models ก่อนเรียก SQLModel.metadata.create_all เพื่อให้รู้จักทุกตาราง
import dental_clinic_system.backend.models


@pytest.fixture(name="engine", scope="function")
def engine_fixture():
    """สร้าง Engine ฐานข้อมูล SQLite ใน RAM (In-Memory) สำหรับแต่ละเคสทดสอบ

    ทำให้ข้อมูลในแต่ละเทสต์แยกขาดจากกัน (Isolation) ไม่กระทบกันเอง
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(name="session", scope="function")
def session_fixture(engine, monkeypatch):
    """Fixture ส่ง session ให้เทสต์ และแทนที่ rx.session() ชั่วคราว

    เมื่อโค้ดฝั่ง Backend ของ Reflex เรียก `with rx.session() as s:`
    จะถูกเปลี่ยนให้ใช้ In-Memory SQLite ในการทดสอบโดยอัตโนมัติ
    """
    # จำลอง rx.session ให้ส่ง Session ที่ผูกกับ Test Engine ใน RAM
    def get_test_session(url: str | None = None):
        return Session(engine)

    monkeypatch.setattr(rx, "session", get_test_session)

    # ส่ง session ให้กับฟังก์ชันทดสอบที่ต้องการเรียกตรง ๆ
    with Session(engine) as session:
        yield session
