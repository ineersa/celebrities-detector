from models.celebrity_image import CelebrityImage
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import numpy as np
import json
from sklearn.metrics.pairwise import cosine_similarity

class Embeddings(object):

    def load(self):
        result = CelebrityImage.query.filter(CelebrityImage.face_embedding.isnot(None)).with_entities(CelebrityImage.id, CelebrityImage.face_embedding).all()
        data = [(r.id, np.array(json.loads(r.face_embedding))) for r in result]
        self.df = pd.DataFrame(data, columns=['id', 'face_embedding'])

    def find_closest(self, faces):
        data_rows = []

        for face in faces:
            similarities = cosine_similarity([face], self.df['face_embedding'].tolist())
            max_sim_index = np.argmax(similarities)
            max_sim_value = similarities[0, max_sim_index]
            closest_id = self.df.iloc[max_sim_index]['id']
            data_rows.append({'id': closest_id, 'cosine_similarity': max_sim_value})

        result = pd.DataFrame(data_rows)
        return result

    def add_embedding(self, id, embedding):
        new_row = [{'id': id, 'face_embedding': embedding}]
        new_row_df = pd.DataFrame(new_row)
        self.df = pd.concat([new_row_df, self.df]).reset_index(drop=True)

    def add_embeddings(self, ids, embeddings):
        new_rows = []
        for id, embedding in zip(ids, embeddings):
            new_rows.append({
                'id': id,
                'face_embedding': embedding
            })
        new_df = pd.DataFrame(new_rows)
        self.df = pd.concat([new_df, self.df]).reset_index(drop=True)

    def remove_record(self, id):
        self.df = self.df[self.df['id'] != id]

    def remove_records(self, ids):
        self.df = self.df[~self.df['id'].isin(ids)]