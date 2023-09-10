from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship, backref
from database import db
from datetime import datetime


class CelebrityImage(db.Model):
    __tablename__ = 'celebrities_images'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    celebrity_id = Column(Integer, ForeignKey('celebrities.id'), nullable=False, index=True)
    image_path = Column(String, nullable=False)
    face_image_path = Column(String)
    face_embedding = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    celebrity = relationship('Celebrity', backref=backref('images', lazy=True))
