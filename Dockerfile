FROM python:3.11-slim

WORKDIR /app

# 1. ติดตั้ง System Dependencies ที่จำเป็น
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. ตั้งค่า Virtual Environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# 3. ติดตั้ง Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. คัดลอกโปรเจกต์ทั้งหมด
COPY . .

# 5. สั่ง Build Production ล่วงหน้าในขั้นตอน Image Build
RUN reflex init
RUN reflex export --no-zip

# กำหนดพอร์ตสำหรับ Render (ค่าเริ่มต้น 10000)
ENV PORT=10000
EXPOSE ${PORT}

# 6. รัน Backend ที่ทำหน้าที่ Serve Static Frontend ในตัว
CMD ["sh", "-c", "reflex run --env prod --backend-only --backend-host 0.0.0.0 --backend-port $PORT"]