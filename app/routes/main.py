from flask import Blueprint, render_template
from app.models.models import Student, Staff, Class, Branch

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    stats = {
        'total_students': Student.query.count(),
        'total_staff': Staff.query.count(),
        'total_classes': Class.query.count(),
        'total_branches': Branch.query.count()
    }
    return render_template('index.html', stats=stats)
