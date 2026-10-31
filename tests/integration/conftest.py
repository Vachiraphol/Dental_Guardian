"""conftest.py สำหรับ Integration Tests.

คุณสมบัติ:
1. รองรับทั้ง PostgreSQL (ผ่าน TEST_DATABASE_URL) และ In-Memory SQLite อัตโนมัติ
2. แยก Engine และ Database แยกขาดกันในแต่ละเคสทดสอบ (Function-scoped Isolation)
3. สลับฟังก์ชัน rx.session() ของ Reflex ให้ชี้มาที่ Integration Database
"""

import os
import pytest
from sqlalchemy import event
from sqlmodel import SQLModel, create_engine, Session
import reflex as rx

# ต้อง Import models ทั้งหมดเพื่อให้ SQLModel รู้จักโครงสร้างตารางทุกตาราง
import dental_clinic_system.backend.models


@pytest.fixture(scope="function")
def integration_session(monkeypatch):
    """Fixture ให้บริการ Database Session แยกเดี่ยวสำหรับแต่ละ Scenario"""
    # ตรวจสอบว่ามีกำหนด PostgreSQL หรือไม่ (เช่น บน Docker หรือ CI)
    db_url = os.getenv(
        "TEST_DATABASE_URL",
        "sqlite:///:memory:",
    )
    is_sqlite = db_url.startswith("sqlite")
    connect_args = {"check_same_thread": False} if is_sqlite else {}

    engine = create_engine(db_url, connect_args=connect_args)

    # หากใช้ SQLite ให้เปิดการบังคับใช้ Foreign Key Constraints เหมือน Database จริง
    if is_sqlite:
        @event.listens_for(engine, "connect")
        def set_sqlite_foreign_keys(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.close()

    # สร้างตารางทั้งหมดก่อนเริ่มแต่ละเทสต์
    SQLModel.metadata.create_all(engine)

    def get_test_session(url: str | None = None):
        return Session(engine)

    monkeypatch.setattr(rx, "session", get_test_session)

    with Session(engine) as session:
        yield session

    # ล้างตารางและคืน Connection หลังเทสต์จบ
    SQLModel.metadata.drop_all(engine)
    engine.dispose()
