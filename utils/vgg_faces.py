from keras_vggface.vggface import VGGFace
from keras_vggface.utils import preprocess_input
from numpy import expand_dims
import numpy as np

class VGGFaces(object):

    def __init__(self):
        self.model = VGGFace(model='resnet50',
                             include_top=False,
                             input_shape=(224, 224, 3),
                             pooling='avg')

    def get_embedding(self, face):
        pixels = face.astype('float32')
        faces = expand_dims(pixels, axis=0)
        faces = preprocess_input(faces, version=2)

        return self.model.predict(faces)

    def get_embeddings(self, faces):
        result = []
        for face in faces:
            result.append(preprocess_input(face.astype('float32'), version=2))
        result = np.stack(result)
        return self.model.predict(result)
