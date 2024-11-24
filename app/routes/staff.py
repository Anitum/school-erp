from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.models.models import db, Staff, Branch, Document, Class, Subject, Attendance, FeeTransaction
from datetime import datetime
import os
from werkzeug.utils import secure_filename

bp = Blueprint('staff', __name__, url_prefix='/staff')

@bp.route('/')
def list_staff():
    """List all staff with filtering options"""
    # Get filter parameters
    branch_id = request.args.get('branch_id', type=int)
    staff_type = request.args.get('staff_type')
    status = request.args.get('status')
    search = request.args.get('search', '')

    # Base query
    query = Staff.query

    # Apply filters
    if branch_id:
        query = query.filter_by(branch_id=branch_id)
    if staff_type:
        query = query.filter_by(staff_type=staff_type)
    if status:
        query = query.filter_by(is_active=(status == 'active'))
    if search:
        search = f"%{search}%"
        query = query.filter(
            db.or_(
                Staff.first_name.ilike(search),
                Staff.last_name.ilike(search),
                Staff.email.ilike(search),
                Staff.phone.ilike(search)
            )
        )

    staff_members = query.order_by(Staff.first_name).all()
    branches = Branch.query.all()

    return render_template('staff/list.html',
                         staff_members=staff_members,
                         branches=branches,
                         selected_branch=branch_id,
                         selected_type=staff_type,
                         selected_status=status,
                         search=search)

@bp.route('/add', methods=['GET', 'POST'])
def add_staff():
    """Add a new staff member"""
    if request.method == 'POST':
        try:
            # First create address
            from app.models.models import Address
            address = Address(
                street_name=request.form['street_name'],
                locality=request.form['locality'],
                city=request.form['city'],
                state=request.form['state'],
                pin_code=request.form['pin_code'],
                address_type=request.form.get('address_type', 'HOME')
            )
            db.session.add(address)
            db.session.flush()  # Get address ID

            # Create staff member
            staff = Staff(
                first_name=request.form['first_name'],
                middle_name=request.form.get('middle_name'),
                last_name=request.form['last_name'],
                staff_type=request.form['staff_type'],
                joining_date=datetime.strptime(request.form['joining_date'], '%Y-%m-%d'),
                branch_id=request.form['branch_id'],
                qualification=request.form.get('qualification'),
                experience_years=request.form.get('experience_years', type=int),
                gender=request.form['gender'],
                phone=request.form['phone'],
                email=request.form.get('email'),
                address_id=address.id,
                aadhaar_number=request.form.get('aadhaar_number')
            )
            db.session.add(staff)
            db.session.flush()  # Get staff ID

            # Handle document uploads
            if 'documents' in request.files:
                for uploaded_file in request.files.getlist('documents'):
                    if uploaded_file and uploaded_file.filename:
                        filename = secure_filename(uploaded_file.filename)
                        file_path = os.path.join('uploads', 'staff', str(staff.id), filename)
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        uploaded_file.save(os.path.join('app/static', file_path))

                        document = Document(
                            entity_type='STAFF',
                            entity_id=staff.id,
                            document_type=request.form.get('document_type', 'OTHER'),
                            file_path=file_path,
                            file_type=os.path.splitext(filename)[1],
                            description=request.form.get('document_description')
                        )
                        db.session.add(document)

            db.session.commit()
            flash('Staff member added successfully!', 'success')
            return redirect(url_for('staff.view_staff', staff_id=staff.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error adding staff member: {str(e)}', 'error')

    branches = Branch.query.filter_by(is_active=True).all()
    return render_template('staff/add.html', branches=branches)

@bp.route('/<int:staff_id>')
def view_staff(staff_id):
    """View staff details"""
    staff_member = Staff.query.get_or_404(staff_id)
    
    # Get assigned classes for teachers
    assigned_classes = None
    if staff_member.staff_type == 'TEACHER':
        assigned_classes = Class.query.filter_by(primary_teacher_id=staff_id).all()
    
    # Get subjects taught
    subjects_taught = Subject.query.filter_by(teacher_id=staff_id).all()
    
    # Get recent attendance
    recent_attendance = Attendance.query.filter_by(
        entity_type='STAFF',
        entity_id=staff_id
    ).order_by(Attendance.date.desc()).limit(10).all()
    
    # Get salary records
    salary_records = FeeTransaction.query.filter_by(
        entity_type='STAFF',
        entity_id=staff_id
    ).order_by(FeeTransaction.due_date.desc()).limit(12).all()
    
    return render_template('staff/view.html',
                         staff=staff_member,
                         assigned_classes=assigned_classes,
                         subjects_taught=subjects_taught,
                         recent_attendance=recent_attendance,
                         salary_records=salary_records)

@bp.route('/<int:staff_id>/edit', methods=['GET', 'POST'])
def edit_staff(staff_id):
    """Edit staff details"""
    staff_member = Staff.query.get_or_404(staff_id)

    if request.method == 'POST':
        try:
            # Update staff details
            staff_member.first_name = request.form['first_name']
            staff_member.middle_name = request.form.get('middle_name')
            staff_member.last_name = request.form['last_name']
            staff_member.qualification = request.form.get('qualification')
            staff_member.experience_years = request.form.get('experience_years', type=int)
            staff_member.phone = request.form['phone']
            staff_member.email = request.form.get('email')
            staff_member.branch_id = request.form['branch_id']
            staff_member.is_active = bool(request.form.get('is_active'))

            # Update address
            staff_member.address.street_name = request.form['street_name']
            staff_member.address.locality = request.form['locality']
            staff_member.address.city = request.form['city']
            staff_member.address.state = request.form['state']
            staff_member.address.pin_code = request.form['pin_code']

            # Handle document uploads
            if 'documents' in request.files:
                for uploaded_file in request.files.getlist('documents'):
                    if uploaded_file and uploaded_file.filename:
                        filename = secure_filename(uploaded_file.filename)
                        file_path = os.path.join('uploads', 'staff', str(staff_id), filename)
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        uploaded_file.save(os.path.join('app/static', file_path))

                        document = Document(
                            entity_type='STAFF',
                            entity_id=staff_id,
                            document_type=request.form.get('document_type', 'OTHER'),
                            file_path=file_path,
                            file_type=os.path.splitext(filename)[1],
                            description=request.form.get('document_description')
                        )
                        db.session.add(document)

            db.session.commit()
            flash('Staff member updated successfully!', 'success')
            return redirect(url_for('staff.view_staff', staff_id=staff_id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating staff member: {str(e)}', 'error')

    branches = Branch.query.filter_by(is_active=True).all()
    return render_template('staff/edit.html',
                         staff=staff_member,
                         branches=branches)

@bp.route('/<int:staff_id>/documents')
def staff_documents(staff_id):
    """View staff documents"""
    staff_member = Staff.query.get_or_404(staff_id)
    return render_template('staff/documents.html', staff=staff_member)

@bp.route('/<int:staff_id>/attendance')
def staff_attendance(staff_id):
    """View staff attendance"""
    staff_member = Staff.query.get_or_404(staff_id)
    
    # Get attendance records for the current month by default
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    month = request.args.get('month', type=int, default=current_month)
    year = request.args.get('year', type=int, default=current_year)
    
    attendance_records = Attendance.query.filter(
        Attendance.entity_type == 'STAFF',
        Attendance.entity_id == staff_id,
        db.extract('month', Attendance.date) == month,
        db.extract('year', Attendance.date) == year
    ).order_by(Attendance.date).all()
    
    return render_template('staff/attendance.html',
                         staff=staff_member,
                         attendance_records=attendance_records,
                         current_month=month,
                         current_year=year)

@bp.route('/<int:staff_id>/salary')
def staff_salary(staff_id):
    """View staff salary records"""
    staff_member = Staff.query.get_or_404(staff_id)
    
    # Get salary records
    salary_records = FeeTransaction.query.filter_by(
        entity_type='STAFF',
        entity_id=staff_id
    ).order_by(FeeTransaction.due_date.desc()).all()
    
    return render_template('staff/salary.html',
                         staff=staff_member,
                         salary_records=salary_records)

@bp.route('/<int:staff_id>/subjects')
def staff_subjects(staff_id):
    """View and manage subjects for teachers"""
    staff_member = Staff.query.get_or_404(staff_id)
    
    if staff_member.staff_type != 'TEACHER':
        flash('Only teachers can be assigned subjects.', 'error')
        return redirect(url_for('staff.view_staff', staff_id=staff_id))
    
    subjects = Subject.query.filter_by(teacher_id=staff_id).all()
    return render_template('staff/subjects.html',
                         staff=staff_member,
                         subjects=subjects)

@bp.route('/<int:staff_id>/delete_document/<int:document_id>', methods=['POST'])
def delete_document(staff_id, document_id):
    """Delete a staff document"""
    document = Document.query.get_or_404(document_id)
    if document.entity_type == 'STAFF' and document.entity_id == staff_id:
        try:
            # Delete physical file
            if os.path.exists(os.path.join('app/static', document.file_path)):
                os.remove(os.path.join('app/static', document.file_path))
            # Delete database record
            db.session.delete(document)
            db.session.commit()
            flash('Document deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting document: {str(e)}', 'error')
    else:
        flash('Invalid document access!', 'error')
    
    return redirect(url_for('staff.staff_documents', staff_id=staff_id))
