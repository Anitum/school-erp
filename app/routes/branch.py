from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.models.models import db, Branch, Student, Staff
from datetime import datetime

bp = Blueprint('branch', __name__, url_prefix='/branches')

@bp.route('/')
def list_branches():
    """List all branches with simple filtering"""
    # Get filter parameters
    status = request.args.get('status')
    search = request.args.get('search', '')

    # Base query
    query = Branch.query

    # Apply filters
    if status:
        query = query.filter_by(is_active=(status == 'active'))
    if search:
        search = f"%{search}%"
        query = query.filter(
            db.or_(
                Branch.name.ilike(search),
                Branch.address.ilike(search),
                Branch.contact_number.ilike(search),
                Branch.email.ilike(search)
            )
        )

    branches = query.order_by(Branch.name).all()
    return render_template('branch/list.html', branches=branches)

@bp.route('/add', methods=['GET', 'POST'])
def add_branch():
    """Add a new branch"""
    if request.method == 'POST':
        try:
            branch = Branch(
                name=request.form['name'],
                address=request.form['address'],
                contact_number=request.form['contact_number'],
                email=request.form.get('email'),
                is_active=True
            )
            
            db.session.add(branch)
            db.session.commit()
            flash('Branch added successfully!', 'success')
            return redirect(url_for('branch.view_branch', branch_id=branch.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding branch: {str(e)}', 'error')

    return render_template('branch/add.html')

@bp.route('/<int:branch_id>')
def view_branch(branch_id):
    """View branch details and statistics"""
    branch = Branch.query.get_or_404(branch_id)
    
    # Get basic statistics
    stats = {
        'total_students': Student.query.filter_by(branch_id=branch_id, is_active=True).count(),
        'total_staff': Staff.query.filter_by(branch_id=branch_id, is_active=True).count(),
        'active_classes': len(set(student.class_id for student in branch.students if student.is_active)),
        'teachers': Staff.query.filter_by(branch_id=branch_id, staff_type='TEACHER', is_active=True).count()
    }
    
    return render_template('branch/view.html',
                         branch=branch,
                         stats=stats)

@bp.route('/<int:branch_id>/edit', methods=['GET', 'POST'])
def edit_branch(branch_id):
    """Edit branch details"""
    branch = Branch.query.get_or_404(branch_id)
    
    if request.method == 'POST':
        try:
            branch.name = request.form['name']
            branch.address = request.form['address']
            branch.contact_number = request.form['contact_number']
            branch.email = request.form.get('email')
            branch.is_active = bool(request.form.get('is_active'))
            
            db.session.commit()
            flash('Branch updated successfully!', 'success')
            return redirect(url_for('branch.view_branch', branch_id=branch_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating branch: {str(e)}', 'error')

    return render_template('branch/edit.html', branch=branch)

@bp.route('/<int:branch_id>/students')
def branch_students(branch_id):
    """View all students in the branch"""
    branch = Branch.query.get_or_404(branch_id)
    
    # Get filter parameters
    class_id = request.args.get('class_id', type=int)
    status = request.args.get('status')
    search = request.args.get('search', '')

    # Base query
    query = Student.query.filter_by(branch_id=branch_id)

    # Apply filters
    if class_id:
        query = query.filter_by(class_id=class_id)
    if status:
        query = query.filter_by(is_active=(status == 'active'))
    if search:
        search = f"%{search}%"
        query = query.filter(
            db.or_(
                Student.first_name.ilike(search),
                Student.last_name.ilike(search)
            )
        )

    students = query.order_by(Student.first_name).all()
    return render_template('branch/students.html',
                         branch=branch,
                         students=students)

@bp.route('/<int:branch_id>/staff')
def branch_staff(branch_id):
    """View all staff in the branch"""
    branch = Branch.query.get_or_404(branch_id)
    
    # Get filter parameters
    staff_type = request.args.get('staff_type')
    status = request.args.get('status')
    search = request.args.get('search', '')

    # Base query
    query = Staff.query.filter_by(branch_id=branch_id)

    # Apply filters
    if staff_type:
        query = query.filter_by(staff_type=staff_type)
    if status:
        query = query.filter_by(is_active=(status == 'active'))
    if search:
        search = f"%{search}%"
        query = query.filter(
            db.or_(
                Staff.first_name.ilike(search),
                Staff.last_name.ilike(search)
            )
        )

    staff = query.order_by(Staff.first_name).all()
    return render_template('branch/staff.html',
                         branch=branch,
                         staff=staff)
