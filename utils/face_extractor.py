import base64
import logging
import os
from io import BytesIO

from mtcnn.mtcnn import MTCNN
import cv2
import numpy as np

logger = logging.getLogger(name="Face extractor")

class FaceExtractor(object):
    def __init__(self, required_size=(224, 224)):
        self.MTCNN = MTCNN()
        self.required_size = required_size

    def extract(self, filename, save_filename):
        image = cv2.imread(filename)
        shape = image.shape

        if shape[2] == 3:
            pixels = np.asarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        else:
            pixels = np.asarray(cv2.cvtColor(image, cv2.COLOR_GRAY2RGB))

        results = self.MTCNN.detect_faces(pixels)

        x, y, width, height = results[0]['box']
        x1, y1 = abs(x), abs(y)
        x2, y2 = x1 + width, y1 + height

        face_detect = image[y1:y2, x1:x2]
        face_detect = np.asarray(face_detect)
        face_array = cv2.resize(face_detect, self.required_size)

        os.makedirs(os.path.dirname(save_filename), exist_ok=True)
        cv2.imwrite(save_filename, face_array)

        return face_array

    def extract_all_faces(self, file):
        nparr = np.fromstring(file.read(), np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Could not open image")

        shape = image.shape

        if shape[2] == 3:
            pixels = np.asarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        else:
            pixels = np.asarray(cv2.cvtColor(image, cv2.COLOR_GRAY2RGB))

        results = self.MTCNN.detect_faces(pixels)

        faces = []
        for result in results:
            x, y, width, height = result['box']
            if width < 60 or height < 60:
                continue
            x1, y1 = abs(x), abs(y)
            x2, y2 = x1 + width, y1 + height

            face_detect = image[y1:y2, x1:x2]
            face_detect = np.asarray(face_detect)
            face_array = cv2.resize(face_detect, self.required_size)

            faces.append(face_array)

        for result in results:
            x, y, width, height = result['box']
            x1, y1 = abs(x), abs(y)
            x2, y2 = x1 + width, y1 + height
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

        is_success, buffer = cv2.imencode(".jpg", image)
        io_buf = BytesIO(buffer)
        base64_encoded_image = base64.b64encode(io_buf.getvalue()).decode('ascii')

        return faces, base64_encoded_image