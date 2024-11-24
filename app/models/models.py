from datetime import datetime
from app import db
from sqlalchemy import Enum
import enum
from sqlalchemy.orm import foreign

class TimestampMixin:
    """Mixin for adding timestamp fields to models"""
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Branch(db.Model, TimestampMixin):
    """Branch model with relationships to students, staff, and inventory"""
    __tablename__ = 'branch'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    students = db.relationship('Student', backref='branch', lazy=True)
    staff = db.relationship('Staff', backref='branch', lazy=True)
    inventory = db.relationship('Inventory', backref='branch', lazy=True)
    admins = db.relationship('Admin', backref='branch', lazy=True)

    def __repr__(self):
        return f'<Branch {self.name}>'

class Class(db.Model):
    """Class model with relationships to students and teachers"""
    __tablename__ = 'class'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(10), nullable=False)
    academic_year = db.Column(db.Integer, nullable=False)
    primary_teacher_id = db.Column(db.Integer, db.ForeignKey('staff.id'))
    capacity = db.Column(db.Integer, default=30)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    students = db.relationship('Student', backref='class_group', lazy=True)
    primary_teacher = db.relationship('Staff', backref='primary_class', foreign_keys=[primary_teacher_id])
    subjects = db.relationship('Subject', backref='class_group', lazy=True)

    __table_args__ = (
        db.UniqueConstraint('name', 'section', 'academic_year', name='unique_class_section'),
    )

    def __repr__(self):
        return f'<Class {self.name}-{self.section}>'

class Student(db.Model, TimestampMixin):
    """Student model with comprehensive relationships"""
    __tablename__ = 'student'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    blood_group = db.Column(db.String(5))
    aadhaar_number = db.Column(db.String(12), unique=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    transport_route_id = db.Column(db.Integer, db.ForeignKey('transport_route.id'))
    joining_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    parents = db.relationship('Parent', secondary='student_parent', back_populates='students')

    # In Student model, change the documents relationship to:
    documents = db.relationship(
       'Document',
        primaryjoin="and_(Student.id == foreign(Document.entity_id), "
                    "Document.entity_type == 'STUDENT')",
        backref=db.backref('student', uselist=False),
        viewonly=True
    )

    # Similarly for attendance:
    attendance = db.relationship(
        'Attendance',
        primaryjoin="and_(Student.id == foreign(Attendance.entity_id), "
                    "Attendance.entity_type == 'STUDENT')",
        backref=db.backref('student', uselist=False),
        viewonly=True
    )

    # And for fees:
    fees = db.relationship(
        'FeeTransaction',
        primaryjoin="and_(Student.id == foreign(FeeTransaction.entity_id), "
                    "FeeTransaction.entity_type == 'STUDENT')",
        backref=db.backref('student', uselist=False),
        viewonly=True
    )
    academic_records = db.relationship('AcademicRecord', backref='student', lazy=True)

    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f'<Student {self.full_name}>'

class Parent(db.Model, TimestampMixin):
    """Parent model with relationships to students and documents"""
    __tablename__ = 'parent'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50), nullable=False)
    phone_primary = db.Column(db.String(20), nullable=False)
    phone_secondary = db.Column(db.String(20))
    email = db.Column(db.String(100))
    occupation = db.Column(db.String(100))
    education = db.Column(db.String(100))
    relationship = db.Column(db.Enum('FATHER', 'MOTHER', 'GUARDIAN', name='relationship_types'), nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'), nullable=False)

    # Relationships
    students = db.relationship('Student', secondary='student_parent', back_populates='parents')
    documents = db.relationship(
        'Document',
        primaryjoin="and_(Parent.id == foreign(Document.entity_id), "
                    "Document.entity_type == 'PARENT')",
        backref=db.backref('parent', uselist=False),
        viewonly=True
    )

    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f'<Parent {self.full_name}>'

# Association table for student-parent relationship
student_parent = db.Table('student_parent',
    db.Column('student_id', db.Integer, db.ForeignKey('student.id'), primary_key=True),
    db.Column('parent_id', db.Integer, db.ForeignKey('parent.id'), primary_key=True)
)

class Staff(db.Model, TimestampMixin):
    """Staff model for both teachers and employees"""
    __tablename__ = 'staff'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50), nullable=False)
    staff_type = db.Column(db.Enum('TEACHER', 'EMPLOYEE', name='staff_types'), nullable=False)
    joining_date = db.Column(db.Date, nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    qualification = db.Column(db.String(100))
    experience_years = db.Column(db.Integer)
    aadhaar_number = db.Column(db.String(12), unique=True)
    gender = db.Column(db.Enum('MALE', 'FEMALE', 'OTHER', name='gender_types'), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    documents = db.relationship(
        'Document',
        primaryjoin="and_(Staff.id == foreign(Document.entity_id), "
                    "Document.entity_type == 'STAFF')",
        backref=db.backref('staff', uselist=False),
        viewonly=True
    )

    attendance = db.relationship(
        'Attendance',
        primaryjoin="and_(Staff.id == foreign(Attendance.entity_id), "
                    "Attendance.entity_type == 'STAFF')",
        backref=db.backref('staff_record', uselist=False),
        viewonly=True
    )

    salary_records = db.relationship(
        'FeeTransaction',
        primaryjoin="and_(Staff.id == foreign(FeeTransaction.entity_id), "
                    "FeeTransaction.entity_type == 'STAFF')",
        backref=db.backref('staff_payment', uselist=False),
        viewonly=True
    )
    subjects_taught = db.relationship('Subject', backref='teacher', lazy=True,
                                    primaryjoin="and_(Subject.teacher_id==Staff.id, "
                                              "Staff.staff_type=='TEACHER')")

    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f'<Staff {self.full_name}>'

class Address(db.Model):
    """Address model for staff and parents"""
    __tablename__ = 'address'
    
    id = db.Column(db.Integer, primary_key=True)
    street_name = db.Column(db.String(100), nullable=False)
    locality = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    pin_code = db.Column(db.String(10), nullable=False)
    address_type = db.Column(db.Enum('HOME', 'OFFICE', 'OTHER', name='address_types'), default='HOME')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    staff = db.relationship('Staff', backref='address', lazy=True)
    parents = db.relationship('Parent', backref='address', lazy=True)

    def __repr__(self):
        return f'<Address {self.street_name}, {self.city}>'

class Document(db.Model, TimestampMixin):
    """Document model for storing various documents"""
    __tablename__ = 'document'

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.Enum('STUDENT', 'STAFF', 'PARENT', name='entity_types'), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    document_type = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))

    __table_args__ = (
        db.Index('idx_entity', 'entity_type', 'entity_id'),
    )

    def __repr__(self):
        return f'<Document {self.document_type} for {self.entity_type} {self.entity_id}>'

class TransportRoute(db.Model):
    """Transport route model with stops"""
    __tablename__ = 'transport_route'
    
    id = db.Column(db.Integer, primary_key=True)
    route_name = db.Column(db.String(50), nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False)
    driver_name = db.Column(db.String(100), nullable=False)
    driver_phone = db.Column(db.String(20), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    students = db.relationship('Student', backref='transport_route', lazy=True)
    stops = db.relationship('TransportStop', backref='route', lazy=True, order_by='TransportStop.sequence')

    def __repr__(self):
        return f'<TransportRoute {self.route_name}>'

class TransportStop(db.Model):
    """Transport stop model"""
    __tablename__ = 'transport_stop'
    
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('transport_route.id'), nullable=False)
    stop_name = db.Column(db.String(100), nullable=False)
    sequence = db.Column(db.Integer, nullable=False)
    pickup_time = db.Column(db.Time, nullable=False)
    drop_time = db.Column(db.Time, nullable=False)

    def __repr__(self):
        return f'<TransportStop {self.stop_name}>'

class Subject(db.Model):
    """Subject model for academic tracking"""
    __tablename__ = 'subject'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True)
    description = db.Column(db.Text)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('staff.id'))
    credits = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    academic_records = db.relationship('AcademicRecord', backref='subject', lazy=True)
    
    def __repr__(self):
        return f'<Subject {self.name}>'

class AcademicRecord(db.Model, TimestampMixin):
    """Academic records for tracking student performance"""
    __tablename__ = 'academic_record'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    exam_type = db.Column(db.Enum('UNIT_TEST', 'MIDTERM', 'FINAL', 'ASSIGNMENT', name='exam_types'), nullable=False)
    marks_obtained = db.Column(db.Float, nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    grade = db.Column(db.String(2))
    remarks = db.Column(db.Text)
    exam_date = db.Column(db.Date, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'subject_id', 'exam_type', 'exam_date', 
                          name='unique_student_subject_exam'),
    )

    def __repr__(self):
        return f'<AcademicRecord {self.student_id}-{self.subject_id}>'

class Attendance(db.Model):
    """Attendance tracking for students and staff"""
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.Enum('STUDENT', 'STAFF', name='attendance_entity_types'), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum('PRESENT', 'ABSENT', 'HALF_DAY', 'LEAVE', name='attendance_status'), nullable=False)
    remarks = db.Column(db.String(255))
    marked_by = db.Column(db.Integer, db.ForeignKey('staff.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    arrival_time = db.Column(db.Time)  # Actual arrival time
    expected_arrival_time = db.Column(db.Time)  # Expected arrival time

    __table_args__ = (
        db.UniqueConstraint('entity_type', 'entity_id', 'date', name='unique_daily_attendance'),
        db.Index('idx_attendance_date', 'date'),
        db.Index('idx_attendance_entity', 'entity_type', 'entity_id')
    )

    def __repr__(self):
        return f'<Attendance {self.entity_type}-{self.entity_id} {self.date}>'

class FeeType(db.Model):
    """Fee types configuration"""
    __tablename__ = 'fee_type'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.Enum('MONTHLY', 'QUARTERLY', 'YEARLY', 'ONE_TIME', name='fee_frequency'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    transactions = db.relationship('FeeTransaction', backref='fee_type', lazy=True)

    def __repr__(self):
        return f'<FeeType {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'amount': float(self.amount),
            'frequency': self.frequency,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if hasattr(self, 'updated_at') and self.updated_at else None
        }
class FeeTransaction(db.Model, TimestampMixin):
    """Fee transactions for both students (fees) and staff (salary)"""
    __tablename__ = 'fee_transaction'

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.Enum('STUDENT', 'STAFF', name='fee_entity_types'), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    fee_type_id = db.Column(db.Integer, db.ForeignKey('fee_type.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    payment_date = db.Column(db.Date)
    payment_method = db.Column(db.Enum('CASH', 'CHEQUE', 'ONLINE', name='payment_methods'))
    transaction_status = db.Column(db.Enum('PENDING', 'PAID', 'OVERDUE', 'CANCELLED', name='transaction_status'), 
                                 nullable=False, default='PENDING')
    reference_number = db.Column(db.String(50))
    remarks = db.Column(db.Text)

    __table_args__ = (
        db.Index('idx_transaction_entity', 'entity_type', 'entity_id'),
        db.Index('idx_transaction_status', 'transaction_status')
    )

    def __repr__(self):
        return f'<FeeTransaction {self.entity_type}-{self.entity_id} {self.amount}>'

class Inventory(db.Model, TimestampMixin):
    """Inventory management"""
    __tablename__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.Enum('FURNITURE', 'ELECTRONICS', 'STATIONERY', 'SPORTS', 'OTHER', 
                                name='inventory_categories'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    unit = db.Column(db.String(20), nullable=False)
    minimum_quantity = db.Column(db.Integer, default=1)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    location = db.Column(db.String(100))
    description = db.Column(db.Text)
    last_purchased = db.Column(db.Date)
    unit_price = db.Column(db.Float)
    supplier_info = db.Column(db.String(255))
    
    # Relationships
    transactions = db.relationship('InventoryTransaction', backref='item', lazy=True)

    def __repr__(self):
        return f'<Inventory {self.name}>'

class InventoryTransaction(db.Model, TimestampMixin):
    """Inventory transaction history"""
    __tablename__ = 'inventory_transaction'

    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    transaction_type = db.Column(db.Enum('IN', 'OUT', 'ADJUST', name='inventory_transaction_types'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    reference = db.Column(db.String(100))
    transaction_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    performed_by = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    notes = db.Column(db.Text)

    def __repr__(self):
        return f'<InventoryTransaction {self.transaction_type} {self.quantity}>'

class Admin(db.Model, TimestampMixin):
    """Admin user model"""
    __tablename__ = 'admin'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    role = db.Column(db.Enum('SUPER_ADMIN', 'BRANCH_ADMIN', 'STAFF', name='admin_roles'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'))
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Admin {self.username}>'

class AuditLog(db.Model):
    """Audit logging for tracking changes"""
    __tablename__ = 'audit_log'

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.Enum('INSERT', 'UPDATE', 'DELETE', name='audit_actions'), nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))

    __table_args__ = (
        db.Index('idx_audit_entity', 'entity_type', 'entity_id'),
        db.Index('idx_audit_timestamp', 'changed_at')
    )

    def __repr__(self):
        return f'<AuditLog {self.action} {self.entity_type}-{self.entity_id}>'


class SchoolEvent(db.Model, TimestampMixin):
    """School event model for tracking holidays, functions, etc."""
    __tablename__ = 'school_event'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False)
    event_type = db.Column(db.Enum('ACADEMIC', 'CULTURAL', 'SPORTS', 'EXAM', 'OTHER', 
                                 name='event_types'), nullable=False)
    venue = db.Column(db.String(100))
    coordinator_id = db.Column(db.Integer, db.ForeignKey('staff.id'))
    is_holiday = db.Column(db.Boolean, default=False)
    participants = db.Column(db.String(255))  # Store as comma-separated class IDs
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    coordinator = db.relationship('Staff', backref='coordinated_events')

    def __repr__(self):
        return f'<Event {self.title} on {self.date}>'

    @property
    def participating_classes(self):
        """Get list of participating class IDs"""
        if not self.participants:
            return []
        return [int(id) for id in self.participants.split(',')]
