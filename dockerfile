FROM python3.12-slim

WORKDIR /app

RUN apt-get uptade && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-fra \
    libtesseract-dev \
    libleptonica-dev \
    pkg-config \
    build-essential \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 5000

CMD ["gunicorn" , "--workers", "10", "--bind", "0.0.0.0:5000","app:app"]