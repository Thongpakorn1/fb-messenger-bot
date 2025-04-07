# ใช้ Python 3.9-slim เป็นพื้นฐาน
FROM python:3.9-slim

# อัปเดตและติดตั้ง Tesseract OCR, libtesseract-dev, และ libzbar0 (ใช้ในการประมวลผล OCR และ QR Code)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libzbar0 \  # ติดตั้ง libzbar0 สำหรับการอ่าน QR Code
    && rm -rf /var/lib/apt/lists/*  # ลบ cache หลังติดตั้งเพื่อประหยัดพื้นที่

# กำหนดไดเรกทอรีทำงานภายใน container
WORKDIR /app

# คัดลอกไฟล์จากเครื่อง host ไปยัง container
COPY . /app

# ติดตั้ง dependencies ของโปรเจกต์จาก requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# คำสั่งที่รันเมื่อ container เริ่มทำงาน
CMD ["python", "app.py"]
