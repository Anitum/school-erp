from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.models.models import db, Student, Staff, Class, Branch, Parent, Address, TransportRoute
from datetime import datetime

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

# Student routes
@bp.route('/students')
def list_students():
    students = Student.query.all()
    return render_template('students/list.html', students=students)

@bp.route('/students/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        try:
            student = Student(
                first_name=request.form['first_name'],
                middle_name=request.form.get('middle_name'),
                last_name=request.form['last_name'],
                date_of_birth=datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d'),
                blood_group=request.form.get('blood_group'),
                aadhaar_number=request.form.get('aadhaar_number'),
                class_id=request.form['class_id'],
                branch_id=request.form['branch_id'],
                joining_date=datetime.now()
            )
            db.session.add(student)
            db.session.commit()
            flash('Student added successfully!', 'success')
            return redirect(url_for('main.list_students'))
        except Exception as e:
            flash(f'Error adding student: {str(e)}', 'error')
    
    classes = Class.query.all()
    branches = Branch.query.all()
    return render_template('students/add.html', classes=classes, branches=branches)

# Staff routes
@bp.route('/staff')
def list_staff():
    staff = Staff.query.all()
    return render_template('staff/list.html', staff=staff)

@bp.route('/staff/add', methods=['GET', 'POST'])
def add_staff():
    if request.method == 'POST':
        try:
            # First create address
            address = Address(
                street_name=request.form['street_name'],
                locality=request.form['locality'],
                city=request.form['city'],
                state=request.form['state'],
                pin_code=request.form['pin_code']
            )
            db.session.add(address)
            db.session.commit()

            staff = Staff(
                first_name=request.form['first_name'],
                middle_name=request.form.get('middle_name'),
                last_name=request.form['last_name'],
                staff_type=request.form['staff_type'],
                joining_date=datetime.now(),
                branch_id=request.form['branch_id'],
                qualification=request.form.get('qualification'),
                experience_years=request.form.get('experience_years'),
                gender=request.form['gender'],
                phone=request.form['phone'],
                email=request.form.get('email'),
                address_id=address.id
            )
            db.session.add(staff)
            db.session.commit()
            flash('Staff member added successfully!', 'success')
            return redirect(url_for('main.list_staff'))
        except Exception as e:
            flash(f'Error adding staff: {str(e)}', 'error')
    
    branches = Branch.query.all()
    return render_template('staff/add.html', branches=branches)

# Class routes
@bp.route('/classes')
def list_classes():
    classes = Class.query.all()
    return render_template('classes/list.html', classes=classes)

@bp.route('/classes/add', methods=['GET', 'POST'])
def add_class():
    if request.method == 'POST':
        try:
            class_ = Class(
                name=request.form['name'],
                section=request.form['section'],
                academic_year=request.form['academic_year'],
                primary_teacher_id=request.form.get('primary_teacher_id'),
                capacity=request.form.get('capacity', 30)
            )
            db.session.add(class_)
            db.session.commit()
            flash('Class added successfully!', 'success')
            return redirect(url_for('main.list_classes'))
        except Exception as e:
            flash(f'Error adding class: {str(e)}', 'error')
    
    teachers = Staff.query.filter_by(staff_type='TEACHER').all()
    return render_template('classes/add.html', teachers=teachers)

# Branch routes
@bp.route('/branches')
def list_branches():
    branches = Branch.query.all()
    return render_template('branches/list.html', branches=branches)

@bp.route('/branches/add', methods=['GET', 'POST'])
def add_branch():
    if request.method == 'POST':
        try:
            branch = Branch(
                name=request.form['name'],
                address=request.form['address'],
                contact_number=request.form['contact_number'],
                email=request.form.get('email')
            )
            db.session.add(branch)
            db.session.commit()
            flash('Branch added successfully!', 'success')
            return redirect(url_for('main.list_branches'))
        except Exception as e:
            flash(f'Error adding branch: {str(e)}', 'error')
    
    return render_template('branches/add.html')
