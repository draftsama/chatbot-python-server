from keras.models import load_model  # TensorFlow is required for Keras to work
import numpy as np
from PIL import Image, ImageOps  # Install pillow instead of PIL
import base64
from io import BytesIO

# class image classification


class ImageClassifucation:
    def __init__(self, model_path: str, label_path: str):

        # Load the model
        self.model = load_model(model_path, compile=False)
        # Load the labels
        self.class_names = open(label_path, "r").readlines()

    def predict(self, image_base64: str, count: int = 1):

        # base64 to image

        # Decode the base64 string to bytes
        image_bytes = base64.b64decode(image_base64)

        # Open the image using PIL
        image = Image.open(BytesIO(image_bytes))
        size = (224, 224)
        image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
        # turn the image into a numpy array
        image_array = np.asarray(image)

        # Normalize the image
        normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1

        # Create the array of the right shape to feed into the keras model
        # The 'length' or number of images you can put into the array is
        # determined by the first position in the shape tuple, in this case 1
        data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)

        # Load the image into the array
        data[0] = normalized_image_array
        # Predicts the model
        prediction = self.model.predict(data)

        top_score_indexes = np.argsort(prediction[0])[-count:][::-1]

        # for i in range(count):
        #     print(f"Class {i+1}: {self.class_names[top_score_indexes[i]][2:]}",end="")
        #     print(f"Confidence Score:{str(prediction[0][top_score_indexes[i]])} \n")

        # return list of dict
        result = []
        for i in range(count):
            # class name
            c = self.class_names[top_score_indexes[i]][2:]
            # remove \n
            c = c.replace("\n", "")
            s = str(prediction[0][top_score_indexes[i]])
            result.append({"class": c, "score": s})
        return result
