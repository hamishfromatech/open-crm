from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_login import LoginManager
import os
import logging
from werkzeug.utils import secure_filename
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

def create_app(config_class='config.Config'):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    admin.init_app(app)
    login_manager.init_app(app)
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Create upload folder if it doesn't exist
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # Set up logging
    if not app.debug:
        # Production logging
        if not os.path.exists('logs'):
            os.makedirs('logs')

        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler('logs/crm.log', maxBytes=10240000, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('CRM application startup')
    else:
        # Development logging
        logging.basicConfig(level=logging.DEBUG)
        app.logger.setLevel(logging.DEBUG)
        app.logger.info('CRM application startup in debug mode')

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp)

    # Add error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f'Page not found: {request.url}')
        if request.is_json:
            return jsonify({'error': 'Not found'}), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Internal server error: {error}')
        if request.is_json:
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f'Unhandled exception: {e}')
        if request.is_json:
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500

    # Create database tables
    with app.app_context():
        db.create_all()

        # Initialize admin views after database is created
        # Store reference to avoid naming collision with app.admin module
        admin_instance = admin
        from app.admin import init_admin_views
        init_admin_views(admin_instance)

    return app
