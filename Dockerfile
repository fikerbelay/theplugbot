FROM python:3.11-slim

WORKDIR /app

# Install FFmpeg and other dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files from the repository
COPY . .

# Create downloads directory
RUN mkdir -p downloads

CMD ["python", "bot.py"]
