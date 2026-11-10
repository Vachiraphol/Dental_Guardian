งาน frontend: ระบบนำเข้าไฟล์เข้าผังฟันของหมอ (หน้า /records)
ทำจาก branch develop ที่ commit 48b02e5


วิธีใช้
1. ไปที่ branch develop แล้ว git pull
2. รัน git log -1 --oneline
   - ถ้าขึ้นต้นด้วย 48b02e5 ให้ทำข้อ 3 ต่อ
   - ถ้าเป็นเลขอื่น แปลว่ามีงานใหม่เข้ามาแล้ว ห้ามคัดลอกทับ ให้ทำตามหัวข้อ "กรณี develop เปลี่ยนแล้ว"
3. คัดลอกทุกอย่างที่อยู่ข้างในโฟลเดอร์ copy-into-repo ไปวางที่โฟลเดอร์หลักของ repo แล้วเลือกแทนที่ไฟล์เดิม
4. รัน git status ต้องเห็นไฟล์ที่เปลี่ยน 5 ไฟล์ตามรายการด้านล่าง แล้วค่อย commit


กรณี develop เปลี่ยนแล้ว
การคัดลอกทับจะลบงานใหม่ของคนอื่น ให้ใช้ไฟล์ patch แทน
1. คัดลอก dental-chart-import-frontend.patch ไปไว้ในโฟลเดอร์หลักของ repo
2. รัน git apply --3way --ignore-whitespace dental-chart-import-frontend.patch
3. ลบไฟล์ .patch ออกจากโฟลเดอร์ แล้วค่อย commit


ไฟล์ที่เปลี่ยน 5 ไฟล์
- BACKEND_HANDOFF.md
- dental_clinic_system/pages/records.py
- dental_clinic_system/state.py
- reflex.lock/bun.lock
- reflex.lock/package.json


งานที่ฝั่ง backend ต้องทำต่อ
มี 2 จุดใน state.py คือ handle_chart_import และ confirm_chart_import
ทั้งสองจุดมีคอมเมนต์ TODO(backend) และรายละเอียดอยู่ใน BACKEND_HANDOFF.md
ตอนนี้อัปโหลดไฟล์แล้วจะขึ้นว่ารอเชื่อมต่อ backend และยังไม่บันทึกข้อมูล
