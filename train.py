import os
import requests
import zipfile
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau, TensorBoard
from tensorflow.keras.optimizers import Adam

from config import (
    MODEL_PATH, DATASET_DIR, IMAGE_SIZE, BATCH_SIZE, EPOCHS, BASE_DIR
)
from utils.augment import get_train_generator
from utils.visualize import plot_training_history, plot_confusion_matrix, save_classification_report
from classes import CLASSES

def download_gtsrb():
    """Handle dataset acquisition (local archive.zip or download)."""
    dataset_url = "https://sid.erda.dk/public/archives/daaeac0d7ce1151aea9b61d9f1d19370/GTSRB_Final_Training_Images.zip"
    zip_path = DATASET_DIR / "GTSRB_Training.zip"
    archive_path = DATASET_DIR / "archive.zip"
    
    # Check if extraction is already done
    if any(DATASET_DIR.glob('**/[0-9]*')):
        print("Dataset already exists/extracted.")
        return

    # Use local archive.zip if provided by user
    source_zip = None
    if archive_path.exists():
        print(f"Found local dataset: {archive_path}")
        source_zip = archive_path
    elif zip_path.exists() and zip_path.stat().st_size > 1000000:
        source_zip = zip_path
    
    if source_zip:
        print(f"Extracting {source_zip.name}...")
        try:
            with zipfile.ZipFile(source_zip, 'r') as zip_ref:
                zip_ref.extractall(DATASET_DIR)
            print("Extraction complete.")
            return
        except zipfile.BadZipFile:
            print(f"Error: {source_zip.name} is corrupted.")
            if source_zip == archive_path:
                print("Please check your uploaded archive.zip.")
                return
            os.remove(source_zip)

    # If no local zip, download it
    print("Downloading GTSRB dataset... this may take a while.")
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    try:
        response = requests.get(dataset_url, stream=True, timeout=30)
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024*1024):
                if chunk: f.write(chunk)
        print("Download complete. Extracting...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(DATASET_DIR)
        os.remove(zip_path)
    except Exception as e:
        print(f"Acquisition failed: {e}")

def find_train_dir():
    """Locate the directory containing traffic sign class folders (0, 1, 2...)."""
    # Search for a directory that contains a folder named '0' or '00000'
    for path in DATASET_DIR.rglob('*'):
        if path.is_dir() and (path / '0').exists() or (path / '00000').exists():
            return path
    return None

def build_model(num_classes=43):
    """Build MobileNetV2 with custom classification head."""
    base_model = MobileNetV2(
        weights='imagenet', 
        include_top=False, 
        input_shape=(IMAGE_SIZE[0], IMAGE_SIZE[1], 3)
    )
    
    # Freeze first 100 layers as requested
    for layer in base_model.layers[:100]:
        layer.trainable = False
        
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(256, activation='relu')(x)
    x = Dropout(0.4)(x)
    predictions = Dense(num_classes, activation='softmax')(x)
    
    model = Model(inputs=base_model.input, outputs=predictions)
    model.compile(
        optimizer=Adam(learning_rate=0.0001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    return model

def train():
    """Execute the full training pipeline."""
    # 1. Setup
    download_gtsrb()
    train_dir = find_train_dir()
    
    if not train_dir:
        print("Error: Could not locate training images. Ensure dataset is extracted correctly.")
        return

    print(f"Using training directory: {train_dir}")
    
    # 2. Data Generators
    train_datagen = get_train_generator()
    
    train_generator = train_datagen.flow_from_directory(
        train_dir,
        target_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        subset='training'
    )
    
    val_generator = train_datagen.flow_from_directory(
        train_dir,
        target_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        subset='validation'
    )
    
    # 3. Model
    model = build_model(num_classes=len(CLASSES))
    model.summary()
    
    # 4. Callbacks
    callbacks = [
        ModelCheckpoint(str(MODEL_PATH), save_best_only=True, monitor='val_accuracy'),
        EarlyStopping(patience=10, restore_best_weights=True),
        ReduceLROnPlateau(factor=0.2, patience=5, min_lr=1e-6),
        TensorBoard(log_dir=str(BASE_DIR / 'logs'))
    ]
    
    # 5. Training
    history = model.fit(
        train_generator,
        epochs=EPOCHS,
        validation_data=val_generator,
        callbacks=callbacks
    )
    
    # 6. Evaluation & Visualizations
    print("Training complete. Generating plots...")
    
    # Plot history
    plot_training_history(history, save_path=BASE_DIR / 'training_history.png')
    
    # Evaluate and Confusion Matrix
    # (Simplified evaluation on validation set for demonstration)
    val_generator.reset()
    y_pred_raw = model.predict(val_generator)
    y_pred = np.argmax(y_pred_raw, axis=1)
    y_true = val_generator.classes
    
    class_names = [CLASSES[i]['name'] for i in range(len(CLASSES))]
    
    plot_confusion_matrix(y_true, y_pred, class_names, save_path=BASE_DIR / 'confusion_matrix.png')
    save_classification_report(y_true, y_pred, class_names, save_path=BASE_DIR / 'classification_report.txt')
    
    with open(BASE_DIR / 'model_summary.txt', 'w') as f:
        model.summary(print_fn=lambda x: f.write(x + '\n'))
    
    print(f"Final Validation Accuracy: {history.history['val_accuracy'][-1]:.4f}")

if __name__ == "__main__":
    train()
