from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from datetime import datetime
import calendar


db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from app.routes.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.routes.student import bp as student_bp
    app.register_blueprint(student_bp)

    from app.routes.staff import bp as staff_bp
    app.register_blueprint(staff_bp, url_prefix='/staff')

    from app.routes.classes import bp as class_bp
    app.register_blueprint(class_bp)

    from app.routes.fees import bp as fees_bp
    app.register_blueprint(fees_bp)

    
    from app.routes.attendance import bp as attendance_bp
    app.register_blueprint(attendance_bp)


    from app.routes.branch import bp as branch_bp
    app.register_blueprint(branch_bp)

    from app.routes.events import bp as events_bp
    app.register_blueprint(events_bp)

    from app.routes.inventory import bp as inventory_bp
    app.register_blueprint(inventory_bp)


    # Custom Jinja Filters
    @app.template_filter('month_name')
    def month_name_filter(month_number):
        if isinstance(month_number, int) and 1 <= month_number <= 12:
            return calendar.month_name[month_number]
        return ""

    @app.template_filter('format_money')
    def format_money(amount):
        if amount is None:
            return "0.00"
        return "{:,.2f}".format(float(amount))

    @app.template_filter('date')
    def format_date(date):
        if not date:
            return ""
        if isinstance(date, str):
            try:
                date = datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                return date
        return date.strftime('%d-%m-%Y')

    @app.template_filter('datetime')
    def format_datetime(dt):
        if not dt:
            return ""
        return dt.strftime('%d-%m-%Y %H:%M')

    @app.template_filter('timeago')
    def timeago(dt):
        if not dt:
            return ""
        now = datetime.utcnow()
        diff = now - dt
        
        if diff.days > 365:
            years = diff.days // 365
            return f"{years}y ago"
        elif diff.days > 30:
            months = diff.days // 30
            return f"{months}m ago"
        elif diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            return "Just now"
    # Create upload directories
    

    import os
    os.makedirs(os.path.join(app.static_folder, 'uploads', 'staff'), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'uploads', 'documents'), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'uploads'), exist_ok=True)

    return app
