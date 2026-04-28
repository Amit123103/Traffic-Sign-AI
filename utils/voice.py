import os
import hashlib
from gtts import gTTS
import pyttsx3
from pathlib import Path
from config import AUDIO_DIR

# Initialize offline TTS engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)

def get_audio_filename(text, lang):
    """Generate a unique filename based on text and language."""
    hash_object = hashlib.md5(f"{text}_{lang}".encode())
    return f"{hash_object.hexdigest()}.mp3"

def speak_english(text):
    """Generate or retrieve English TTS audio."""
    filename = get_audio_filename(text, 'en')
    filepath = AUDIO_DIR / filename
    
    if filepath.exists():
        return f"/static/audio/{filename}"
    
    try:
        tts = gTTS(text=text, lang='en')
        tts.save(str(filepath))
        return f"/static/audio/{filename}"
    except Exception as e:
        print(f"gTTS English error: {e}. Falling back to offline TTS.")
        # Offline fallback doesn't easily save to MP3 in a cross-platform way 
        # without additional libraries, but we can try:
        try:
            engine.save_to_file(text, str(filepath))
            engine.runAndWait()
            return f"/static/audio/{filename}"
        except:
            return None

def speak_hindi(text):
    """Generate or retrieve Hindi TTS audio."""
    filename = get_audio_filename(text, 'hi')
    filepath = AUDIO_DIR / filename
    
    if filepath.exists():
        return f"/static/audio/{filename}"
    
    try:
        tts = gTTS(text=text, lang='hi')
        tts.save(str(filepath))
        return f"/static/audio/{filename}"
    except Exception as e:
        print(f"gTTS Hindi error: {e}. No offline fallback for Hindi in most pyttsx3 setups.")
        return None

def speak_sign(class_info, lang='en'):
    """Dispatcher for sign name TTS."""
    if lang == 'hi':
        return speak_hindi(class_info['hindi'])
    return speak_english(class_info['name'])
