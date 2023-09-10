from datetime import datetime
from database import db

class Celebrity(db.Model):
    __tablename__ = 'celebrities'
    id = db.Column(db.Integer, primary_key=True, index=True, autoincrement=True)
    name = db.Column(db.String, unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)