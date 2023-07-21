from keras.models import load_model  # TensorFlow is required for Keras to work
import numpy as np
import sys
import json
import base64
import os
from image_classification import ImageClassifucation
import tensorflow as tf
import matplotlib.pyplot as plt
from PIL import Image, ImageOps


# get agument from command line
arg = sys.argv[1]


def crop_and_resize(soruce: Image, resize: int):
    width, height = soruce.size
    size = min(width, height)
    if width > height:
        left = (width - size) // 2
        top = 0
        right = left + size
        bottom = size
    else:
        left = 0
        top = (height - size) // 2
        right = size
        bottom = top + size

    return soruce.crop((left, top, right, bottom)).resize((resize, resize))


image_size = 224
mode_path = os.path.join('models', 'model.keras')
class_names_path = os.path.join('models', 'labels.txt')

# image to base64
image_base64 = base64.b64encode(open(arg, "rb").read())

ic = ImageClassifucation(mode_path, class_names_path, image_size)

predictions = ic.predict(image_base64, 5)

print(json.dumps(predictions, indent=4))
