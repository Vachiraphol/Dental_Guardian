import reflex as rx

# ตารางบัญชีผู้ใช้ (ใช้สำหรับ Login)
class User(rx.Model, table=True):
    email: str
    password_hash: str
    role: str  # 'patient', 'dentist', 'nurse'

# ตารางข้อมูลส่วนตัว (เชื่อมกับ User ด้วย user_id)
class UserProfile(rx.Model, table=True):
    user_id: int
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    medical_conditions: str = "" # โรคประจำตัว