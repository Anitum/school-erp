from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.models.models import db, Student, Class, Branch, Parent, Document, TransportRoute
from datetime import datetime
import os
from werkzeug.utils import secure_filename

bp = Blueprint('student', __name__, url_prefix='/students')

@bp.route('/')
def list_students():
    """List all students with filtering options"""
    # Get filter parameters
    class_id = request.args.get('class_id', type=int)
    branch_id = request.args.get('branch_id', type=int)
    status = request.args.get('status')
    search = request.args.get('search', '')

    # Base query
    query = Student.query

    # Apply filters
    if class_id:
        query = query.filter_by(class_id=class_id)
    if branch_id:
        query = query.filter_by(branch_id=branch_id)
    if status:
        query = query.filter_by(is_active=(status == 'active'))
    if search:
        search = f"%{search}%"
        query = query.filter(
            db.or_(
                Student.first_name.ilike(search),
                Student.last_name.ilike(search),
                Student.aadhaar_number.ilike(search)
            )
        )

    # Get all required data for filters
    students = query.order_by(Student.first_name).all()
    classes = Class.query.all()
    branches = Branch.query.all()

    return render_template('students/list.html',
                         students=students,
                         classes=classes,
                         branches=branches,
                         selected_class=class_id,
                         selected_branch=branch_id,
                         selected_status=status,
                         search=search)

@bp.route('/add', methods=['GET', 'POST'])
def add_student():
    """Add a new student"""
    if request.method == 'POST':
        try:
            # Create new student
            student = Student(
                first_name=request.form['first_name'],
                middle_name=request.form.get('middle_name'),
                last_name=request.form['last_name'],
                date_of_birth=datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d'),
                blood_group=request.form.get('blood_group'),
                aadhaar_number=request.form.get('aadhaar_number'),
                class_id=request.form['class_id'],
                branch_id=request.form['branch_id'],
                transport_route_id=request.form.get('transport_route_id'),
                joining_date=datetime.now().date()
            )
            db.session.add(student)
            db.session.flush()  # Get student ID before committing

            # Handle document uploads if any
            if 'documents' in request.files:
                for uploaded_file in request.files.getlist('documents'):
                    if uploaded_file and uploaded_file.filename:
                        filename = secure_filename(uploaded_file.filename)
                        file_path = os.path.join('uploads', 'students', str(student.id), filename)
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        uploaded_file.save(file_path)

                        document = Document(
                            entity_type='STUDENT',
                            entity_id=student.id,
                            document_type=request.form.get('document_type', 'OTHER'),
                            file_path=file_path,
                            file_type=os.path.splitext(filename)[1],
                            description=request.form.get('document_description')
                        )
                        db.session.add(document)

            db.session.commit()
            flash('Student added successfully!', 'success')
            return redirect(url_for('student.view_student', student_id=student.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding student: {str(e)}', 'error')

    # Get data for dropdowns
    classes = Class.query.filter_by(is_active=True).all()
    branches = Branch.query.filter_by(is_active=True).all()
    transport_routes = TransportRoute.query.filter_by(is_active=True).all()

    return render_template('students/add.html',
                         classes=classes,
                         branches=branches,
                         transport_routes=transport_routes)

@bp.route('/<int:student_id>')
def view_student(student_id):
    """View student details"""
    student = Student.query.get_or_404(student_id)
    return render_template('students/view.html', student=student)

@bp.route('/<int:student_id>/edit', methods=['GET', 'POST'])
def edit_student(student_id):
    """Edit student details"""
    student = Student.query.get_or_404(student_id)

    if request.method == 'POST':
        try:
            student.first_name = request.form['first_name']
            student.middle_name = request.form.get('middle_name')
            student.last_name = request.form['last_name']
            student.date_of_birth = datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d')
            student.blood_group = request.form.get('blood_group')
            student.aadhaar_number = request.form.get('aadhaar_number')
            student.class_id = request.form['class_id']
            student.branch_id = request.form['branch_id']
            student.transport_route_id = request.form.get('transport_route_id')
            student.is_active = bool(request.form.get('is_active'))

            # Handle document uploads
            if 'documents' in request.files:
                for uploaded_file in request.files.getlist('documents'):
                    if uploaded_file and uploaded_file.filename:
                        filename = secure_filename(uploaded_file.filename)
                        file_path = os.path.join('uploads', 'students', str(student.id), filename)
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        uploaded_file.save(file_path)

                        document = Document(
                            entity_type='STUDENT',
                            entity_id=student.id,
                            document_type=request.form.get('document_type', 'OTHER'),
                            file_path=file_path,
                            file_type=os.path.splitext(filename)[1],
                            description=request.form.get('document_description')
                        )
                        db.session.add(document)

            db.session.commit()
            flash('Student updated successfully!', 'success')
            return redirect(url_for('student.view_student', student_id=student.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating student: {str(e)}', 'error')

    classes = Class.query.filter_by(is_active=True).all()
    branches = Branch.query.filter_by(is_active=True).all()
    transport_routes = TransportRoute.query.filter_by(is_active=True).all()

    return render_template('students/edit.html',
                         student=student,
                         classes=classes,
                         branches=branches,
                         transport_routes=transport_routes)

@bp.route('/<int:student_id>/documents')
def student_documents(student_id):
    """View student documents"""
    student = Student.query.get_or_404(student_id)
    return render_template('students/documents.html', student=student)

@bp.route('/<int:student_id>/delete_document/<int:document_id>', methods=['POST'])
def delete_document(student_id, document_id):
    """Delete a student document"""
    document = Document.query.get_or_404(document_id)
    if document.entity_type == 'STUDENT' and document.entity_id == student_id:
        try:
            # Delete physical file
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
            # Delete database record
            db.session.delete(document)
            db.session.commit()
            flash('Document deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting document: {str(e)}', 'error')
    else:
        flash('Invalid document access!', 'error')
    
    return redirect(url_for('student.student_documents', student_id=student_id))
