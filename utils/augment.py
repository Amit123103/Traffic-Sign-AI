import cv2
import numpy as np
import random
from tensorflow.keras.preprocessing.image import ImageDataGenerator

def custom_blur_and_noise(image):
    """
    Apply random Gaussian blur and Salt & Pepper noise to images.
    Used as a preprocessing_function in ImageDataGenerator.
    """
    # Expects image as a numpy array in range [0, 255] or [0, 1] depending on generator config
    # We assume [0, 255] since it runs before rescaling usually
    
    # Random Blur
    if random.random() > 0.7:
        ksize = random.choice([3, 5])
        image = cv2.GaussianBlur(image, (ksize, ksize), 0)
    
    # Random Noise (Salt & Pepper)
    if random.random() > 0.8:
        s_vs_p = 0.5
        amount = 0.004
        out = np.copy(image)
        # Salt mode
        num_salt = np.ceil(amount * image.size * s_vs_p)
        coords = [np.random.randint(0, i - 1, int(num_salt)) for i in image.shape]
        out[tuple(coords)] = 255
        # Pepper mode
        num_pepper = np.ceil(amount * image.size * (1. - s_vs_p))
        coords = [np.random.randint(0, i - 1, int(num_pepper)) for i in image.shape]
        out[tuple(coords)] = 0
        image = out

    return image

def get_train_generator(rescale=1./255):
    """Returns an ImageDataGenerator configured for GTSRB training."""
    return ImageDataGenerator(
        rescale=rescale,
        rotation_range=15,
        zoom_range=0.2,
        width_shift_range=0.1,
        height_shift_range=0.1,
        brightness_range=[0.7, 1.3],
        horizontal_flip=False,  # Important: Traffic signs are directional!
        preprocessing_function=custom_blur_and_noise,
        validation_split=0.2
    )

def get_test_generator(rescale=1./255):
    """Returns a simple generator for testing/validation."""
    return ImageDataGenerator(rescale=rescale)
