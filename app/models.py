from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db
import enum

class RoleEnum(enum.Enum):
    ADMIN = 'admin'
    MANAGER = 'manager'
    EMPLOYEE = 'employee'

class LeadStatusEnum(enum.Enum):
    NEW = 'new'
    CONTACTED = 'contacted'
    QUALIFIED = 'qualified'
    PROPOSAL = 'proposal'
    NEGOTIATION = 'negotiation'
    CLOSED_WON = 'closed_won'
    CLOSED_LOST = 'closed_lost'

class OpportunityStatusEnum(enum.Enum):
    OPEN = 'open'
    WON = 'won'
    LOST = 'lost'

class ActivityTypeEnum(enum.Enum):
    CALL = 'call'
    EMAIL = 'email'
    MEETING = 'meeting'
    NOTE = 'note'
    TASK = 'task'

class UserRole(db.Model):
    """Role model for role-based access control"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    permissions = db.Column(db.Text)  # JSON string of permissions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    users = db.relationship('User', back_populates='role')

    def __repr__(self):
        return f'<UserRole {self.name}>'

class User(db.Model, UserMixin):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    role_id = db.Column(db.Integer, db.ForeignKey('user_role.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    role = db.relationship('UserRole', back_populates='users')
    customers = db.relationship('Customer', back_populates='assigned_user')
    leads = db.relationship('Lead', back_populates='assigned_user')
    opportunities = db.relationship('Opportunity', back_populates='assigned_user')
    activities = db.relationship('Activity', back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_admin(self):
        return self.role.name == RoleEnum.ADMIN.value

    @property
    def is_manager(self):
        return self.role.name == RoleEnum.MANAGER.value

    @property
    def is_employee(self):
        return self.role.name == RoleEnum.EMPLOYEE.value

    def __repr__(self):
        return f'<User {self.username}>'

class Customer(db.Model):
    """Customer model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    company = db.Column(db.String(255))
    address = db.Column(db.Text)
    website = db.Column(db.String(255))
    industry = db.Column(db.String(100))
    notes = db.Column(db.Text)
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assigned_user = db.relationship('User', back_populates='customers')
    contacts = db.relationship('Contact', back_populates='customer')
    leads = db.relationship('Lead', back_populates='customer')
    opportunities = db.relationship('Opportunity', back_populates='customer')
    documents = db.relationship('Document', back_populates='customer')

    def __repr__(self):
        return f'<Customer {self.name}>'

class Contact(db.Model):
    """Contact model for customer contacts"""
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    position = db.Column(db.String(100))
    department = db.Column(db.String(100))
    notes = db.Column(db.Text)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    customer = db.relationship('Customer', back_populates='contacts')
    activities = db.relationship('Activity', back_populates='contact')

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f'<Contact {self.get_full_name()}>'

class Lead(db.Model):
    """Lead model"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    source = db.Column(db.String(100))  # website, referral, cold call, etc.
    status = db.Column(db.Enum(LeadStatusEnum), default=LeadStatusEnum.NEW)
    value = db.Column(db.Float)  # Potential value
    probability = db.Column(db.Integer, default=0)  # Percentage 0-100
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    expected_close_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = db.relationship('Customer', back_populates='leads')
    assigned_user = db.relationship('User', back_populates='leads')
    opportunities = db.relationship('Opportunity', back_populates='lead')
    activities = db.relationship('Activity', back_populates='lead')

    def __repr__(self):
        return f'<Lead {self.title}>'

class Opportunity(db.Model):
    """Opportunity/Sales Opportunity model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Float, nullable=False)
    probability = db.Column(db.Integer, default=0)  # Percentage 0-100
    status = db.Column(db.Enum(OpportunityStatusEnum), default=OpportunityStatusEnum.OPEN)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    expected_close_date = db.Column(db.DateTime)
    closed_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = db.relationship('Customer', back_populates='opportunities')
    lead = db.relationship('Lead', back_populates='opportunities')
    assigned_user = db.relationship('User', back_populates='opportunities')
    activities = db.relationship('Activity', back_populates='opportunity')

    def __repr__(self):
        return f'<Opportunity {self.name}>'

class Activity(db.Model):
    """Activity/Note model for tracking interactions"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    activity_type = db.Column(db.Enum(ActivityTypeEnum), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'))
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunity.id'))
    due_date = db.Column(db.DateTime)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='activities')
    customer = db.relationship('Customer')
    contact = db.relationship('Contact', back_populates='activities')
    lead = db.relationship('Lead', back_populates='activities')
    opportunity = db.relationship('Opportunity', back_populates='activities')

    def __repr__(self):
        return f'<Activity {self.title}>'

class Document(db.Model):
    """Document model for file uploads"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # Size in bytes
    mime_type = db.Column(db.String(100))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.String(500))
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    customer = db.relationship('Customer', back_populates='documents')
    uploader = db.relationship('User')

    def __repr__(self):
        return f'<Document {self.filename}>'
