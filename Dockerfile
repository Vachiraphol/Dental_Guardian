FROM python:3.11-slim

WORKDIR /app

# ติดตั้ง System Dependencies
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ติดตั้ง Python Packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกโปรเจกต์
COPY . .

# Build frontend ล่วงหน้าในขั้นตอน Image build
RUN reflex init
RUN reflex export --frontend-only --no-zip

# กำหนด Port สำหรับ Render
ENV PORT=3001
EXPOSE ${PORT}

# รัน Reflex ในโหมด Production (เสิร์ฟทั้งเว็บหน้าบ้านและ API หลังบ้านที่พอร์ตเดียวกัน)
CMD ["sh", "-c", "reflex run --env prod --backend-host 0.0.0.0 --backend-port $PORT --frontend-port $PORT"]