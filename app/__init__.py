from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_login import LoginManager
from flask_uploads import UploadSet, configure_uploads, IMAGES, TEXT, DOCUMENTS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
admin = Admin(name='CRM Admin', template_mode='bootstrap4')
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Configure file uploads
documents = UploadSet('documents', DOCUMENTS + TEXT + IMAGES)

def create_app(config_class='config.Config'):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    admin.init_app(app)
    login_manager.init_app(app)

    # Configure uploads
    configure_uploads(app, documents)

    # Create upload folder if it doesn't exist
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # Initialize admin views
    from app.admin import init_admin_views
    init_admin_views(admin)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app
