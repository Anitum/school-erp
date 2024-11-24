from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.models.models import db, Class, Staff, Student, Subject, Branch
from datetime import datetime

bp = Blueprint('class', __name__, url_prefix='/classes')

@bp.route('/')
def list_classes():
    """List all classes with filtering options"""
    # Get filter parameters
    branch_id = request.args.get('branch_id', type=int)
    academic_year = request.args.get('academic_year', type=int, default=datetime.now().year)
    is_active = request.args.get('status')
    search = request.args.get('search', '')

    # Base query
    query = Class.query

    # Apply filters
    if branch_id:
        # Filter by branch through teacher's branch
        query = query.join(Staff, Class.primary_teacher_id == Staff.id)\
                    .filter(Staff.branch_id == branch_id)
    if academic_year:
        query = query.filter_by(academic_year=academic_year)
    if is_active is not None:
        query = query.filter_by(is_active=(is_active == 'active'))
    if search:
        search = f"%{search}%"
        query = query.filter(db.or_(
            Class.name.ilike(search),
            Class.section.ilike(search)
        ))

    current_year = datetime.now().year
    classes = query.order_by(Class.name, Class.section).all()
    branches = Branch.query.all()
    
    # Get available teachers for dropdown
    available_teachers = Staff.query.filter_by(
        staff_type='TEACHER',
        is_active=True
).all()

    return render_template('classes/list.html',
                         classes=classes,
                         branches=branches,
                         teachers=available_teachers,
                         selected_branch=branch_id,
                         selected_year=academic_year,
                         selected_status=is_active,
                         search=search,
                         current_year = current_year)

@bp.route('/add', methods=['GET', 'POST'])
def add_class():
    """Add a new class"""
    if request.method == 'POST':
        try:
            new_class = Class(
                name=request.form['name'],
                section=request.form['section'],
                academic_year=request.form.get('academic_year', datetime.now().year),
                primary_teacher_id=request.form.get('primary_teacher_id'),
                capacity=request.form.get('capacity', type=int) or 30,
                is_active=True
            )
            
            db.session.add(new_class)
            db.session.commit()
            
            flash('Class added successfully!', 'success')
            return redirect(url_for('class.view_class', class_id=new_class.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding class: {str(e)}', 'error')

    # Get available teachers
    available_teachers = Staff.query.filter_by(
        staff_type='TEACHER',
        is_active=True
    ).all()

    return render_template('classes/add.html',
                         teachers=available_teachers,
                         current_year=datetime.now().year)

@bp.route('/<int:class_id>')
def view_class(class_id):
    """View class details"""
    class_obj = Class.query.get_or_404(class_id)
    
    # Get student statistics
    student_stats = {
        'total': len(class_obj.students),
        'active': sum(1 for s in class_obj.students if s.is_active),
        'male': sum(1 for s in class_obj.students if hasattr(s, 'gender') and s.gender == 'MALE'),
        'female': sum(1 for s in class_obj.students if hasattr(s, 'gender') and s.gender == 'FEMALE')
    }
    
    # Get subject statistics
    subject_stats = {
        'total': len(class_obj.subjects),
        'teachers': len(set(subj.teacher_id for subj in class_obj.subjects if subj.teacher_id))
    }
    
    return render_template('classes/view.html',
                         class_obj=class_obj,
                         student_stats=student_stats,
                         subject_stats=subject_stats)

@bp.route('/<int:class_id>/edit', methods=['GET', 'POST'])
def edit_class(class_id):
    """Edit class details"""
    class_obj = Class.query.get_or_404(class_id)
    
    if request.method == 'POST':
        try:
            class_obj.name = request.form['name']
            class_obj.section = request.form['section']
            class_obj.primary_teacher_id = request.form.get('primary_teacher_id')
            class_obj.capacity = request.form.get('capacity', type=int) or 30
            class_obj.is_active = bool(request.form.get('is_active'))
            
            db.session.commit()
            flash('Class updated successfully!', 'success')
            return redirect(url_for('class.view_class', class_id=class_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating class: {str(e)}', 'error')

    available_teachers = Staff.query.filter_by(
        staff_type='TEACHER',
        is_active=True
    ).all()

    return render_template('classes/edit.html',
                         class_obj=class_obj,
                         teachers=available_teachers)

@bp.route('/<int:class_id>/students')
def class_students(class_id):
    """View and manage class students"""
    class_obj = Class.query.get_or_404(class_id)
    
    # Get available students for adding to class
    available_students = Student.query.filter_by(
        is_active=True
    ).filter(Student.class_id != class_id).all()
    
    return render_template('classes/students.html',
                         class_obj=class_obj,
                         available_students=available_students)

@bp.route('/<int:class_id>/subjects')
def class_subjects(class_id):
    """View and manage class subjects"""
    class_obj = Class.query.get_or_404(class_id)
    
    # Get available teachers for subject assignment
    available_teachers = Staff.query.filter_by(
        staff_type='TEACHER',
        is_active=True
    ).all()
    
    return render_template('classes/subjects.html',
                         class_obj=class_obj,
                         teachers=available_teachers)

@bp.route('/<int:class_id>/timetable')
def class_timetable(class_id):
    """View and manage class timetable"""
    class_obj = Class.query.get_or_404(class_id)
    
    return render_template('classes/timetable.html',
                         class_obj=class_obj)

@bp.route('/<int:class_id>/promote', methods=['POST'])
def promote_class(class_id):
    """Promote class to next academic year"""
    class_obj = Class.query.get_or_404(class_id)
    
    try:
        # Create new class for next year
        new_class = Class(
            name=str(int(class_obj.name) + 1) if class_obj.name.isdigit() else class_obj.name,
            section=class_obj.section,
            academic_year=class_obj.academic_year + 1,
            primary_teacher_id=class_obj.primary_teacher_id,
            capacity=class_obj.capacity,
            is_active=True
        )
        db.session.add(new_class)
        db.session.flush()  # Get new class ID
        
        # Update students
        for student in class_obj.students:
            if student.is_active:
                student.class_id = new_class.id
        
        # Mark old class as inactive
        class_obj.is_active = False
        
        db.session.commit()
        flash('Class promoted successfully!', 'success')
        return redirect(url_for('class.view_class', class_id=new_class.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error promoting class: {str(e)}', 'error')
        return redirect(url_for('class.view_class', class_id=class_id))

@bp.route('/<int:class_id>/add_student', methods=['POST'])
def add_student(class_id):
    """Add student to class"""
    class_obj = Class.query.get_or_404(class_id)
    student_id = request.form.get('student_id', type=int)
    
    if not student_id:
        flash('No student selected', 'error')
        return redirect(url_for('class.class_students', class_id=class_id))
        
    try:
        student = Student.query.get(student_id)
        if student:
            if len(class_obj.students) >= class_obj.capacity:
                flash('Class capacity reached', 'error')
            else:
                student.class_id = class_id
                db.session.commit()
                flash('Student added to class successfully!', 'success')
        else:
            flash('Student not found', 'error')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding student: {str(e)}', 'error')
        
    return redirect(url_for('class.class_students', class_id=class_id))

@bp.route('/<int:class_id>/remove_student/<int:student_id>', methods=['POST'])
def remove_student(class_id, student_id):
    """Remove student from class"""
    try:
        student = Student.query.get_or_404(student_id)
        if student.class_id == class_id:
            student.class_id = None
            db.session.commit()
            flash('Student removed from class successfully!', 'success')
        else:
            flash('Student not in this class', 'error')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing student: {str(e)}', 'error')
        
    return redirect(url_for('class.class_students', class_id=class_id))

@bp.route('/<int:class_id>/add_subject', methods=['POST'])
def add_subject(class_id):
    """Add subject to class"""
    try:
        subject = Subject(
            name=request.form['name'],
            code=request.form['code'],
            class_id=class_id,
            teacher_id=request.form.get('teacher_id'),
            credits=request.form.get('credits', type=int) or 1,
            description=request.form.get('description')
        )
        
        db.session.add(subject)
        db.session.commit()
        flash('Subject added successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding subject: {str(e)}', 'error')
        
    return redirect(url_for('class.class_subjects', class_id=class_id))

@bp.route('/<int:class_id>/remove_subject/<int:subject_id>', methods=['POST'])
def remove_subject(class_id, subject_id):
    """Remove subject from class"""
    try:
        subject = Subject.query.get_or_404(subject_id)
        if subject.class_id == class_id:
            db.session.delete(subject)
            db.session.commit()
            flash('Subject removed successfully!', 'success')
        else:
            flash('Subject not in this class', 'error')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing subject: {str(e)}', 'error')
        
    return redirect(url_for('class.class_subjects', class_id=class_id))
