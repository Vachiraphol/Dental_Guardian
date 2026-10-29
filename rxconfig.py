import reflex as rx

config = rx.Config(
    app_name="dental_clinic_system",
    db_url="sqlite:///reflex.db",
    # Socket Server ต้องรับค่าเป็นเลข IP เท่านั้น (แก้ปัญหา ValueError)
    backend_host="127.0.0.1",
    backend_port=8000,
    # ส่วน URL ที่แอปและหน้าเว็บใช้เชื่อมต่อ ให้ใช้ localhost ตามที่ต้องการ
    api_url="http://localhost:8000",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        rx.plugins.RadixThemesPlugin(
            theme=rx.theme(
                appearance="light",
                has_background=True,
                radius="large",
                accent_color="purple",
                gray_color="slate",
            )
        ),
    ],
)