FROM python:3.10-slim-bullseye

# ติดตั้ง System Dependencies สำหรับ GIS (GDAL, PROJ, GEOS)
RUN apt-get update && apt-get install -y \
    binutils \
    libproj-dev \
    gdal-bin \
    libgdal-dev \
    python3-gdal \
    && apt-get clean

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY ./backend /app/backend
# Copy Key file เข้าไปใน Container
COPY gee-key.json /app/backend/gee-key.json

WORKDIR /app/backend