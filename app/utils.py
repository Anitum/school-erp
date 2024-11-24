import os
from werkzeug.utils import secure_filename

def save_document(file, student_id):
    """Helper function to save uploaded documents"""
    filename = secure_filename(file.filename)
    path = os.path.join('uploads', 'students', str(student_id), filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    file.save(os.path.join('app', 'static', path))
    return path
