# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# import os

# db = SQLAlchemy()

# def create_app():
#     app = Flask(__name__)
#     app.config['SECRET_KEY'] = 'weak-secret-key'  # VULNERABLE: Weak secret key
#     app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://shah_user:shah_password@localhost/shah_database'
#     app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#     db.init_app(app)

#     from .routes import bp
#     app.register_blueprint(bp)

#     with app.app_context():
#         db.create_all()

#     return app


from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'weak-secret-key'  # VULNERABLE: Weak secret key
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://cyberpit:cyberpit123456@postgres:5432/vulnbook_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static/uploads')
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

    # Create uploads directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)

    from .routes import bp
    app.register_blueprint(bp)

    return app