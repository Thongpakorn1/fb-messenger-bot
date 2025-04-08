# ใช้ Python 3.9-slim เป็นพื้นฐาน
FROM python:3.9-slim

# ติดตั้ง Tesseract OCR, libtesseract-dev, libzbar และ dependencies อื่น ๆ
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libzbar-dev \  # สำคัญ: ติดตั้ง development files สำหรับ zbar
    build-essential \
    pkg-config \    # อาจจำเป็นสำหรับการหา zbar library
    && rm -rf /var/lib/apt/lists/* # ลบ cache หลังติดตั้งเพื่อประหยัดพื้นที่

# กำหนดไดเรกทอรีทำงานภายใน container
WORKDIR /app

# คัดลอกไฟล์ requirements.txt ไปยัง container ก่อน
COPY requirements.txt /app/requirements.txt

# ติดตั้ง dependencies ของโปรเจกต์จาก requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกไฟล์จากเครื่อง host ไปยัง container
COPY . /app

# คำสั่งที่รันเมื่อ container เริ่มทำงาน
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]  # ใช้ gunicorn แทนการใช้ flask development server
