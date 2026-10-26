# Dental Guardian — ส่งต่อให้ทีม Backend

โค้ดตอนนี้มีแค่ส่วน **frontend** (หน้าเว็บ, ฟอร์ม, การตรวจฟอร์ม, การกรอง/เรียงข้อมูลเพื่อแสดงผล, ผังฟัน)
ไม่มีข้อมูลตัวอย่าง ไม่มีบัญชีผู้ใช้ และไม่มี logic ฝั่งระบบ ทุกจุดที่ต้องเชื่อมต่อมีคอมเมนต์ `TODO(backend)` กำกับ

```bash
grep -rn "TODO(backend)" dental_clinic_system
```

ไฟล์หลักคือ `dental_clinic_system/state.py` (คลาส `AppState`)
ตอนนี้ปุ่มที่ต้องใช้ backend จะขึ้นข้อความ "รอเชื่อมต่อระบบหลังบ้าน (backend)" — เมื่อเชื่อมแล้วให้ลบ `return not_connected(...)` ออก

## 1. ข้อมูลที่หน้าเว็บอ่าน (ให้ backend โหลดใส่ตัวแปรเหล่านี้)

ทุกค่าเป็น `str` วันที่ใช้รูปแบบ `YYYY-MM-DD` และวัน-เวลาใช้ `YYYY-MM-DD HH:MM`
ก่อนใส่ลง state ให้ผ่านฟังก์ชัน `format_*` เพื่อเติมฟิลด์ที่หน้าเว็บใช้แสดงผล

| ตัวแปร | ฟิลด์ที่ backend ต้องส่งมา | ฟังก์ชันจัดรูปแบบ (ฟิลด์ที่เติมให้) |
|---|---|---|
| `patients` | `id, first_name, last_name, gender, dob, national_id, phone, email, address, disease, allergy, registered` | `format_patient` (`full_name, age, dob_th, registered_th`) |
| `dentists` | `id, name, specialty, days` (เลขวัน 1=จันทร์…7=อาทิตย์ คั่นด้วย `,`), `start, end` (`HH:MM`), `lunch` (`HH:MM` หรือว่าง), `leaves` (วันที่คั่นด้วย `,`) | – |
| `appointments` | `id, kind` (`จองคิว` / `นัดครั้งถัดไป`), `patient_id, patient_name, phone, date, time, service, dentist, status, disease, allergy, note, purpose, reason, created` | `format_appointment` (`date_th, weekday`) |
| `entries` (ประวัติการรักษา) | `id, patient_id, tooth` (`"1"`–`"32"`), `icd, procedure, note, dentist, timestamp` | `format_entry` (`icd_th, tooth_label, ts_th`) |
| `available_slots` | `time, left` (จำนวนคิวที่เหลือ), `available` (`"1"` / `"0"`) ของวันที่ `booking_date` | – |

ค่า `status` ของนัดหมายที่หน้าเว็บรองรับ: `รออนุมัติ, ยืนยันแล้ว, มาตามนัด, เลื่อนนัด, ยกเลิกนัด, ปฏิเสธ`

**ผู้ใช้ที่ล็อกอิน:** `user_role` (`""` / `"patient"` / `"staff"`), `user_name`, `user_email`, `current_patient_id`

## 2. จุดที่ต้องเขียน logic (event handlers ใน `AppState`)

| SRS | handler | สิ่งที่ต้องทำ |
|---|---|---|
| 5.1 | `login` | ตรวจอีเมล/รหัสผ่านตาม `login_role` แล้วตั้งค่าผู้ใช้และ redirect |
| 5.1 | `register` | สร้างบัญชีผู้ป่วย (frontend ตรวจรหัสผ่านให้แล้ว) |
| 5.1 | `request_reset`, `confirm_reset` | ส่งรหัส OTP ทางอีเมล / ตรวจ OTP และตั้งรหัสผ่านใหม่ |
| 5.1 | `logout` | ปิด session ฝั่ง server |
| 5.2 | `save_profile`, `change_password`, `toggle_privacy`, `download_my_data` | บันทึกข้อมูลส่วนตัว / รหัสผ่าน / การตั้งค่าความเป็นส่วนตัว / export ข้อมูล |
| 5.3 | `pick_date`, `set_booking_dentist` | โหลดช่วงเวลาว่างใส่ `available_slots` |
| 5.3 | `confirm_booking` | บันทึกการจอง (สถานะ `รออนุมัติ`) แล้วใส่แถวที่บันทึกไว้ใน `booking_slip` |
| 5.3 | `cancel_my_appt` | ผู้ป่วยยกเลิกนัด |
| 5.3 | `approve_request`, `reject_request` | อนุมัติ / ปฏิเสธคำขอจองคิว |
| 5.3 | `mark_arrived`, `cancel_appt`, `reschedule`, `create_next_appt` | มาตามนัด / ยกเลิก / เลื่อนนัด / ออกใบนัดครั้งถัดไป |
| 5.3 | `save_schedule` | บันทึกตารางเวลาทันตแพทย์ (`schedule_dentist`) |
| 5.4 | `save_entry` | บันทึกการรักษา (frontend ตรวจซี่ฟันและ ICD-10 ให้แล้ว) |

## 3. การจำกัดสิทธิ์การเข้าหน้า

ตอนนี้ทุกหน้าเปิดดูได้โดยไม่ต้องล็อกอิน เพื่อให้ตรวจหน้าตาได้
เมื่อระบบล็อกอินใช้งานได้ ให้เปิดการตรวจสิทธิ์ตาม `TODO(backend)` ใน
`components/layout.py` (`member_page`, `staff_page`) และ `pages/booking.py`
