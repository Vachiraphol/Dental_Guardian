"""SRS 5.1 หน้ากรอกข้อมูลสมัครสมาชิก."""

from datetime import date
import reflex as rx

from dental_clinic_system.components.auth_card import auth_card, password_input
from dental_clinic_system.components.layout import public_page
from dental_clinic_system.components.ui import error_callout, field
from dental_clinic_system.state import AppState, GENDERS


@rx.page(route="/register", title="สมัครสมาชิก - Dental Guardian")
def register() -> rx.Component:
    today = date.today()
    current_ad_year = today.year
    current_be_year = current_ad_year + 543

    days = [f"{d:02d}" for d in range(1, 32)]
    months = [
        ("01", "มกราคม"),
        ("02", "กุมภาพันธ์"),
        ("03", "มีนาคม"),
        ("04", "เมษายน"),
        ("05", "พฤษภาคม"),
        ("06", "มิถุนายน"),
        ("07", "กรกฎาคม"),
        ("08", "สิงหาคม"),
        ("09", "กันยายน"),
        ("10", "ตุลาคม"),
        ("11", "พฤศจิกายน"),
        ("12", "ธันวาคม"),
    ]
    # ปี พ.ศ. เริ่มจากปีปัจจุบันย้อนหลังไป 120 ปี (ไม่มีปีอนาคตให้เลือกบน iPad/iOS เด็ดขาด)
    years_be = [str(y) for y in range(current_be_year, current_be_year - 120, -1)]

    def section(text: str) -> rx.Component:
        return rx.text(
            text,
            weight="bold",
            size="3",
            color="var(--primary-color)",
            width="100%",
            padding_top="8px",
            border_bottom="1px solid var(--slate-4)",
            padding_bottom="4px",
        )

    grid = lambda *c: rx.grid(*c, columns={"initial": "1", "sm": "2"}, spacing="3", width="100%")
    return public_page(
        # สคริปต์รวมค่า วัน/เดือน/ปี พ.ศ. เป็น YYYY-MM-DD ลงใน input[name="dob"] และกันเลือกเกินวัน/เดือนปัจจุบัน
        rx.script(
            f"""
            (function() {{
                const maxYear = {current_ad_year};
                const maxMonth = {today.month};
                const maxDay = {today.day};

                const syncDob = () => {{
                    const dSel = document.getElementById('dob_day');
                    const mSel = document.getElementById('dob_month');
                    const ySel = document.getElementById('dob_year');
                    const hiddenDob = document.getElementById('dob_hidden');
                    if (!dSel || !mSel || !ySel || !hiddenDob) return;

                    let d = parseInt(dSel.value || '0', 10);
                    let m = parseInt(mSel.value || '0', 10);
                    let yBe = parseInt(ySel.value || '0', 10);
                    let yAd = yBe > 2400 ? yBe - 543 : yBe;

                    // ปรับจำนวนวันสูงสุดตามเดือนและปีอธิกสุรทิน
                    if (m > 0) {{
                        const daysInMonth = new Date(yAd || 2000, m, 0).getDate();
                        if (d > daysInMonth) {{
                            d = daysInMonth;
                            dSel.value = String(d).padStart(2, '0');
                        }}
                    }}

                    // หากเลือกปีปัจจุบัน ห้ามเลือกเดือนหรือวันเกินวันปัจจุบัน
                    if (yAd === maxYear) {{
                        if (m > maxMonth) {{
                            m = maxMonth;
                            mSel.value = String(m).padStart(2, '0');
                        }}
                        if (m === maxMonth && d > maxDay) {{
                            d = maxDay;
                            dSel.value = String(d).padStart(2, '0');
                        }}
                    }}

                    if (d > 0 && m > 0 && yAd > 1900) {{
                        hiddenDob.value = `${{yAd}}-${{String(m).padStart(2, '0')}}-${{String(d).padStart(2, '0')}}`;
                    }} else {{
                        hiddenDob.value = '';
                    }}
                }};

                document.addEventListener('change', (e) => {{
                    if (e.target && ['dob_day', 'dob_month', 'dob_year'].includes(e.target.id)) {{
                        syncDob();
                    }}
                }});
            }})();
            """
        ),
        auth_card(
            "user_plus",
            "สมัครสมาชิก",
            "กรอกข้อมูลส่วนตัวเพื่อสร้างบัญชี ระบบจะสร้างรหัสผู้ป่วยให้อัตโนมัติ",
            rx.form(
                rx.vstack(
                    section("ข้อมูลส่วนตัว"),
                    grid(
                        field("ชื่อ", rx.input(name="first_name", size="3", required=True, autocomplete="off"), True),
                        field("นามสกุล", rx.input(name="last_name", size="3", required=True, autocomplete="off"), True),
                        field("เพศ", rx.select(GENDERS, name="gender", default_value="ไม่ระบุ", size="3", width="100%")),
                        field(
                            "วันเกิด (วัน/เดือน/ปี พ.ศ.)",
                            rx.box(
                                rx.el.input(type="hidden", name="dob", id="dob_hidden", required=True),
                                rx.grid(
                                    rx.el.select(
                                        rx.el.option("วัน", value="", disabled=True, selected=True),
                                        *[rx.el.option(d, value=d) for d in days],
                                        id="dob_day",
                                        required=True,
                                        class_name="dg-dob-select",
                                    ),
                                    rx.el.select(
                                        rx.el.option("เดือน", value="", disabled=True, selected=True),
                                        *[rx.el.option(label, value=val) for val, label in months],
                                        id="dob_month",
                                        required=True,
                                        class_name="dg-dob-select",
                                    ),
                                    rx.el.select(
                                        rx.el.option("ปี พ.ศ.", value="", disabled=True, selected=True),
                                        *[rx.el.option(y, value=y) for y in years_be],
                                        id="dob_year",
                                        required=True,
                                        class_name="dg-dob-select",
                                    ),
                                    columns="3",
                                    spacing="2",
                                    width="100%",
                                ),
                                width="100%",
                            ),
                            True,
                            "เลือก วัน / เดือน / ปี พ.ศ. (จำกัดไม่เกินวัน/เดือน/ปีปัจจุบัน)",
                        ),
                        field(
                            "เลขบัตรประชาชน / Passport",
                            rx.input(
                                name="national_id",
                                size="3",
                                max_length=13,
                                min_length=6,
                                pattern="([0-9]{13}|[A-Za-z0-9]{6,12})",
                                placeholder="เลข 13 หลัก หรือ Passport ต่างชาติ",
                                title="กรอกเลขบัตรประชาชน 13 หลัก หรือเลขที่ Passport 6-12 ตัวอักษร",
                                autocomplete="off",
                                required=True,
                            ),
                            True,
                            "คนไทยกรอกเลข 13 หลัก / ต่างชาติกรอกเลข Passport",
                        ),
                        field(
                            "เบอร์โทรศัพท์",
                            rx.input(
                                name="phone",
                                type="tel",
                                size="3",
                                max_length=10,
                                min_length=10,
                                pattern="0[0-9]{9}",
                                placeholder="08xxxxxxxx (10 หลัก)",
                                autocomplete="off",
                                required=True,
                            ),
                            True,
                        ),
                    ),
                    field("ที่อยู่", rx.text_area(name="address", rows="2", autocomplete="off")),
                    section("ข้อมูลทางการแพทย์"),
                    grid(
                        field("โรคประจำตัว", rx.input(name="disease", size="3", placeholder="ไม่มี / เช่น เบาหวาน", autocomplete="off")),
                        field("ยาที่แพ้", rx.input(name="allergy", size="3", placeholder="ไม่มี / เช่น เพนิซิลลิน", autocomplete="off")),
                    ),
                    section("บัญชีผู้ใช้"),
                    field(
                        "อีเมล (ใช้เข้าสู่ระบบ)",
                        rx.input(
                            name="email",
                            type="email",
                            placeholder="you@example.com",
                            size="3",
                            required=True,
                            autocomplete="off",
                            custom_attrs={"data-lpignore": "true", "data-1p-ignore": "true"},
                        ),
                        True,
                    ),
                    grid(
                        field(
                            "รหัสผ่าน",
                            password_input(
                                "password",
                                "อย่างน้อย 8 ตัว (A-Z, a-z, 0-9)",
                                min_length=8,
                                pattern="(?=.*\\d)(?=.*[a-z])(?=.*[A-Z]).{8,}",
                                required=True,
                            ),
                            True,
                        ),
                        field(
                            "ยืนยันรหัสผ่าน",
                            password_input(
                                "confirm",
                                "กรอกรหัสผ่านอีกครั้ง",
                                min_length=8,
                                required=True,
                            ),
                            True,
                        ),
                    ),
                    rx.hstack(
                        rx.checkbox(name="accept", required=True),
                        rx.text("ยอมรับเงื่อนไขการใช้งานและนโยบายความเป็นส่วนตัว", size="2"),
                        align="center",
                        width="100%",
                    ),
                    error_callout(AppState.register_error),
                    rx.button("สร้างบัญชีผู้ใช้", type="submit", size="3", width="100%", color_scheme="purple", radius="full"),
                    rx.text("มีบัญชีอยู่แล้ว? ", rx.link("เข้าสู่ระบบ", href="/login", weight="bold"), size="2", align="center", width="100%"),
                    width="100%",
                    spacing="3",
                ),
                on_submit=AppState.register,
                autocomplete="off",
                width="100%",
            ),
            max_width="640px",
        ),
    )