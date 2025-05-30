from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from apps.logging_config import setup_logging
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecret$007'  # Replace with a secure, random key in production

app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# Setup global app logger
logger = setup_logging("flask-app")
with app.app_context():
    from apps.models import ModelInfo
    db.create_all()
    print('DB created!')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
from apps import routes