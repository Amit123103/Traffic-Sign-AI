import cv2
import numpy as np
import tensorflow as tf
from pathlib import Path
import time
from config import MODEL_PATH, IMAGE_SIZE, CONFIDENCE_THRESHOLD, PROCESSED_DIR
from classes import CLASSES
from utils.preprocess import preprocess_image, night_mode_enhance

# Global model cache
_MODEL = None

def load_traffic_model():
    """Load the trained model with caching."""
    global _MODEL
    if _MODEL is None:
        if not MODEL_PATH.exists():
            print(f"Warning: Model not found at {MODEL_PATH}. Prediction will fail.")
            return None
        _MODEL = tf.keras.models.load_model(str(MODEL_PATH))
        print("Model loaded successfully.")
    return _MODEL

def predict_sign(image):
    """
    Predict traffic sign from a single image (Bayer/RGB array).
    Returns a dictionary with prediction details.
    """
    model = load_traffic_model()
    if model is None:
        return None

    # Preprocess
    processed = preprocess_image(image, target_size=IMAGE_SIZE)
    # Add batch dimension
    processed = np.expand_dims(processed, axis=0)

    # Predict
    start_time = time.time()
    predictions = model.predict(processed, verbose=0)
    end_time = time.time()

    class_id = np.argmax(predictions[0])
    confidence = float(predictions[0][class_id])
    processing_time = (end_time - start_time) * 1000

    if confidence < CONFIDENCE_THRESHOLD:
        return {
            "class_id": -1,
            "class_name": "Unknown",
            "confidence": confidence,
            "processing_time_ms": processing_time
        }

    class_info = CLASSES[class_id]
    return {
        "class_id": int(class_id),
        "class_name": class_info["name"],
        "hindi_name": class_info["hindi"],
        "confidence": confidence,
        "category": class_info["category"],
        "description": class_info["description"],
        "color": class_info["color"],
        "processing_time_ms": processing_time
    }

def draw_bounding_box(frame, prediction, box=None):
    """Overlay detection results on the frame."""
    if prediction is None or prediction.get("class_id") == -1:
        return frame

    h, w, _ = frame.shape
    # If no box provided, we assume full frame detection (centered)
    if box is None:
        # Drawing a symbolic box for UI purposes if needed
        box = (int(w*0.1), int(h*0.1), int(w*0.9), int(h*0.9))

    x1, y1, x2, y2 = box
    color = tuple(int(prediction['color'].lstrip('#')[i:i+2], 16) for i in (4, 2, 0)) # Hex to BGR
    
    # Draw Rectangle
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
    
    # Label Background
    label = f"{prediction['class_name']} ({prediction['confidence']*100:.1f}%)"
    (l_w, l_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
    cv2.rectangle(frame, (x1, y1 - l_h - 10), (x1 + l_w, y1), color, -1)
    
    # Text
    cv2.putText(frame, label, (x1, y1 - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    return frame

def detect_from_file(image_path):
    """Full pipeline for a single image file."""
    img = cv2.imread(str(image_path))
    if img is None:
        return None, None
    
    prediction = predict_sign(img)
    annotated_img = draw_bounding_box(img.copy(), prediction)
    
    # Save annotated image
    output_filename = f"detected_{Path(image_path).name}"
    output_path = PROCESSED_DIR / output_filename
    cv2.imwrite(str(output_path), annotated_img)
    
    return prediction, f"/static/processed/{output_filename}"

def detect_from_frame(frame, night_mode=False):
    """Optimized for real-time webcam frames."""
    if night_mode:
        frame = night_mode_enhance(frame)
    
    prediction = predict_sign(frame)
    annotated_frame = draw_bounding_box(frame, prediction)
    
    return prediction, annotated_frame

def detect_from_video(video_path, output_filename):
    """Process video file and save annotated version."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None

    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    output_path = PROCESSED_DIR / output_filename
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    processed_frames = 0
    detections = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        prediction, annotated_frame = detect_from_frame(frame)
        out.write(annotated_frame)
        
        if prediction and prediction['class_id'] != -1:
            detections.append(prediction)
            
        processed_frames += 1
        # In a real app, you might want to send progress updates here via a callback

    cap.release()
    out.release()
    
    return {
        "output_url": f"/static/processed/{output_filename}",
        "total_frames": total_frames,
        "detection_count": len(detections)
    }
