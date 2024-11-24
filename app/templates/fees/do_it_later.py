'''


this is additional to db to add functionality of sending reminders, do it later add in the db and test it




'''






class ReminderTemplate(db.Model, TimestampMixin):
    """Reminder template model for storing SMS and email templates"""
    __tablename__ = 'reminder_template'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sms_template = db.Column(db.String(160), nullable=False)  # SMS standard length
    email_template = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<ReminderTemplate {self.name}>'

class ReminderHistory(db.Model):
    """Model to track reminder history"""
    __tablename__ = 'reminder_history'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('reminder_template.id'), nullable=False)
    type = db.Column(db.Enum('SMS', 'EMAIL', name='reminder_types'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum('SENT', 'FAILED', 'PENDING', name='reminder_status'), nullable=False)
    response = db.Column(db.Text)  # Store API response or error message
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('staff.id'))  # Staff who sent the reminder

    # Relationships
    student = db.relationship('Student', backref='reminders', lazy=True)
    template = db.relationship('ReminderTemplate', backref='sent_reminders', lazy=True)
    sender = db.relationship('Staff', backref='sent_reminders', lazy=True)

    def __repr__(self):
        return f'<ReminderHistory {self.type} to {self.student.full_name}>'
