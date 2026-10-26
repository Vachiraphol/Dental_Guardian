"""SRS 5.3 (ลูกค้า) หน้าสรุปการจองคิวและยืนยัน."""

import reflex as rx

from dental_clinic_system.components.booking_steps import step_bar
from dental_clinic_system.components.layout import public_page
from dental_clinic_system.components.slip import slip_card
from dental_clinic_system.components.ui import card, card_title, empty_state, info_row
from dental_clinic_system.state import AppState


@rx.page(route="/booking/summary", title="สรุปการจองคิว - Dental Guardian")
def booking_summary() -> rx.Component:
    d = AppState.booking_draft
    return public_page(
        # TODO(backend): show login_required(...) instead when the visitor is not a logged-in patient
        rx.vstack(
            rx.cond(AppState.has_booking_slip, step_bar(3), step_bar(2)),
            rx.cond(
                AppState.has_booking_slip,
                # step 3: slip
                rx.vstack(
                    rx.callout("ส่งคำขอจองคิวเรียบร้อย สถานะ 'รออนุมัติ' — คลินิกจะยืนยันการจองและแจ้งให้ทราบ",
                               icon="circle_check", color_scheme="green", width="100%"),
                    slip_card(AppState.booking_slip),
                    rx.flex(
                        rx.button(rx.icon(tag="printer", size=14), "พิมพ์ใบจองคิว", variant="soft", on_click=rx.call_script("window.print()")),
                        rx.button(rx.icon(tag="calendar_plus", size=14), "เพิ่มลงปฏิทิน", variant="soft",
                                  on_click=AppState.download_ics(AppState.booking_slip["id"])),
                        rx.link(rx.button("ดูตารางนัดหมายของฉัน", color_scheme="purple"), href="/my-appointments"),
                        rx.button("จองคิวเพิ่ม", variant="ghost", on_click=AppState.new_booking),
                        gap="8px",
                        wrap="wrap",
                        justify="center",
                        width="100%",
                    ),
                    max_width="520px",
                    width="100%",
                    margin_x="auto",
                    spacing="4",
                ),
                rx.cond(
                    AppState.has_booking_draft,
                    # step 2: summary & confirm
                    card(
                        card_title("ตรวจสอบรายละเอียดการจอง"),
                        info_row("วันที่", "วัน" + d["weekday"] + "ที่ " + d["date_th"]),
                        info_row("เวลา", d["time"] + " น."),
                        info_row("บริการ", d["service"]),
                        info_row("ทันตแพทย์", rx.cond(d["dentist"] != "", d["dentist"], "ไม่ระบุ (คลินิกจัดให้)")),
                        info_row("ชื่อ-นามสกุล", d["patient_name"]),
                        info_row("เบอร์โทรศัพท์", d["phone"]),
                        info_row("โรคประจำตัว", d["disease"]),
                        info_row("ยาที่แพ้", d["allergy"]),
                        info_row("อาการ / หมายเหตุ", d["note"]),
                        rx.callout("หลังยืนยัน การจองจะอยู่ในสถานะ 'รออนุมัติ' จนกว่าคลินิกจะยืนยันการจองคิว",
                                   icon="info", size="1", margin_top="12px"),
                        rx.hstack(
                            rx.link(rx.button(rx.icon(tag="arrow_left", size=14), "แก้ไข", variant="soft", color_scheme="gray"), href="/booking"),
                            rx.button(rx.icon(tag="check", size=14), "ยืนยันการจองคิว", color_scheme="purple", on_click=AppState.confirm_booking),
                            justify="end",
                            width="100%",
                            margin_top="16px",
                            spacing="2",
                        ),
                        max_width="620px",
                        margin_x="auto",
                    ),
                    empty_state("ยังไม่มีรายการจอง กรุณาเลือกวันและเวลาก่อน", "calendar_search"),
                ),
            ),
            rx.cond(
                ~AppState.has_booking_draft & ~AppState.has_booking_slip,
                rx.link(rx.button("ไปหน้าจองคิว", color_scheme="purple"), href="/booking"),
            ),
            width="100%",
            spacing="5",
            align="center",
        ),
        hero_title="สรุปการจองคิว",
    )
