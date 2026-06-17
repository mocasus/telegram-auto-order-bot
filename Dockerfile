# ============================================================
# Telegram Auto Order Bot — Dockerfile
# ============================================================
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Buat user non-root
RUN groupadd -r bot && useradd -r -g bot bot

# Install dependencies sistem
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements dan install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Buat direktori data
RUN mkdir -p /app/data && chown -R bot:bot /app

# Switch ke user non-root
USER bot

# Expose port untuk webhook (opsional)
EXPOSE 8443

# Jalankan bot
CMD ["python3", "bot.py"]
