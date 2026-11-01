FROM python:3.11-slim

WORKDIR /app

# 1. ติดตั้ง System Dependencies และ Nginx
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    git \
    libpq-dev \
    nginx \
    util-linux \
    && rm -rf /var/lib/apt/lists/*

# 2. ตั้งค่า Virtual Environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# 3. ติดตั้ง Python Packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. คัดลอกซอร์สโค้ด
COPY . .

# 5. Build หน้าบ้านล่วงหน้า
RUN reflex init
RUN reflex export --frontend-only --no-zip

# 6. เขียนคอนฟิก Nginx ใหม่ ป้องกัน 500 rewrite loop
RUN echo 'server {\
    listen 10000;\
    server_name _;\
    root /app/.web/_static;\
    index index.html;\
\
    location /_event {\
        proxy_pass http://127.0.0.1:8000;\
        proxy_http_version 1.1;\
        proxy_set_header Upgrade $http_upgrade;\
        proxy_set_header Connection "upgrade";\
        proxy_set_header Host $host;\
    }\
\
    location /ping {\
        proxy_pass http://127.0.0.1:8000;\
    }\
\
    location /api {\
        proxy_pass http://127.0.0.1:8000;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
    }\
\
    location /docs {\
        proxy_pass http://127.0.0.1:8000;\
    }\
\
    location /openapi.json {\
        proxy_pass http://127.0.0.1:8000;\
    }\
\
    location / {\
        try_files $uri $uri/ /index.html =404;\
    }\
}' > /etc/nginx/sites-available/default

ENV PORT=10000
EXPOSE 10000

# 7. เริ่มการทำงาน Nginx และ Reflex Backend
CMD service nginx start && reflex run --env prod --backend-only --backend-host 127.0.0.1 --backend-port 8000