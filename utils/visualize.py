import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from sklearn.metrics import confusion_matrix, classification_report
import numpy as np
from config import BASE_DIR

def plot_training_history(history, save_path=None):
    """Plot accuracy and loss curves."""
    acc = history.history['accuracy']
    val_acc = history.history['val_accuracy']
    loss = history.history['loss']
    val_loss = history.history['val_loss']
    epochs_range = range(len(acc))

    plt.figure(figsize=(12, 10))
    plt.subplot(2, 2, 1)
    plt.plot(epochs_range, acc, label='Training Accuracy', color='#00FF88')
    plt.plot(epochs_range, val_acc, label='Validation Accuracy', color='#FF3366')
    plt.title('Training and Validation Accuracy')
    plt.legend(loc='lower right')
    plt.grid(True, alpha=0.3)

    plt.subplot(2, 2, 2)
    plt.plot(epochs_range, loss, label='Training Loss', color='#00FF88')
    plt.plot(epochs_range, val_loss, label='Validation Loss', color='#FF3366')
    plt.title('Training and Validation Loss')
    plt.legend(loc='upper right')
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    plt.close()

def plot_confusion_matrix(y_true, y_pred, classes, save_path=None):
    """Plot confusion matrix heatmap."""
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(20, 20))
    sns.heatmap(cm, annot=False, fmt='d', cmap='Blues', xticklabels=classes, yticklabels=classes)
    plt.title('Confusion Matrix')
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    
    if save_path:
        plt.savefig(save_path)
    plt.close()

def save_classification_report(y_true, y_pred, target_names, save_path):
    """Save classification report to text file."""
    report = classification_report(y_true, y_pred, target_names=target_names)
    with open(save_path, 'w') as f:
        f.write(report)
