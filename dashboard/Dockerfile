FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY templates/ templates/
COPY static/ static/
COPY services/ services/

RUN mkdir -p /app/videos /app/data /app/models

EXPOSE 5000
ENV HOST=0.0.0.0

CMD ["python", "app.py"]
