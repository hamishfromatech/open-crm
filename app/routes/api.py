from flask import Blueprint, request, jsonify, send_from_directory, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from app import db, documents
from app.models import Customer, Contact, Lead, Opportunity, Activity, Document, RoleEnum
from app.routes.main import role_required

api_bp = Blueprint('api', __name__)

# File upload endpoint
@api_bp.route('/upload', methods=['POST'])
@login_required
@role_required(RoleEnum.ADMIN.value, RoleEnum.MANAGER.value, RoleEnum.EMPLOYEE.value)
def upload_file():
    """Upload a file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    customer_id = request.form.get('customer_id')

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        # Validate file extension
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

        if file_ext not in current_app.config['ALLOWED_EXTENSIONS']:
            return jsonify({'error': 'File type not allowed'}), 400

        # Save file
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)

        # Create document record
        document = Document(
            filename=filename,
            original_filename=file.filename,
            file_path=upload_path,
            file_size=os.path.getsize(upload_path),
            mime_type=file.mimetype,
            customer_id=customer_id,
            uploaded_by=current_user.id
        )

        db.session.add(document)
        db.session.commit()

        return jsonify({
            'message': 'File uploaded successfully',
            'document_id': document.id,
            'filename': filename
        }), 201

# CRUD API endpoints for Customer
@api_bp.route('/customers', methods=['GET'])
@login_required
def get_customers():
    """Get all customers"""
    customers = Customer.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'email': c.email,
        'company': c.company,
        'phone': c.phone,
        'assigned_user': c.assigned_user.get_full_name() if c.assigned_user else None
    } for c in customers])

@api_bp.route('/customers', methods=['POST'])
@login_required
@role_required(RoleEnum.ADMIN.value, RoleEnum.MANAGER.value)
def create_customer():
    """Create a new customer"""
    data = request.get_json()

    customer = Customer(
        name=data['name'],
        email=data.get('email'),
        phone=data.get('phone'),
        company=data.get('company'),
        address=data.get('address'),
        website=data.get('website'),
        industry=data.get('industry'),
        notes=data.get('notes'),
        assigned_user_id=data.get('assigned_user_id')
    )

    db.session.add(customer)
    db.session.commit()

    return jsonify({'message': 'Customer created successfully', 'id': customer.id}), 201

@api_bp.route('/customers/<int:id>', methods=['GET'])
@login_required
def get_customer(id):
    """Get a specific customer"""
    customer = Customer.query.get_or_404(id)
    return jsonify({
        'id': customer.id,
        'name': customer.name,
        'email': customer.email,
        'phone': customer.phone,
        'company': customer.company,
        'address': customer.address,
        'website': customer.website,
        'industry': customer.industry,
        'notes': customer.notes,
        'assigned_user_id': customer.assigned_user_id
    })

@api_bp.route('/customers/<int:id>', methods=['PUT'])
@login_required
@role_required(RoleEnum.ADMIN.value, RoleEnum.MANAGER.value)
def update_customer(id):
    """Update a customer"""
    customer = Customer.query.get_or_404(id)
    data = request.get_json()

    customer.name = data.get('name', customer.name)
    customer.email = data.get('email', customer.email)
    customer.phone = data.get('phone', customer.phone)
    customer.company = data.get('company', customer.company)
    customer.address = data.get('address', customer.address)
    customer.website = data.get('website', customer.website)
    customer.industry = data.get('industry', customer.industry)
    customer.notes = data.get('notes', customer.notes)
    customer.assigned_user_id = data.get('assigned_user_id', customer.assigned_user_id)

    db.session.commit()

    return jsonify({'message': 'Customer updated successfully'})

@api_bp.route('/customers/<int:id>', methods=['DELETE'])
@login_required
@role_required(RoleEnum.ADMIN.value, RoleEnum.MANAGER.value)
def delete_customer(id):
    """Delete a customer"""
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()

    return jsonify({'message': 'Customer deleted successfully'})

# Similar CRUD endpoints for other entities would go here
# For brevity, I'll add a few more key ones

# CRUD API endpoints for Contacts
@api_bp.route('/contacts', methods=['GET'])
@login_required
def get_contacts():
    """Get all contacts"""
    contacts = Contact.query.all()
    return jsonify([{
        'id': c.id,
        'first_name': c.first_name,
        'last_name': c.last_name,
        'email': c.email,
        'phone': c.phone,
        'position': c.position,
        'customer': c.customer.name if c.customer else None
    } for c in contacts])

@api_bp.route('/contacts', methods=['POST'])
@login_required
@role_required(RoleEnum.ADMIN.value, RoleEnum.MANAGER.value, RoleEnum.EMPLOYEE.value)
def create_contact():
    """Create a new contact"""
    data = request.get_json()

    contact = Contact(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data.get('email'),
        phone=data.get('phone'),
        position=data.get('position'),
        department=data.get('department'),
        notes=data.get('notes'),
        customer_id=data['customer_id'],
        is_primary=data.get('is_primary', False)
    )

    db.session.add(contact)
    db.session.commit()

    return jsonify({'message': 'Contact created successfully', 'id': contact.id}), 201

@api_bp.route('/contacts/<int:id>', methods=['PUT'])
@login_required
@role_required(RoleEnum.ADMIN.value, RoleEnum.MANAGER.value, RoleEnum.EMPLOYEE.value)
def update_contact(id):
    """Update a contact"""
    contact = Contact.query.get_or_404(id)
    data = request.get_json()

    contact.first_name = data.get('first_name', contact.first_name)
    contact.last_name = data.get('last_name', contact.last_name)
    contact.email = data.get('email', contact.email)
    contact.phone = data.get('phone', contact.phone)
    contact.position = data.get('position', contact.position)
    contact.department = data.get('department', contact.department)
    contact.notes = data.get('notes', contact.notes)
    contact.is_primary = data.get('is_primary', contact.is_primary)

    db.session.commit()

    return jsonify({'message': 'Contact updated successfully'})

@api_bp.route('/contacts/<int:id>', methods=['DELETE'])
@login_required
@role_required(RoleEnum.ADMIN.value, RoleEnum.MANAGER.value)
def delete_contact(id):
    """Delete a contact"""
    contact = Contact.query.get_or_404(id)
    db.session.delete(contact)
    db.session.commit()

    return jsonify({'message': 'Contact deleted successfully'})

@api_bp.route('/leads', methods=['GET'])
@login_required
def get_leads():
    """Get all leads"""
    leads = Lead.query.all()
    return jsonify([{
        'id': l.id,
        'title': l.title,
        'status': l.status.value,
        'value': l.value,
        'customer': l.customer.name if l.customer else None,
        'assigned_user': l.assigned_user.get_full_name() if l.assigned_user else None
    } for l in leads])

@api_bp.route('/opportunities', methods=['GET'])
@login_required
def get_opportunities():
    """Get all opportunities"""
    opportunities = Opportunity.query.all()
    return jsonify([{
        'id': o.id,
        'name': o.name,
        'amount': o.amount,
        'status': o.status.value,
        'probability': o.probability,
        'customer': o.customer.name if o.customer else None,
        'assigned_user': o.assigned_user.get_full_name() if o.assigned_user else None
    } for o in opportunities])

@api_bp.route('/activities', methods=['GET'])
@login_required
def get_activities():
    """Get user's activities"""
    activities = Activity.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': a.id,
        'title': a.title,
        'description': a.description,
        'activity_type': a.activity_type.value,
        'created_at': a.created_at.isoformat()
    } for a in activities])

@api_bp.route('/activities', methods=['POST'])
@login_required
def create_activity():
    """Create a new activity"""
    data = request.get_json()

    activity = Activity(
        title=data['title'],
        description=data.get('description'),
        activity_type=data['activity_type'],
        user_id=current_user.id,
        customer_id=data.get('customer_id'),
        contact_id=data.get('contact_id'),
        lead_id=data.get('lead_id'),
        opportunity_id=data.get('opportunity_id'),
        due_date=datetime.fromisoformat(data['due_date']) if data.get('due_date') else None
    )

    db.session.add(activity)
    db.session.commit()

    return jsonify({'message': 'Activity created successfully', 'id': activity.id}), 201

# File serving endpoint
@api_bp.route('/files/<filename>')
@login_required
def get_file(filename):
    """Serve uploaded files"""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
