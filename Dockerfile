FROM python:3.11-slim

# Install system dependencies for OpenCV and other libs
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --no-warn-script-location -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p models static/uploads static/processed static/audio dataset

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV TF_CPP_MIN_LOG_LEVEL=3
ENV PORT=5000

# Command to run the application (using $PORT for Render)
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 app:app
