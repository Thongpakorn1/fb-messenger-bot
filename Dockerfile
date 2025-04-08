# ใช้ Python 3.9-slim เป็นพื้นฐาน
FROM python:3.9-slim

# ติดตั้ง Tesseract OCR, libtesseract-dev, libzbar และ dependencies อื่น ๆ
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libzbar0 \      # กลับมาใช้ libzbar0 สำหรับ shared library
    libzbar-dev \  # ยังคง libzbar-dev ไว้สำหรับการ build pyzbar
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# กำหนดไดเรกทอรีทำงานภายใน container
WORKDIR /app

# คัดลอกไฟล์ requirements.txt ไปยัง container ก่อน
COPY requirements.txt /app/requirements.txt

# ติดตั้ง dependencies ของโปรเจกต์จาก requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกไฟล์จากเครื่อง host ไปยัง container
COPY . /app

# ตั้งค่า LD_LIBRARY_PATH เพื่อให้ระบบค้นหา shared library ของ zbar ได้
ENV LD_LIBRARY_PATH=/usr/local/lib:/usr/lib:/usr/lib/x86_64-linux-gnu

# คำสั่งที่รันเมื่อ container เริ่มทำงาน
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]
