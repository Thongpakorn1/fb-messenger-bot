# ใช้ Python 3.9-slim เป็นพื้นฐาน
FROM python:3.9-slim

# ติดตั้ง Tesseract OCR, libtesseract-dev, libzbar และ dependencies อื่น ๆ
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libzbar0 \
    libzbar-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# ค้นหาตำแหน่ง libzbar.so (เพื่อ debug)
RUN find / -name libzbar.so

# กำหนดไดเรกทอรีทำงานภายใน container
WORKDIR /app

# คัดลอกไฟล์ requirements.txt ไปยัง container ก่อน
COPY requirements.txt /app/requirements.txt

# ติดตั้ง dependencies ของโปรเจกต์จาก requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกไฟล์จากเครื่อง host ไปยัง container
COPY . /app

# Copy shared library (อาจต้องปรับ path ตามผลลัพธ์ของ find)
RUN cp /usr/lib/x86_64-linux-gnu/libzbar.so.0 /usr/lib/libzbar.so.0
RUN ldconfig # อัปเดต shared library cache

# คำสั่งที่รันเมื่อ container เริ่มทำงาน
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]
