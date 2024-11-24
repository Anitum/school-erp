from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.models.models import db, Staff, Class, SchoolEvent
from datetime import datetime, timedelta
import holidays
from calendar import monthcalendar

bp = Blueprint('events', __name__, url_prefix='/events')

# Indian holidays instance - includes major government holidays
in_holidays = holidays.India()

@bp.route('/')
def list_events():
    """List all events with calendar view"""
    # Get current month/year or from query params
    month = request.args.get('month', type=int, default=datetime.now().month)
    year = request.args.get('year', type=int, default=datetime.now().year)
    
    # Get all events for the month
    start_date = datetime(year, month, 1)
    end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Query events for the month
    events = SchoolEvent.query.filter(
        SchoolEvent.date >= start_date,
        SchoolEvent.date <= end_date
    ).order_by(SchoolEvent.date).all()
    
    # Get holidays for the month
    monthly_holidays = []
    for date, name in in_holidays.items():
        if date.month == month and date.year == year:
            monthly_holidays.append({
                'date': date,
                'name': name,
                'type': 'HOLIDAY'
            })
    
    # Get calendar data
    calendar_data = monthcalendar(year, month)
    today = datetime.now().strftime('%Y-%m-%d')

    return render_template('events/list.html',
                         events=events,
                         holidays=monthly_holidays,
                         calendar=calendar_data,
                         current_month=month,
                         current_year=year, 
                         today=today)

@bp.route('/add', methods=['GET', 'POST'])
def add_event():
    """Add a new school event"""
    if request.method == 'POST':
        try:
            event = SchoolEvent(
                title=request.form['title'],
                description=request.form.get('description'),
                date=datetime.strptime(request.form['date'], '%Y-%m-%d'),
                event_type=request.form['event_type'],
                venue=request.form.get('venue'),
                coordinator_id=request.form.get('coordinator_id', type=int),
                is_holiday=bool(request.form.get('is_holiday')),
                participants=request.form.get('participants'),  # Store as comma-separated classes
                is_active=True
            )
            
            db.session.add(event)
            db.session.commit()
            flash('Event added successfully!', 'success')
            return redirect(url_for('events.list_events'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding event: {str(e)}', 'error')
    
    # Get staff list for coordinator selection
    staff = Staff.query.filter_by(is_active=True).order_by(Staff.first_name).all()
    classes = Class.query.filter_by(is_active=True).all()
    
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('events/add.html',
                         staff=staff,
                         classes=classes,
                         today=today)

@bp.route('/<int:event_id>/edit', methods=['GET', 'POST'])
def edit_event(event_id):
    """Edit event details"""
    event = SchoolEvent.query.get_or_404(event_id)
    
    if request.method == 'POST':
        try:
            event.title = request.form['title']
            event.description = request.form.get('description')
            event.date = datetime.strptime(request.form['date'], '%Y-%m-%d')
            event.event_type = request.form['event_type']
            event.venue = request.form.get('venue')
            event.coordinator_id = request.form.get('coordinator_id', type=int)
            event.is_holiday = bool(request.form.get('is_holiday'))
            event.participants = request.form.get('participants')
            event.is_active = bool(request.form.get('is_active'))
            
            db.session.commit()
            flash('Event updated successfully!', 'success')
            return redirect(url_for('events.list_events'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating event: {str(e)}', 'error')
    
    staff = Staff.query.filter_by(is_active=True).order_by(Staff.first_name).all()
    classes = Class.query.filter_by(is_active=True).all()
    
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('events/edit.html',
                         event=event,
                         staff=staff,
                         classes=classes,
                         today = today)

@bp.route('/<int:event_id>/delete', methods=['POST'])
def delete_event(event_id):
    """Delete an event"""
    event = SchoolEvent.query.get_or_404(event_id)
    try:
        event.is_active = False
        db.session.commit()
        flash('Event deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting event: {str(e)}', 'error')
    
    return redirect(url_for('events.list_events'))

@bp.route('/calendar')
def calendar_view():
    """Full calendar view of events and holidays"""
    month = request.args.get('month', type=int, default=datetime.now().month)
    year = request.args.get('year', type=int, default=datetime.now().year)
    
    # Get the calendar matrix
    cal_matrix = monthcalendar(year, month)
    
    # Get events and holidays
    start_date = datetime(year, month, 1)
    end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    events = SchoolEvent.query.filter(
        SchoolEvent.date >= start_date,
        SchoolEvent.date <= end_date,
        SchoolEvent.is_active == True
    ).all()
    
    # Get holidays
    monthly_holidays = []
    for date, name in in_holidays.items():
        if date.month == month and date.year == year:
            monthly_holidays.append({
                'date': date,
                'name': name
            })
    today = datetime.now().strftime('%Y-%m-%d')

    return render_template('events/calendar.html',
                         calendar=cal_matrix,
                         events=events,
                         holidays=monthly_holidays,
                         month=month,
                         year=year,
                         today=today)

@bp.route('/upcoming')
def upcoming_events():
    """View upcoming events"""
    today = datetime.now().date()
    
    # Get next 30 days events
    upcoming = SchoolEvent.query.filter(
        SchoolEvent.date >= today,
        SchoolEvent.date <= today + timedelta(days=30),
        SchoolEvent.is_active == True
    ).order_by(SchoolEvent.date).all()
    
    # Get upcoming holidays
    upcoming_holidays = []
    next_30_days = [today + timedelta(days=x) for x in range(31)]
    for date in next_30_days:
        if date in in_holidays:
            upcoming_holidays.append({
                'date': date,
                'name': in_holidays[date]
            })
    today = datetime.now().strftime('%Y-%m-%d')

    return render_template('events/upcoming.html',
                         events=upcoming,
                         holidays=upcoming_holidays,
                         today=today)
