import reflex as rx
from sqlmodel import select
from datetime import date, datetime, timedelta
import uuid
from typing import List, Optional
from .models import QueueBooking, Appointment

class ScheduleState(rx.State):
    # Form: การจองคิว
    q_name: str = ""
    q_phone: str = ""
    q_date: str = str(date.today())
    q_time: str = "09:00"
    q_service: str = ""
    q_disease: str = ""
    q_allergy: str = ""

    # Form: การนัดหมาย
    appt_name: str = ""
    appt_contact: str = ""
    appt_date: str = str(date.today() + timedelta(days=7))
    appt_time: str = "10:00"
    appt_purpose: str = ""
    appt_notes: str = ""

    # Dashboard & ปฏิทิน
    filter_date: str = str(date.today())
    daily_queues: List[QueueBooking] = []
    daily_appts: List[Appointment] = []

    # ป๊อปอัปใบสรุปและใบนัด
    latest_booking_slip: Optional[QueueBooking] = None
    latest_appointment_slip: Optional[Appointment] = None
    is_booking_slip_ready: bool = False
    is_appointment_slip_ready: bool = False

    def create_queue_booking(self):
        if not self.q_name.strip() or not self.q_phone.strip():
            return rx.toast.error("กรุณาระบุชื่อและเบอร์โทรศัพท์")

        target_date = datetime.strptime(self.q_date, "%Y-%m-%d").date()
        target_time = datetime.strptime(self.q_time, "%H:%M").time()
        code = f"Q-{target_date.strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"

        with rx.session() as session:
            new_booking = QueueBooking(
                patient_name=self.q_name.strip(),
                phone_number=self.q_phone.strip(),
                booking_date=target_date,
                booking_time=target_time,
                service_type=self.q_service or "ตรวจสุขภาพช่องปากทั่วไป",
                underlying_disease=self.q_disease.strip() or "ไม่มี",
                drug_allergy=self.q_allergy.strip() or "ไม่มี",
                status="รออนุมัติ",
                booking_code=code,
            )
            session.add(new_booking)
            session.commit()
            session.refresh(new_booking)

            self.latest_booking_slip = new_booking
            self.is_booking_slip_ready = True

        self.q_name = ""
        self.q_phone = ""
        self.q_disease = ""
        self.q_allergy = ""
        self.load_daily_dashboard()
        return rx.toast.success("บันทึกการจองคิวสำเร็จ")

    def update_queue_status(self, booking_id: int, new_status: str):
        with rx.session() as session:
            booking = session.get(QueueBooking, booking_id)
            if booking:
                booking.status = new_status
                session.add(booking)
                session.commit()
        self.load_daily_dashboard()

    def create_appointment(self):
        if not self.appt_name.strip() or not self.appt_purpose.strip():
            return rx.toast.error("กรุณาระบุชื่อผู้ป่วยและวัตถุประสงค์การนัดหมาย")

        target_date = datetime.strptime(self.appt_date, "%Y-%m-%d").date()
        target_time = datetime.strptime(self.appt_time, "%H:%M").time()
        slip_code = f"AP-{target_date.strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"

        with rx.session() as session:
            new_appt = Appointment(
                patient_name=self.appt_name.strip(),
                contact_info=self.appt_contact.strip() or "-",
                appointment_date=target_date,
                appointment_time=target_time,
                purpose=self.appt_purpose.strip(),
                status="มาตามเวลานัด",
                appointment_slip_code=slip_code,
                notes=self.appt_notes.strip() or None,
            )
            session.add(new_appt)
            session.commit()
            session.refresh(new_appt)

            self.latest_appointment_slip = new_appt
            self.is_appointment_slip_ready = True

        self.appt_name = ""
        self.appt_contact = ""
        self.appt_notes = ""
        self.load_daily_dashboard()
        return rx.toast.success("บันทึกการนัดหมายสำเร็จ")

    def update_appointment_status(self, appt_id: int, new_status: str):
        with rx.session() as session:
            appt = session.get(Appointment, appt_id)
            if appt:
                appt.status = new_status
                session.add(appt)
                session.commit()
        self.load_daily_dashboard()

    def set_filter_date_and_reload(self, new_date: str):
        self.filter_date = new_date
        self.load_daily_dashboard()

    def load_daily_dashboard(self):
        try:
            target = datetime.strptime(self.filter_date, "%Y-%m-%d").date()
        except ValueError:
            target = date.today()

        with rx.session() as session:
            self.daily_queues = session.exec(
                select(QueueBooking).where(QueueBooking.booking_date == target)
            ).all()
            self.daily_appts = session.exec(
                select(Appointment).where(Appointment.appointment_date == target)
            ).all()

    @rx.var
    def total_patients_today(self) -> int:
        return len(self.daily_queues) + len(self.daily_appts)

    @rx.var
    def pending_queues_count(self) -> int:
        return sum(1 for q in self.daily_queues if q.status == "รออนุมัติ")

    @rx.var
    def confirmed_queues_count(self) -> int:
        return sum(1 for q in self.daily_queues if q.status == "ยืนยันการจองคิว")

    def close_booking_slip(self):
        self.is_booking_slip_ready = False

    def close_appointment_slip(self):
        self.is_appointment_slip_ready = False