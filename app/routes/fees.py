from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.models.models import db, FeeType, FeeTransaction, Student, Staff
from datetime import datetime, date
from sqlalchemy import extract

bp = Blueprint('fees', __name__, url_prefix='/fees')

@bp.route('/')
def list_fees():
    """List all fee transactions with filtering"""
    # Get filter parameters
    entity_type = request.args.get('entity_type', 'STUDENT')
    status = request.args.get('status')
    month = request.args.get('month', type=int, default=datetime.now().month)
    year = request.args.get('year', type=int, default=datetime.now().year)
    search = request.args.get('search', '')

    # Base query
    query = FeeTransaction.query

    # Apply filters
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
    if status:
        query = query.filter_by(transaction_status=status)
    if month and year:
        query = query.filter(
            extract('month', FeeTransaction.due_date) == month,
            extract('year', FeeTransaction.due_date) == year
        )
    if search:
        if entity_type == 'STUDENT':
            query = query.join(Student, 
                FeeTransaction.entity_id == Student.id).filter(
                    Student.first_name.ilike(f'%{search}%') | 
                    Student.last_name.ilike(f'%{search}%')
                )
        else:
            query = query.join(Staff,
                FeeTransaction.entity_id == Staff.id).filter(
                    Staff.first_name.ilike(f'%{search}%') |
                    Staff.last_name.ilike(f'%{search}%')
                )

    transactions = query.order_by(FeeTransaction.due_date.desc()).all()
    fee_types = FeeType.query.all()
    current_year = datetime.now().year
        
    # Get filter parameters (your existing code)
    entity_type = request.args.get('entity_type', 'STUDENT')
    status = request.args.get('status')
    month = request.args.get('month', type=int, default=datetime.now().month)
    year = request.args.get('year', type=int, default=current_year)
    search = request.args.get('search', '')

    # Calculate statistics
    transactions = FeeTransaction.query.all()  # or your existing filtered query
    stats = {
        'total_amount': sum(t.amount for t in transactions) if transactions else 0,
        'collected_amount': sum(t.amount for t in transactions if t.transaction_status == 'PAID'),
        'pending_amount': sum(t.amount for t in transactions if t.transaction_status == 'PENDING'),
        'overdue_amount': sum(t.amount for t in transactions if t.transaction_status == 'OVERDUE'),
        'total_transactions': len(transactions),
        'paid_transactions': len([t for t in transactions if t.transaction_status == 'PAID']),
        'pending_transactions': len([t for t in transactions if t.transaction_status == 'PENDING'])
    }

    return render_template('fees/list.html',
                         transactions=transactions,
                         fee_types=FeeType.query.all(),
                         selected_type=entity_type,
                         selected_status=status,
                         selected_month=month,
                         selected_year=year,
                         search=search,
                         current_year=current_year,
                         # Add these statistics
                         total_amount=stats['total_amount'],
                         collected_amount=stats['collected_amount'],
                         pending_amount=stats['pending_amount'],
                         overdue_amount=stats['overdue_amount'])

@bp.route('/types')
def list_fee_types():
    """List and manage fee types"""
    fee_types = FeeType.query.all()
    fee_types_dict = [fee_type.to_dict() for fee_type in fee_types]
    return render_template('fees/types.html', 
                         fee_types=fee_types,           # For normal template use
                         fee_types_json=fee_types_dict) 

@bp.route('/types/add', methods=['POST'])
def add_fee_type():
    """Add a new fee type"""
    try:
        fee_type = FeeType(
            name=request.form['name'],
            description=request.form.get('description'),
            amount=float(request.form['amount']),
            frequency=request.form['frequency'],
            is_active=True
        )
        db.session.add(fee_type)
        db.session.commit()
        flash('Fee type added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding fee type: {str(e)}', 'error')
    
    return redirect(url_for('fees.list_fee_types'))

@bp.route('/collect', methods=['POST'])
def collect_fee():
    """Record a fee payment"""
    try:
        transaction = FeeTransaction.query.get_or_404(request.form['transaction_id'])
        
        transaction.payment_date = datetime.strptime(request.form['payment_date'], '%Y-%m-%d')
        transaction.payment_method = request.form['payment_method']
        transaction.transaction_status = 'PAID'
        transaction.reference_number = request.form.get('reference_number')
        transaction.remarks = request.form.get('remarks')
        
        db.session.commit()
        flash('Payment recorded successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error recording payment: {str(e)}', 'error')
    
    return redirect(url_for('fees.list_fees'))

@bp.route('/generate', methods=['POST'])
def generate_fees():
    """Generate monthly fees for students"""
    try:
        fee_type_id = request.form['fee_type_id']
        due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d')
        
        # Get active students
        students = Student.query.filter_by(is_active=True).all()
        fee_type = FeeType.query.get(fee_type_id)
        
        # Create fee transactions
        for student in students:
            transaction = FeeTransaction(
                entity_type='STUDENT',
                entity_id=student.id,
                fee_type_id=fee_type_id,
                amount=fee_type.amount,
                due_date=due_date,
                transaction_status='PENDING'
            )
            db.session.add(transaction)
        
        db.session.commit()
        flash(f'Generated fees for {len(students)} students!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error generating fees: {str(e)}', 'error')
    
    return redirect(url_for('fees.list_fees'))

@bp.route('/student/<int:student_id>')
def student_fees(student_id):
    """View fee history for a student"""
    student = Student.query.get_or_404(student_id)
    transactions = FeeTransaction.query.filter_by(
        entity_type='STUDENT',
        entity_id=student_id
    ).order_by(FeeTransaction.due_date.desc()).all()
    
    return render_template('fees/student.html',
                         student=student,
                         transactions=transactions)

@bp.route('/report')
def fee_report():
    """Simple fee collection report"""
    month = request.args.get('month', type=int, default=datetime.now().month)
    year = request.args.get('year', type=int, default=datetime.now().year)
    
    # Get monthly collection stats
    transactions = FeeTransaction.query.filter(
        extract('month', FeeTransaction.due_date) == month,
        extract('year', FeeTransaction.due_date) == year
    ).all()
    
    stats = {
        'total_amount': sum(t.amount for t in transactions),
        'collected_amount': sum(t.amount for t in transactions if t.transaction_status == 'PAID'),
        'pending_amount': sum(t.amount for t in transactions if t.transaction_status == 'PENDING'),
        'total_transactions': len(transactions),
        'paid_transactions': len([t for t in transactions if t.transaction_status == 'PAID']),
        'pending_transactions': len([t for t in transactions if t.transaction_status == 'PENDING'])
    }
    
    current_year = datetime.now().year
    return render_template('fees/report.html',
                         transactions=transactions,
                         stats=stats,
                         month=month,
                         year=year,
                         current_year=current_year)
