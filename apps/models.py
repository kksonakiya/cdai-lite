from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.sqlite import JSON

from datetime import datetime
from apps import db


class ModelInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    base_model = db.Column(db.String(255))  # sdxl1.0
    model_path = db.Column(db.String(255))
    model_type = db.Column(db.String(50))  # lora # checkpoint
    trigger_words=db.Column(db.String(255))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Model {self.name}>"


class ImageGeneration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prompt = db.Column(db.Text, nullable=False)
    negative_prompt = db.Column(db.Text)
    model_used = db.Column(db.String(100), default="default-model")
    style = db.Column(db.String(50))  # optional styling (realistic, cartoon, etc.)
    trigger_words=db.Column(db.String(255))
    file_path = db.Column(db.String(255))
    status = db.Column(db.String(20), default="completed")  # completed, failed, etc.
    duration = db.Column(db.Float)  # seconds
    imggen_metadata = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

