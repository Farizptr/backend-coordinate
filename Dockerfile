# syntax=docker/dockerfile:1

FROM python:3.12-slim

# System deps (minimal)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    libgl1 \
    libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer cache)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Default environment (can be overridden at run-time)
ENV HOST=0.0.0.0 \
    PORT=5050 \
    RELOAD=false \
    LOG_LEVEL=info \
    MODEL_PATH=/app/best.pt

EXPOSE 5050

# Default command: start API server
CMD ["python", "run_server.py"]


