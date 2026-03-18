FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    libtesseract-dev \
    libleptonica-dev \
    pkg-config \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 5000

#CMD ["gunicorn" , "--workers", "3", "--timeout", "300", "--bind", "0.0.0.0:5000","--access-logfile", "-", "--error-logfile", "-", "--log-level", "debug","app:app"]
CMD ["python", "main.py"]