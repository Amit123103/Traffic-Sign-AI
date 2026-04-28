import os
import uuid
import time
import cv2
import threading
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from flask import Flask, render_template, request, jsonify, Response, send_file, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import func
import csv
import io

import config
from utils.database import db, init_db, Detection, SystemLog, add_detection, add_log
from utils.voice import speak_sign
from detect import predict_sign, detect_from_file, detect_from_frame, detect_from_video, load_traffic_model
from classes import CLASSES

app = Flask(__name__)
app.config.from_object(config)

# Initialize Database
init_db(app)

# Global variables for video processing progress
video_tasks = {}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           os.path.splitext(filename)[1].lower() in allowed_extensions

# --- Routes ---

@app.route('/')
def index():
    # Fetch stats for home page
    total_detections = db.session.query(func.count(Detection.id)).scalar() or 0
    today = datetime.utcnow().date()
    today_detections = db.session.query(func.count(Detection.id)).filter(func.date(Detection.timestamp) == today).scalar() or 0
    
    most_common = db.session.query(Detection.class_name, func.count(Detection.class_name).label('count')) \
        .group_by(Detection.class_name).order_by(db.desc('count')).first()
    
    recent_detections = Detection.query.order_by(Detection.timestamp.desc()).limit(5).all()
    
    stats = {
        "total": total_detections,
        "today": today_detections,
        "most_common": most_common[0] if most_common else "N/A",
        "recent": [d.to_dict() for d in recent_detections]
    }
    return render_template('index.html', stats=stats)

@app.route('/detect')
def detect_page():
    return render_template('detect.html')

@app.route('/video')
def video_page():
    return render_template('video.html')

@app.route('/webcam')
def webcam_page():
    return render_template('webcam.html')

@app.route('/analytics')
def analytics_page():
    return render_template('analytics.html')

@app.route('/admin')
def admin_page():
    return render_template('admin.html')

# --- API Endpoints ---

@app.route('/api/detect/image', methods=['POST'])
def api_detect_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400
    
    if file and allowed_file(file.filename, config.ALLOWED_IMAGE_EXTENSIONS):
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        filepath = config.UPLOADS_DIR / filename
        file.save(str(filepath))
        
        # Run detection
        prediction, annotated_url = detect_from_file(filepath)
        
        if prediction:
            # Save to DB
            add_detection(
                source='image',
                class_id=prediction['class_id'],
                class_name=prediction['class_name'],
                confidence=prediction['confidence'],
                image_path=annotated_url,
                processing_time_ms=prediction['processing_time_ms']
            )
            return jsonify({
                "success": True,
                "prediction": prediction,
                "annotated_url": annotated_url
            })
        else:
            return jsonify({
                "success": False, 
                "error": "Detection engine unavailable. Please ensure the model is trained and placed in the /models directory."
            }), 503
            
    return jsonify({"error": "File type not allowed"}), 400

@app.route('/api/detect/video', methods=['POST'])
def api_detect_video():
    file = request.files['video']
    if file and allowed_file(file.filename, config.ALLOWED_VIDEO_EXTENSIONS):
        # Check if model exists
        from detect import load_traffic_model
        if load_traffic_model() is None:
            return jsonify({
                "success": False, 
                "error": "Detection engine unavailable. Please ensure the model is trained."
            }), 503

        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        filepath = config.UPLOADS_DIR / filename
        file.save(str(filepath))
        
        task_id = str(uuid.uuid4())
        output_filename = f"proc_{filename}"
        
        # Start background processing
        def process_video_task(tid, path, out_name):
            video_tasks[tid] = {"status": "processing", "progress": 0}
            result = detect_from_video(path, out_name)
            video_tasks[tid] = {"status": "completed", "result": result}
            add_log("INFO", f"Video processing completed: {out_name}", "/api/detect/video")

        thread = threading.Thread(target=process_video_task, args=(task_id, filepath, output_filename))
        thread.start()
        
        return jsonify({"success": True, "task_id": task_id})
    
    return jsonify({"error": "Invalid video file"}), 400

@app.route('/api/video/status/<task_id>')
def video_status(task_id):
    status = video_tasks.get(task_id, {"status": "not_found"})
    return jsonify(status)

def generate_webcam_stream():
    cap = cv2.VideoCapture(0)
    while True:
        success, frame = cap.read()
        if not success:
            break
        
        # Night mode detection from session/request if needed (simplified here)
        prediction, annotated_frame = detect_from_frame(frame)
        
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    cap.release()

@app.route('/api/webcam/stream')
def api_webcam_stream():
    return Response(generate_webcam_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/webcam/capture', methods=['POST'])
def api_webcam_capture():
    data = request.json
    # In a real app, you'd capture the frame from the stream and save it
    # Here we simulate or accept a base64 from client
    # For simplicity, we assume detection was already displayed
    if data:
        add_detection(
            source='webcam',
            class_id=data['class_id'],
            class_name=data['class_name'],
            confidence=data['confidence'],
            processing_time_ms=data.get('processing_time_ms', 0)
        )
        return jsonify({"success": True})
    return jsonify({"error": "No data"}), 400

@app.route('/api/analytics/data')
def api_analytics_data():
    # Stats by class
    by_class = db.session.query(Detection.class_name, func.count(Detection.id)) \
        .group_by(Detection.class_name).all()
    
    # Daily detections (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily = db.session.query(func.date(Detection.timestamp).label('date'), func.count(Detection.id)) \
        .filter(Detection.timestamp >= thirty_days_ago) \
        .group_by(func.date(Detection.timestamp)).all()
    
    return jsonify({
        "by_class": {name: count for name, count in by_class},
        "daily": {str(date): count for date, count in daily},
        "total": db.session.query(func.count(Detection.id)).scalar()
    })

@app.route('/api/admin/logs')
def api_admin_logs():
    page = request.args.get('page', 1, type=int)
    logs = SystemLog.query.order_by(SystemLog.timestamp.desc()).paginate(page=page, per_page=20)
    return jsonify({
        "logs": [{"level": l.level, "message": l.message, "timestamp": l.timestamp.isoformat(), "route": l.route} for l in logs.items],
        "has_next": logs.has_next,
        "total": logs.total
    })

@app.route('/api/admin/export/csv')
def api_admin_export():
    detections = Detection.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Timestamp', 'Source', 'Class ID', 'Class Name', 'Confidence', 'Processing Time (ms)'])
    for d in detections:
        writer.writerow([d.id, d.timestamp, d.source, d.class_id, d.class_name, d.confidence, d.processing_time_ms])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='traffic_detections_history.csv'
    )

@app.route('/api/admin/history', methods=['DELETE'])
def api_clear_history():
    Detection.query.delete()
    db.session.commit()
    add_log("WARNING", "Detection history cleared by admin", "/api/admin/history")
    return jsonify({"success": True})

@app.route('/api/voice/speak', methods=['POST'])
def api_voice_speak():
    data = request.json
    class_id = data.get('class_id')
    lang = data.get('lang', 'en')
    
    if class_id is not None and int(class_id) in CLASSES:
        audio_url = speak_sign(CLASSES[int(class_id)], lang=lang)
        return jsonify({"success": True, "audio_url": audio_url})
    
    return jsonify({"error": "Invalid class ID"}), 400

@app.route('/api/health')
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

if __name__ == '__main__':
    # Force model load on startup
    load_traffic_model()
    app.run(host='0.0.0.0', port=5000)
