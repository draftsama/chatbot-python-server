import tensorflow as tf
from keras.models import load_model  # TensorFlow is required for Keras to work
import numpy as np
from PIL import Image, ImageOps  # Install pillow instead of PIL
import base64
from io import BytesIO

# class image classification


class ImageClassifucation:
    def __init__(self, model_path: str, label_path: str, image_size: int = 256):

        # Load the model
        self.model = load_model(model_path, compile=False)
        # Load the labels
        self.class_names = open(label_path, "r").readlines()
        self.image_size = image_size
        # Disable scientific notation for clarity
        np.set_printoptions(suppress=True)

    def predict(self, image_base64: str, count: int = 1):

        # base64 to image

        # Decode the base64 string to bytes
        image_bytes = base64.b64decode(image_base64)
        # Open the image using PIL
        image = Image.open(BytesIO(image_bytes))

        # Resize the image to a 256x256 with the same strategy as in TM2:
        size = (self.image_size, self.image_size)
        image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)

        img_array = tf.keras.utils.img_to_array(image)
        img_array = tf.expand_dims(img_array, 0)  # Create a batch
        predictions = self.model.predict(img_array)

        softmax = tf.nn.softmax(predictions[0])
        scores = softmax.numpy()

        # get indexes
        indexes = np.argsort(softmax)[-count:][::-1]

        results = []
        for i in indexes:
            class_name = self.class_names[i].split(" ")[1].strip()
            score = str(scores[i])
            results.append({"class": class_name, "score": score})

        return results

       
