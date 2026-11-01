import datetime as dt
from sqlmodel import Session, create_engine, select
from passlib.context import CryptContext
from rxconfig import config

# นำเข้า Models ของระบบ
from dental_clinic_system.backend.models import User, Patient, get_utc_now

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def seed():
    engine = create_engine(config.db_url)
    with Session(engine) as session:
        # รายการบัญชีผู้ใช้เริ่มต้นทั้งหมด
        users_data = [
            # ทันตแพทย์ (Dentists)
            {
                "username": "dentist@dental.com",
                "password": "dentist1111",
                "full_name": "ทพ. สมศักดิ์ รักฟัน",
                "role": "dentist",
            },
            {
                "username": "dentist2@dental.com",
                "password": "dentist2222",
                "full_name": "ทพญ. พิมพา ยิ้มสวย",
                "role": "dentist",
            },
            {
                "username": "dentist3@dental.com",
                "password": "dentist3333",
                "full_name": "ทพ. ชาญชัย สุขภาพดี",
                "role": "dentist",
            },
            {
                "username": "dentist4@dental.com",
                "password": "dentist4444",
                "full_name": "ทพญ. ณิชา อารมณ์ดี",
                "role": "dentist",
            },
            # เจ้าหน้าที่ (Staff)
            {
                "username": "staff@dental.com",
                "password": "staff1234",
                "full_name": "เจ้าหน้าที่คลินิก (Staff)",
                "role": "staff",
            },
            # ผู้ป่วย (Patient)
            {
                "username": "T0ng.FAh@gmail.com",
                "password": "J@m_s@i2607",
                "full_name": "ท้องฟ้า แจ่มใส",
                "role": "patient",
                "hn_code": "P-0001",
                "phone": "0974463582",
                "dob": dt.date(1998, 5, 15),
                "gender": "หญิง",
                "national_id": "1100200300401",
                "address": "กรุงเทพมหานคร",
            },
        ]

        print("--- เริ่มต้นบันทึกข้อมูลผู้ใช้งานลง Neon Cloud ---")
        for u in users_data:
            existing = session.exec(select(User).where(User.username == u["username"])).first()
            if not existing:
                new_user = User(
                    username=u["username"],
                    password_hash=hash_password(u["password"]),
                    full_name=u["full_name"],
                    role=u["role"],
                    is_active=True,
                    created_at=get_utc_now(),
                )
                session.add(new_user)
                session.commit()
                session.refresh(new_user)
                print(f"[+] สร้างบัญชีสำเร็จ: {u['username']} (Role: {u['role']})")

                # ถ้าเป็นบทบาทคนไข้ ให้เปิดเวชระเบียนใน Patient ด้วย
                if u["role"] == "patient":
                    new_patient = Patient(
                        user_id=new_user.id,
                        hn_code=u.get("hn_code", "P-0001"),
                        national_id=u.get("national_id", "-"),
                        first_name=u["full_name"].split()[0],
                        last_name=u["full_name"].split()[1] if len(u["full_name"].split()) > 1 else "",
                        email=u["username"],
                        birth_date=u.get("dob"),
                        gender=u.get("gender", "ไม่ระบุ"),
                        phone_number=u.get("phone", "-"),
                        address=u.get("address", "-"),
                        underlying_disease="ไม่มี",
                        drug_allergy="ไม่มี",
                        created_at=get_utc_now(),
                    )
                    session.add(new_patient)
                    session.commit()
                    print(f"[+] บันทึกเวชระเบียน: {u['full_name']} (HN: {new_patient.hn_code})")
            else:
                # อัปเดตรหัสผ่านใหม่กรณีมีบัญชีเดิมอยู่แล้ว
                existing.password_hash = hash_password(u["password"])
                existing.full_name = u["full_name"]
                session.add(existing)
                session.commit()
                print(f"[*] อัปเดตข้อมูลและรหัสผ่าน: {u['username']}")

        print("--- บันทึกข้อมูลทั้งหมดสำเร็จเรียบร้อยแล้ว ---")

if __name__ == "__main__":
    seed()