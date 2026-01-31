FROM python:3.9-slim

WORKDIR /app

# OCR might need additional system libraries (e.g. GL for opencv-headless if used, or tesseract?)
# Assuming standard python dependencies for now, but adding basic libs just in case.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install six && pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
