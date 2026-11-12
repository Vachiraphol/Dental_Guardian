FROM python:3.11-slim

WORKDIR /app

# 1. ติดตั้ง System Dependencies แบบ Non-interactive
RUN DEBIAN_FRONTEND=noninteractive apt-get update -qq && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
    curl \
    unzip \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ปิด Error ของ lscpu ใน Docker Build ของ Render
RUN printf '#!/bin/sh\necho "CPU(s): 1"\n' > /usr/local/bin/lscpu && chmod +x /usr/local/bin/lscpu

# 2. ตั้งค่า Virtual Environment และปิดแจ้งเตือนอัปเดตเวอร์ชันของ Reflex
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV REFLEX_CHECK_LATEST_VERSION=false

# 3. ติดตั้ง Python dependencies และ uvicorn สำหรับรัน ASGI บน Render
COPY requirements.txt .
RUN pip install --quiet --no-cache-dir --upgrade pip && \
    pip install --quiet --no-cache-dir -r requirements.txt uvicorn

# 4. คัดลอกโปรเจกต์ทั้งหมด
COPY . .

# 5. สั่ง Build Production ล่วงหน้าในขั้นตอน Image Build
RUN reflex init
RUN reflex export --no-zip

# กำหนดพอร์ตสำหรับ Render
ENV PORT=10000
EXPOSE ${PORT}

# 6. รัน Backend ผ่าน python -m uvicorn บน 0.0.0.0:$PORT เพื่อให้ Render จับพอร์ตได้ทันที
CMD ["sh", "-c", "python -m uvicorn dental_clinic_system.dental_clinic_system:app --host 0.0.0.0 --port ${PORT:-10000}"]