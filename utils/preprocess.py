import cv2
import numpy as np

def grayscale(img):
    """Convert image to grayscale."""
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

def equalize(img):
    """Histogram equalization to improve contrast."""
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    return clahe.apply(img)

def normalize(img):
    """Normalize pixel values to [0, 1]."""
    return img / 255.0

def preprocess_image(img, target_size=(64, 64)):
    """Full preprocessing pipeline for traffic signs."""
    # Resize
    img = cv2.resize(img, target_size)
    # Convert to grayscale (optional, but good for many traffic sign models)
    # Most pre-trained MobileNet expect 3 channels, so we stick to 3 channels but enhance them
    
    # Enhance contrast using CLAHE on the L channel of LAB color space
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    final_img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    
    # Normalize
    final_img = final_img.astype(np.float32) / 255.0
    
    return final_img

def night_mode_enhance(frame):
    """Enhance low-light frames for better detection."""
    # Gamma correction
    gamma = 1.5
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    enhanced = cv2.LUT(frame, table)
    
    # CLAHE on enhanced image
    lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
