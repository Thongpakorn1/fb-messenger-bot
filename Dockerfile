# ใช้ Python 3.9-slim เป็นพื้นฐาน
FROM python:3.9-slim

# อัปเดตและติดตั้ง Tesseract OCR และ libtesseract-dev (ใช้ในการประมวลผล OCR)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libzbar0 \
    && rm -rf /var/lib/apt/lists/*  # ลบ cache หลังติดตั้งเพื่อประหยัดพื้นที่

# กำหนดไดเรกทอรีทำงานภายใน container
WORKDIR /app

# คัดลอกไฟล์จากเครื่อง host ไปยัง container
COPY . /app

# คัดลอกไฟล์ requirements.txt ไปยัง container
COPY requirements.txt /app/requirements.txt

# ตรวจสอบว่า pip สามารถทำงานได้หรือไม่
RUN pip --version
RUN pip install --upgrade pip  # อัปเกรด pip ถ้าจำเป็น

# ติดตั้ง dependencies ของโปรเจกต์จาก requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# คำสั่งที่รันเมื่อ container เริ่มทำงาน
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]  # ใช้ gunicorn แทนการใช้ flask development server
