# ใช้ Python image เป็นพื้นฐาน
FROM python:3.9-slim

# อัปเดตและติดตั้ง Tesseract OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# ติดตั้ง dependencies ของโปรเจกต์
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# รันโปรแกรมเมื่อคอนเทนเนอร์เริ่มทำงาน
CMD ["python", "app.py"]
