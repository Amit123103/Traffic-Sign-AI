import os
from pathlib import Path

# Base Directories
BASE_DIR = Path(__file__).parent
MODEL_DIR = BASE_DIR / "models"
DATASET_DIR = BASE_DIR / "dataset"
STATIC_DIR = BASE_DIR / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"
PROCESSED_DIR = STATIC_DIR / "processed"
AUDIO_DIR = STATIC_DIR / "audio"

# Create directories if they don't exist
for folder in [MODEL_DIR, DATASET_DIR, UPLOADS_DIR, PROCESSED_DIR, AUDIO_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# File Paths
MODEL_PATH = MODEL_DIR / "traffic_sign_model.h5"
SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/traffic_signs.db")

# ML Configuration
IMAGE_SIZE = (64, 64)
BATCH_SIZE = 32
EPOCHS = 50
CONFIDENCE_THRESHOLD = 0.60

# Flask Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "tsrs-dev-key-cyberpunk-2024")
DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
MAX_UPLOAD_SIZE_MB = 16

# Supported Extensions
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv'}

# Streaming Configuration
WEBCAM_FPS_TARGET = 20
MJPEG_QUALITY = 80
