from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from app.models.models import db, Attendance, Student, Staff, Class
from datetime import datetime, date, timedelta
import json

bp = Blueprint('attendance', __name__, url_prefix='/attendance')

# Dashboard view
@bp.route('/')
def dashboard():
    """Attendance dashboard showing today's overview"""
    today = date.today()
    
    # Get today's statistics
    student_attendance = Attendance.query.filter(
        Attendance.entity_type == 'STUDENT',
        Attendance.date == today
    ).all()
    
    staff_attendance = Attendance.query.filter(
        Attendance.entity_type == 'STAFF',
        Attendance.date == today
    ).all()
    
    stats = {
        'student_total': Student.query.filter_by(is_active=True).count(),
        'student_present': len([a for a in student_attendance if a.status == 'PRESENT']),
        'student_absent': len([a for a in student_attendance if a.status == 'ABSENT']),
        'staff_total': Staff.query.filter_by(is_active=True).count(),
        'staff_present': len([a for a in staff_attendance if a.status == 'PRESENT']),
        'staff_absent': len([a for a in staff_attendance if a.status == 'ABSENT']),
        'late_arrivals': len([a for a in student_attendance + staff_attendance 
                            if a.arrival_time and a.arrival_time > a.expected_arrival_time])
    }
    
    return render_template('attendance/dashboard.html', stats=stats, today=today)

# Student attendance views
@bp.route('/students')
def student_attendance():
    """List all students attendance for today with marking interface"""
    class_id = request.args.get('class_id', type=int)
    date_str = request.args.get('date', type=str)
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
    except ValueError:
        selected_date = date.today()
    
    # Base query
    students = Student.query.filter_by(is_active=True)
    
    if class_id:
        students = students.filter_by(class_id=class_id)
    
    students = students.all()
    
    # Get existing attendance records
    attendance_records = {
        record.entity_id: record for record in Attendance.query.filter(
            Attendance.entity_type == 'STUDENT',
            Attendance.date == selected_date
        ).all()
    }
    
    classes = Class.query.filter_by(is_active=True).all()
    
    return render_template('attendance/student_list.html',
                         students=students,
                         classes=classes,
                         selected_class=class_id,
                         selected_date=selected_date,
                         attendance_records=attendance_records)

@bp.route('/students/mark', methods=['POST'])
def mark_student_attendance():
    """Mark or update student attendance"""
    student_id = request.form.get('student_id', type=int)
    attendance_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
    status = request.form.get('status')
    arrival_time = request.form.get('arrival_time')
    remarks = request.form.get('remarks')
    
    try:
        # Check for existing record
        attendance = Attendance.query.filter_by(
            entity_type='STUDENT',
            entity_id=student_id,
            date=attendance_date
        ).first()
        
        if not attendance:
            attendance = Attendance(
                entity_type='STUDENT',
                entity_id=student_id,
                date=attendance_date
            )
        
        attendance.status = status
        if arrival_time:
            attendance.arrival_time = datetime.strptime(arrival_time, '%H:%M').time()
        attendance.remarks = remarks
        attendance.marked_by = request.form.get('staff_id')  # Current logged-in staff
        
        if not attendance.id:
            db.session.add(attendance)
        db.session.commit()
        
        flash('Attendance marked successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error marking attendance: {str(e)}', 'error')
    
    return redirect(url_for('attendance.student_attendance'))

# Class attendance view
@bp.route('/class/<int:class_id>')
def class_attendance(class_id):
    """View and manage attendance for a specific class"""
    class_obj = Class.query.get_or_404(class_id)
    selected_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    
    # Get attendance records for the class
    attendance_records = Attendance.query.join(
        Student, 
        Attendance.entity_id == Student.id
    ).filter(
        Student.class_id == class_id,
        Attendance.date == selected_date,
        Attendance.entity_type == 'STUDENT'
    ).all()
    
    return render_template('attendance/class_view.html',
                         class_obj=class_obj,
                         selected_date=selected_date,
                         attendance_records=attendance_records)

# Staff attendance views
@bp.route('/staff')
def staff_attendance():
    """List all staff attendance for today with marking interface"""
    date_str = request.args.get('date', type=str)
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
    except ValueError:
        selected_date = date.today()
    
    staff_members = Staff.query.filter_by(is_active=True).all()
    
    # Get existing attendance records
    attendance_records = {
        record.entity_id: record for record in Attendance.query.filter(
            Attendance.entity_type == 'STAFF',
            Attendance.date == selected_date
        ).all()
    }
    
    return render_template('attendance/staff_list.html',
                         staff_members=staff_members,
                         selected_date=selected_date,
                         attendance_records=attendance_records)

@bp.route('/staff/mark', methods=['POST'])
def mark_staff_attendance():
    """Mark or update staff attendance"""
    staff_id = request.form.get('staff_id', type=int)
    attendance_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
    status = request.form.get('status')
    arrival_time = request.form.get('arrival_time')
    remarks = request.form.get('remarks')
    
    try:
        attendance = Attendance.query.filter_by(
            entity_type='STAFF',
            entity_id=staff_id,
            date=attendance_date
        ).first()
        
        if not attendance:
            attendance = Attendance(
                entity_type='STAFF',
                entity_id=staff_id,
                date=attendance_date
            )
        
        attendance.status = status
        if arrival_time:
            attendance.arrival_time = datetime.strptime(arrival_time, '%H:%M').time()
        attendance.remarks = remarks
        attendance.marked_by = request.form.get('admin_id')  # Current logged-in admin
        
        if not attendance.id:
            db.session.add(attendance)
        db.session.commit()
        
        flash('Staff attendance marked successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error marking attendance: {str(e)}', 'error')
    
    return redirect(url_for('attendance.staff_attendance'))

# History views
@bp.route('/student/<int:student_id>/history')
def student_history(student_id):
    """View attendance history for a specific student"""
    student = Student.query.get_or_404(student_id)
    month = request.args.get('month', type=int, default=date.today().month)
    year = request.args.get('year', type=int, default=date.today().year)
    
    attendance_records = Attendance.query.filter(
        Attendance.entity_type == 'STUDENT',
        Attendance.entity_id == student_id,
        db.extract('month', Attendance.date) == month,
        db.extract('year', Attendance.date) == year
    ).order_by(Attendance.date.desc()).all()
    
    return render_template('attendance/student_history.html',
                         student=student,
                         attendance_records=attendance_records,
                         month=month,
                         year=year)

@bp.route('/staff/<int:staff_id>/history')
def staff_history(staff_id):
    """View attendance history for a specific staff member"""
    staff = Staff.query.get_or_404(staff_id)
    month = request.args.get('month', type=int, default=date.today().month)
    year = request.args.get('year', type=int, default=date.today().year)
    
    attendance_records = Attendance.query.filter(
        Attendance.entity_type == 'STAFF',
        Attendance.entity_id == staff_id,
        db.extract('month', Attendance.date) == month,
        db.extract('year', Attendance.date) == year
    ).order_by(Attendance.date.desc()).all()
    
    return render_template('attendance/staff_history.html',
                         staff=staff,
                         attendance_records=attendance_records,
                         month=month,
                         year=year)

# Biometric integration API
@bp.route('/biometric/mark', methods=['POST'])
def biometric_attendance():
    """Simple API endpoint for biometric attendance integration"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['entity_type', 'entity_id', 'timestamp', 'device_id']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Parse timestamp
        try:
            timestamp = datetime.fromisoformat(data['timestamp'])
        except ValueError:
            return jsonify({'error': 'Invalid timestamp format'}), 400
        
        # Create/Update attendance record
        attendance = Attendance.query.filter_by(
            entity_type=data['entity_type'],
            entity_id=data['entity_id'],
            date=timestamp.date()
        ).first()
        
        if not attendance:
            attendance = Attendance(
                entity_type=data['entity_type'],
                entity_id=data['entity_id'],
                date=timestamp.date(),
                status='PRESENT'
            )
            db.session.add(attendance)
        
        attendance.arrival_time = timestamp.time()
        attendance.remarks = f"Marked by biometric device {data['device_id']}"
        
        db.session.commit()
        
        return jsonify({'message': 'Attendance marked successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
