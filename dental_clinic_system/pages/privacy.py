"""SRS 5.2 หน้าตั้งค่าความเป็นส่วนตัว."""

import reflex as rx

from dental_clinic_system.components.layout import member_page
from dental_clinic_system.components.ui import card, card_title, page_header
from dental_clinic_system.state import AppState


def privacy_item(key: str, title: str, description: str, icon: str) -> rx.Component:
    return rx.hstack(
        rx.center(rx.icon(tag=icon, size=18, color="var(--primary-color)"), width="40px", height="40px",
                  border_radius="10px", background_color="var(--primary-light)", flex_shrink="0"),
        rx.vstack(
            rx.text(title, weight="bold", size="2"),
            rx.text(description, size="1", color="var(--slate-10)"),
            spacing="0",
        ),
        rx.spacer(),
        rx.switch(checked=AppState.privacy[key], on_change=lambda _: AppState.toggle_privacy(key), color_scheme="purple"),
        width="100%",
        align="center",
        padding_y="14px",
        border_bottom="1px solid var(--slate-3)",
    )


@rx.page(route="/profile/privacy", title="ตั้งค่าความเป็นส่วนตัว - Dental Guardian")
def privacy() -> rx.Component:
    return member_page(
        "privacy",
        page_header("ตั้งค่าความเป็นส่วนตัว", "ควบคุมการใช้และการแสดงผลข้อมูลส่วนบุคคลของคุณ (PDPA)"),
        card(
            card_title("การใช้ข้อมูล"),
            privacy_item("share_history", "แชร์ประวัติการรักษาให้ทันตแพทย์ทุกท่านในคลินิก",
                         "ช่วยให้ทันตแพทย์ที่ไม่ใช่เจ้าของไข้ดูประวัติและผังฟันของคุณได้", "stethoscope"),
            privacy_item("mask_name", "ซ่อนชื่อจริงบนจอเรียกคิว",
                         "แสดงเฉพาะเลขคิวและชื่อย่อบนหน้าจอในคลินิก", "eye_off"),
            privacy_item("research", "อนุญาตให้ใช้ข้อมูลแบบไม่ระบุตัวตนเพื่อพัฒนาบริการ",
                         "ข้อมูลจะถูกลบชื่อและข้อมูลที่ระบุตัวตนก่อนนำไปใช้", "chart_line"),
        ),
        card(
            card_title("ข้อมูลของฉัน"),
            rx.flex(
                rx.button(rx.icon(tag="download", size=14), "ดาวน์โหลดข้อมูลของฉัน", variant="soft", on_click=AppState.download_my_data),
                rx.alert_dialog.root(
                    rx.alert_dialog.trigger(rx.button(rx.icon(tag="user_x", size=14), "ขอลบบัญชีผู้ใช้", variant="soft", color_scheme="red")),
                    rx.alert_dialog.content(
                        rx.alert_dialog.title("ส่งคำขอลบบัญชี?"),
                        rx.alert_dialog.description(
                            "คลินิกจะติดต่อกลับเพื่อยืนยันตัวตนก่อนลบบัญชี ประวัติการรักษาจะถูกเก็บไว้ตามระยะเวลาที่กฎหมายกำหนด"
                        ),
                        rx.hstack(
                            rx.alert_dialog.cancel(rx.button("ยกเลิก", variant="soft", color_scheme="gray")),
                            rx.alert_dialog.action(rx.button("ส่งคำขอ", color_scheme="red",
                                                             on_click=rx.toast.info("ส่งคำขอลบบัญชีแล้ว คลินิกจะติดต่อกลับ"))),
                            justify="end",
                            spacing="2",
                            margin_top="16px",
                        ),
                    ),
                ),
                gap="8px",
                wrap="wrap",
            ),
        ),
    )
