import reflex as rx
import bcrypt
from dental_clinic_system.models import User, UserProfile

class AuthState(rx.State):
    email: str = ""
    password: str = ""
    role: str = "patient"
    error_message: str = ""

    def set_email(self, email: str):
        self.email = email

    def set_password(self, password: str):
        self.password = password

    def set_role(self, role: str):
        self.role = role

    # จัดการสถานะการเข้าสู่ระบบด้วย Cookie
    current_user_id: str = rx.Cookie("", name="user_id")
    current_role: str = rx.Cookie("", name="role")

    @rx.var
    def is_logged_in(self) -> bool:
        return self.current_user_id != ""

    def register(self):
        self.error_message = ""
        # 1. ตรวจสอบข้อมูลที่ผู้ใช้กรอก (Validation)
        if not self.email or not self.password:
            self.error_message = "กรุณากรอกข้อมูลให้ครบถ้วน"
            return
        if len(self.password) < 6:
            self.error_message = "รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร"
            return

        with rx.session() as session:
            # ตรวจสอบอีเมลซ้ำ
            if session.query(User).filter(User.email == self.email).first():
                self.error_message = "อีเมลนี้มีในระบบแล้ว"
                return

            # 2. จัดการรหัสผ่านอย่างปลอดภัย (Hashing)
            hashed_pw = bcrypt.hashpw(self.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            new_user = User(email=self.email, password_hash=hashed_pw, role=self.role)
            session.add(new_user)
            session.commit()
            session.refresh(new_user)

            # 4. สร้าง Profile เปล่าเชื่อมโยงกับบัญชีผู้ใช้
            new_profile = UserProfile(user_id=new_user.id)
            session.add(new_profile)
            session.commit()

            return rx.window_alert("สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบ")

    def login(self):
        self.error_message = ""
        with rx.session() as session:
            user = session.query(User).filter(User.email == self.email).first()
            # 2. ตรวจสอบตัวตนผู้ใช้
            if user and bcrypt.checkpw(self.password.encode('utf-8'), user.password_hash.encode('utf-8')):
                self.current_user_id = str(user.id)
                self.current_role = user.role
                self.email = ""
                self.password = ""
                return rx.window_alert("เข้าสู่ระบบสำเร็จ")
            
            self.error_message = "อีเมลหรือรหัสผ่านไม่ถูกต้อง"

    def logout(self):
        self.current_user_id = ""
        self.current_role = ""
        return rx.window_alert("ออกจากระบบเรียบร้อยแล้ว")
        
class ProtectedState(AuthState):
    # ป้องกันไม่ให้คนที่ไม่ได้ล็อกอินเข้าถึงข้อมูล
    def check_login(self):
        if not self.is_logged_in:
            return rx.redirect("/") # เด้งกลับไปหน้าแรกหรือหน้า Login

    # ตรวจสอบสิทธิ์ฝั่งพนักงาน (หมอและพยาบาลเท่านั้น)
    def check_is_staff(self):
        self.check_login()
        if self.current_role not in ["dentist", "nurse"]:
            return rx.window_alert("คุณไม่มีสิทธิ์เข้าถึงส่วนนี้") # หรือสั่ง Redirect
          
class ProfileState(ProtectedState):
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    medical_conditions: str = ""

    # โหลดข้อมูลส่วนตัวมาแสดงผล
    def load_profile(self):
        if not self.is_logged_in:
            return
        
        with rx.session() as session:
            profile = session.query(UserProfile).filter(UserProfile.user_id == int(self.current_user_id)).first()
            if profile:
                self.first_name = profile.first_name
                self.last_name = profile.last_name
                self.phone = profile.phone
                self.medical_conditions = profile.medical_conditions

    # บันทึกการแก้ไขข้อมูล
    def save_profile(self):
        with rx.session() as session:
            profile = session.query(UserProfile).filter(UserProfile.user_id == int(self.current_user_id)).first()
            if profile:
                profile.first_name = self.first_name
                profile.last_name = self.last_name
                profile.phone = self.phone
                profile.medical_conditions = self.medical_conditions
                
                session.commit()
                return rx.window_alert("อัปเดตข้อมูลส่วนตัวสำเร็จ")