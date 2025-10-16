import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def secure_filename_uuid(filename):
    """Generate a secure filename with UUID"""
    _, ext = os.path.splitext(filename)
    return f"{uuid.uuid4().hex}{ext}"

def get_file_size_mb(file_path):
    """Get file size in MB"""
    if os.path.exists(file_path):
        size_bytes = os.path.getsize(file_path)
        return round(size_bytes / (1024 * 1024), 2)
    return 0

def cleanup_old_files(days_old=30):
    """Clean up files older than specified days"""
    from datetime import datetime, timedelta
    from app.models import Document

    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    old_documents = Document.query.filter(Document.created_at < cutoff_date).all()

    deleted_count = 0
    for doc in old_documents:
        try:
            if os.path.exists(doc.file_path):
                os.remove(doc.file_path)
            db.session.delete(doc)
            deleted_count += 1
        except Exception as e:
            print(f"Error deleting file {doc.filename}: {e}")

    db.session.commit()
    return deleted_count
