FROM python:3.11-slim

WORKDIR /app

# ติดตั้ง System Dependencies และ Nginx
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    git \
    libpq-dev \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# ติดตั้ง Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกซอร์สโค้ดทั้งหมด
COPY . .

# คอมไพล์หน้าบ้านเป็น Static Files ในช่วง Build (ไม่กิน RAM ช่วง Run)
RUN reflex init
RUN reflex export --frontend-only --no-zip

# สร้างการตั้งค่า Nginx
RUN echo 'server { \
    listen 10000; \
    server_name _; \
    root /app/.web/_static; \
    index index.html; \
    location /_event { \
        proxy_pass http://127.0.0.1:8000; \
        proxy_http_version 1.1; \
        proxy_set_header Upgrade $http_upgrade; \
        proxy_set_header Connection "upgrade"; \
        proxy_set_header Host $host; \
    } \
    location /ping { \
        proxy_pass http://127.0.0.1:8000; \
    } \
    location /api { \
        proxy_pass http://127.0.0.1:8000; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
    } \
    location /docs { \
        proxy_pass http://127.0.0.1:8000; \
    } \
    location /openapi.json { \
        proxy_pass http://127.0.0.1:8000; \
    } \
    location / { \
        try_files $uri $uri.html $uri/ /index.html; \
    } \
}' > /etc/nginx/sites-available/default

ENV PORT=10000
EXPOSE 10000

# สั่งเริ่ม Nginx บนพอร์ต 10000 ควบคู่กับ Backend บนพอร์ต 8000
CMD service nginx start && reflex run --env prod --backend-only --backend-host 127.0.0.1 --backend-port 8000