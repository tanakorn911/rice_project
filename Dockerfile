FROM python:3.10-slim-bullseye

RUN apt-get update && apt-get install -y --fix-missing \
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
# COPY gee-key.json /app/backend/gee-key.json
CMD ["gunicorn", "rice_core.wsgi:application", "--bind", "0.0.0.0:8000"]

WORKDIR /app/backend
