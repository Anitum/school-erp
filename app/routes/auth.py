from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from app.models.models import Admin, Staff, Student, db
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

bp = Blueprint('auth', __name__, url_prefix='/auth')

def login_required(user_type):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session or 'user_type' not in session:
                flash('Please log in first.', 'warning')
                return redirect(url_for('auth.login'))
            if session['user_type'] != user_type:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_type = request.form.get('user_type')

        if not all([username, password, user_type]):
            flash('Please fill in all fields.', 'error')
            return redirect(url_for('auth.login'))

        user = None
        if user_type == 'admin':
            user = Admin.query.filter_by(username=username).first()
        elif user_type == 'staff':
            user = Staff.query.filter_by(email=username).first()
        elif user_type == 'student':
            user = Student.query.filter_by(aadhaar_number=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['user_type'] = user_type
            session['username'] = user.username if hasattr(user, 'username') else user.full_name

            flash(f'Welcome back, {session["username"]}!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/profile')
@login_required('any')
def profile():
    user_type = session.get('user_type')
    user_id = session.get('user_id')
    
    user = None
    if user_type == 'admin':
        user = Admin.query.get(user_id)
    elif user_type == 'staff':
        user = Staff.query.get(user_id)
    elif user_type == 'student':
        user = Student.query.get(user_id)
        
    return render_template('auth/profile.html', user=user, user_type=user_type)
