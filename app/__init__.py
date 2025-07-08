from flask import Flask
from .db import db
from .routes import bp

def create_app():
    app = Flask(__name__)
    
    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vulnbook.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'vulnerable-secret-key'
    app.config['UPLOAD_FOLDER'] = 'app/static/uploads'
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}
    
    # Initialize database
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(bp)
    
    return app