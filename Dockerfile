FROM python:3.11-slim

WORKDIR /app

# ติดตั้ง system dependencies ที่จำเป็นสำหรับ build และ runtime
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ติดตั้ง python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกโปรเจกต์
COPY . .

# สั่ง init และ export frontend แบบ static ล่วงหน้า (ใช้ memory ตอน build ไม่กระทบ runtime)
RUN reflex init
RUN reflex export --frontend-only --no-zip

# กำหนดพอร์ตเริ่มต้นที่ Render กำหนด
ENV PORT=10000
EXPOSE ${PORT}

# รัน backend ตัวเดียวที่ serve static files บน Render port
CMD ["sh", "-c", "reflex run --env prod --backend-only --backend-host 0.0.0.0 --backend-port $PORT"]