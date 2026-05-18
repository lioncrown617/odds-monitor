FROM python:3.11-slim
RUN apt-get update && apt-get install -y \
    chromium-driver chromium \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "odd8.py"]
