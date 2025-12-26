FROM python:3.12-slim

WORKDIR /app

# Install system dependencies:
# - curl: for healthcheck
# - chromium: for html2image card generation
# - fonts: for proper text rendering in generated images
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    chromium \
    fonts-noto-color-emoji \
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Set Chromium path for html2image
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMIUM_FLAGS="--no-sandbox --disable-gpu --disable-dev-shm-usage"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the bot
CMD ["python", "main.py"]
