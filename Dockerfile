FROM python:3.11-slim

WORKDIR /app

# 1. ติดตั้ง System Dependencies ที่จำเป็น (รวม curl, unzip สำหรับ Node/Bun/Reflex)
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    git \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. ติดตั้ง Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. คัดลอกโปรเจกต์ทั้งหมดเข้า container
COPY . .

# 4. สั่ง init reflex ล่วงหน้าตอน build เพื่อดาวน์โหลด runtime ของ frontend (Node/Bun)
RUN reflex init

# 5. Build frontend asset ล่วงหน้าสำหรับ Production
RUN reflex export --frontend-only --no-zip

# กำหนด Default Port (Render จะ override ค่า PORT ให้อัตโนมัติ)
ENV PORT=10000
EXPOSE ${PORT}

# 6. รันด้วย Production Command ที่รองรับ $PORT ของ Render
CMD ["sh", "-c", "reflex run --env prod --backend-host 0.0.0.0 --backend-port $PORT"]