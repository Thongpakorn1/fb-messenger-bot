# ใช้ Python 3.9-slim เป็นพื้นฐาน
FROM python:3.9-slim

# อัปเดตและติดตั้ง Tesseract OCR และ libtesseract-dev (ใช้ในการประมวลผล OCR)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libzbar0 && rm -rf /var/lib/apt/lists/*

# กำหนดไดเรกทอรีทำงานภายใน container
WORKDIR /app

# คัดลอกไฟล์จากเครื่อง host ไปยัง container
COPY . /app

# คัดลอกไฟล์ requirements.txt ไปยัง container
COPY requirements.txt /app/requirements.txt

# ติดตั้ง dependencies ของโปรเจกต์จาก requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# คำสั่งที่รันเมื่อ container เริ่มทำงาน
CMD ["python", "app.py"]
