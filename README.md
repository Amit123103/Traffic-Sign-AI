# TrafficSign AI: Cyberpunk Neural Infrastructure 🚦🧠

[![Python](https://img.shields.io/badge/Python-3.11-00FF88?style=flat-square&logo=python)](https://python.org)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.12-FF6F00?style=flat-square&logo=tensorflow)](https://tensorflow.org)
[![Flask](https://img.shields.io/badge/Flask-2.3-white?style=flat-square&logo=flask)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

A complete, production-ready, end-to-end AI-powered Traffic Sign Recognition System (TSRS) utilizing **MobileNetV2** for high-speed, accurate classification. Features a stunning Cyberpunk-industrial dark mode UI, real-time webcam streaming, video analysis, and multi-lingual voice alerts (English & Hindi).

![TSRS Dashboard Placeholder](https://via.placeholder.com/1200x600/0A0A0F/00FF88?text=TrafficSign+AI+Dashboard+Preview)

## 🚀 Key Features

- 🏎️ **Ultra-Fast Inference**: < 50ms per frame detection.
- 📸 **Multi-Source Support**: Images, Video Files, and Live Webcam.
- 🔊 **Voice Synthesis**: Automatic TTS alerts in English and Hindi.
- 📊 **Neural Analytics**: Real-time stats, detection trends, and distribution charts.
- 🌙 **Night Mode**: AI-enhanced visibility for low-light conditions.
- 🛡️ **Admin Core**: Secure panel for history management and system logs.
- 🐳 **Docker Ready**: Full containerization for instant deployment.

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Backend** | Python / Flask / SQLAlchemy |
| **Deep Learning** | TensorFlow / Keras (MobileNetV2) |
| **Computer Vision** | OpenCV / NumPy |
| **Frontend** | Vanilla JS / CSS3 (Industrial Dark Mode) |
| **Database** | SQLite (Default) / PostgreSQL Compatible |
| **Voice** | gTTS / pyttsx3 (Offline Fallback) |

## 📦 Quick Start (PowerShell)

### 1. Environment Setup
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies (with timeout for slow connections)
pip install --default-timeout=1000 -r requirements.txt
```

### 2. Dataset Initialization
```powershell
# Auto-download GTSRB dataset and begin training
python train.py
```

### 3. Launch Neural Grid
```powershell
# Start the web server
python app.py
```
Visit `http://localhost:5000` in your browser.

## 🐳 Docker Deployment

Deploy instantly using Docker Compose:
```bash
docker-compose up --build
```

## 🧠 Model Specifications

- **Architecture**: MobileNetV2 with custom GlobalAveragePooling2D head.
- **Classes**: 43 (GTSRB Standard).
- **Image Size**: 64x64 pixels.
- **Optimization**: Adam optimizer, EarlyStopping, ReduceLROnPlateau.
- **Accuracy Goal**: 95%+ on GTSRB test set.

## 📁 Project Structure

```text
TrafficSignAI/
├── dataset/            # GTSRB Data
├── models/             # Trained .h5 weights
├── static/             # Assets (CSS, JS, Audio)
├── templates/          # Jinja2 HTML Templates
├── utils/              # Preprocessing, DB, Voice logic
├── app.py              # Main Flask Entry
├── train.py            # Training Pipeline
└── detect.py           # Inference Engine
```

## 📡 API Documentation

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/detect/image` | `POST` | Upload image for analysis |
| `/api/detect/video` | `POST` | Start background video processing |
| `/api/webcam/stream` | `GET` | MJPEG real-time detection stream |
| `/api/analytics/data` | `GET` | Fetch system stats JSON |
| `/api/admin/logs` | `GET` | Paginated system logs |

## 📜 License
This project is licensed under the MIT License - see the LICENSE file for details.

---
Built with 💚 for Autonomous Infrastructure.
