FROM python:3.11-slim

WORKDIR /app

# Install FFmpeg and other dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install spotdl and other Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .
COPY Procfile .

CMD ["python", "bot.py"]
