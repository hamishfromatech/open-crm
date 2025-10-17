from flask import Blueprint, request, jsonify, send_from_directory, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from app import db
from app.models import (Customer, Contact, Lead, Opportunity, Activity, Document, User,
                        RoleEnum, LeadStatusEnum, OpportunityStatusEnum, ActivityTypeEnum)
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

        return jsonify({'message': 'File uploaded successfully', 'document': _serialize_document(document)}), 201


@api_bp.route('/documents', methods=['GET'])
@login_required
def list_documents():
    """List documents optionally filtered by customer"""
    customer_id = request.args.get('customer_id', type=int)
    query = Document.query

    if customer_id:
        query = query.filter_by(customer_id=customer_id)

    if not (current_user.is_admin or current_user.is_manager):
        query = query.join(Document.customer).filter(Customer.assigned_user_id == current_user.id)

    documents = query.order_by(Document.created_at.desc()).all()
    return jsonify([_serialize_document(doc) for doc in documents])


@api_bp.route('/documents/<int:document_id>', methods=['GET'])
@login_required
def download_document(document_id):
    """Download a specific document"""
    document = Document.query.get_or_404(document_id)

    if document.customer and not (current_user.is_admin or current_user.is_manager):
        if document.customer.assigned_user_id != current_user.id:
            return jsonify({'error': 'Permission denied'}), 403

    directory = os.path.dirname(document.file_path)
    filename = os.path.basename(document.file_path)

    return send_from_directory(directory, filename, as_attachment=True, download_name=document.original_filename)


@api_bp.route('/documents/<int:document_id>', methods=['DELETE'])
@login_required
@role_required(RoleEnum.ADMIN.value, RoleEnum.MANAGER.value, RoleEnum.EMPLOYEE.value)
def delete_document(document_id):
    """Delete a document"""
    document = Document.query.get_or_404(document_id)

    if document.customer and not (current_user.is_admin or current_user.is_manager):
        if document.customer.assigned_user_id != current_user.id:
            return jsonify({'error': 'Permission denied'}), 403

    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
    except OSError:
        pass

    serialized = _serialize_document(document)
    db.session.delete(document)
    db.session.commit()

    return jsonify({'message': 'Document deleted successfully', 'document': serialized})

# CRUD API endpoints for Customer
@api_bp.route('/customers', methods=['GET'])
@login_required
def get_customers():
    """Get all customers"""
    if current_user.is_admin or current_user.is_manager:
        customers = Customer.query.all()
    else:
        customers = Customer.query.filter_by(assigned_user_id=current_user.id).all()
    return jsonify([_serialize_customer(c) for c in customers])

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

    return jsonify({'message': 'Customer created successfully', 'customer': _serialize_customer(customer)}), 201

@api_bp.route('/customers/<int:id>', methods=['GET'])
@login_required
def get_customer(id):
    """Get a specific customer"""
    customer = Customer.query.get_or_404(id)
    return jsonify({
        **_serialize_customer(customer)
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

    return jsonify({'message': 'Customer updated successfully', 'customer': _serialize_customer(customer)})

@api_bp.route('/customers/<int:id>', methods=['DELETE'])
@login_required
@role_required(RoleEnum.ADMIN.value, RoleEnum.MANAGER.value)
def delete_customer(id):
    """Delete a customer"""
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()

    return jsonify({'message': 'Customer deleted successfully', 'customer': _serialize_customer(customer)})

# Similar CRUD endpoints for other entities would go here
# For brevity, I'll add a few more key ones

# CRUD API endpoints for Contacts
def _serialize_contact(contact):
    return {
        'id': contact.id,
        'first_name': contact.first_name,
        'last_name': contact.last_name,
        'email': contact.email,
        'phone': contact.phone,
        'position': contact.position,
        'department': contact.department,
        'notes': contact.notes,
        'customer_id': contact.customer_id,
        'customer_name': contact.customer.name if contact.customer else None,
        'is_primary': contact.is_primary,
        'created_at': contact.created_at.isoformat() if contact.created_at else None
    }


def _coerce_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'y', 'on'}
    return default


def _serialize_document(document):
    return {
        'id': document.id,
        'filename': document.filename,
        'original_filename': document.original_filename,
        'file_size': document.file_size,
        'mime_type': document.mime_type,
        'customer_id': document.customer_id,
        'uploaded_by': document.uploaded_by,
        'uploaded_by_name': document.uploader.get_full_name() if document.uploader else None,
        'created_at': document.created_at.isoformat() if document.created_at else None,
        'description': document.description,
        'is_public': document.is_public
    }


def _parse_enum(value, enum_cls, default=None):
    if value is None:
        return default
    if isinstance(value, enum_cls):
        return value
    try:
        return enum_cls(value)
    except ValueError:
        try:
            return enum_cls[value]
        except KeyError:
            return default


def _parse_iso_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _serialize_customer(customer):
    return {
        'id': customer.id,
        'name': customer.name,
        'email': customer.email,
        'phone': customer.phone,
        'company': customer.company,
        'address': customer.address,
        'website': customer.website,
        'industry': customer.industry,
        'notes': customer.notes,
        'assigned_user_id': customer.assigned_user_id,
        'assigned_user': customer.assigned_user.get_full_name() if customer.assigned_user else None,
        'created_at': customer.created_at.isoformat() if customer.created_at else None,
        'updated_at': customer.updated_at.isoformat() if customer.updated_at else None
    }


def _serialize_lead(lead):
    return {
        'id': lead.id,
        'title': lead.title,
        'description': lead.description,
        'source': lead.source,
        'status': lead.status.value if lead.status else None,
        'value': lead.value,
        'probability': lead.probability,
        'customer_id': lead.customer_id,
        'customer': lead.customer.name if lead.customer else None,
        'assigned_user_id': lead.assigned_user_id,
        'assigned_user': lead.assigned_user.get_full_name() if lead.assigned_user else None,
        'expected_close_date': lead.expected_close_date.isoformat() if lead.expected_close_date else None,
        'created_at': lead.created_at.isoformat() if lead.created_at else None,
        'updated_at': lead.updated_at.isoformat() if lead.updated_at else None
    }


def _serialize_opportunity(opportunity):
    return {
        'id': opportunity.id,
        'name': opportunity.name,
        'description': opportunity.description,
        'amount': opportunity.amount,
        'probability': opportunity.probability,
        'status': opportunity.status.value if opportunity.status else None,
        'customer_id': opportunity.customer_id,
        'customer': opportunity.customer.name if opportunity.customer else None,
        'lead_id': opportunity.lead_id,
        'lead': opportunity.lead.title if opportunity.lead else None,
        'assigned_user_id': opportunity.assigned_user_id,
        'assigned_user': opportunity.assigned_user.get_full_name() if opportunity.assigned_user else None,
        'expected_close_date': opportunity.expected_close_date.isoformat() if opportunity.expected_close_date else None,
        'created_at': opportunity.created_at.isoformat() if opportunity.created_at else None,
        'updated_at': opportunity.updated_at.isoformat() if opportunity.updated_at else None,
        'closed_date': opportunity.closed_date.isoformat() if opportunity.closed_date else None
    }


def _serialize_activity(activity):
    return {
        'id': activity.id,
        'title': activity.title,
        'description': activity.description,
        'activity_type': activity.activity_type.value if activity.activity_type else None,
        'user_id': activity.user_id,
        'user': activity.user.get_full_name() if activity.user else None,
        'customer_id': activity.customer_id,
        'customer': activity.customer.name if activity.customer else None,
        'contact_id': activity.contact_id,
        'contact': activity.contact.get_full_name() if activity.contact else None,
        'lead_id': activity.lead_id,
        'lead': activity.lead.title if activity.lead else None,
        'opportunity_id': activity.opportunity_id,
        'opportunity': activity.opportunity.name if activity.opportunity else None,
        'due_date': activity.due_date.isoformat() if activity.due_date else None,
        'completed': activity.completed,
        'created_at': activity.created_at.isoformat() if activity.created_at else None
    }


@api_bp.route('/contacts', methods=['GET'])
@login_required
def get_contacts():
    """Get all contacts"""
    contacts = Contact.query.all()
    return jsonify([_serialize_contact(c) for c in contacts])

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
        is_primary=_coerce_bool(data.get('is_primary'), False)
    )

    db.session.add(contact)
    db.session.commit()

    return jsonify({'message': 'Contact created successfully', 'contact': _serialize_contact(contact)}), 201


@api_bp.route('/contacts/<int:id>', methods=['GET'])
@login_required
def get_contact(id):
    """Get a specific contact"""
    contact = Contact.query.get_or_404(id)
    return jsonify(_serialize_contact(contact))

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
    if 'customer_id' in data:
        contact.customer_id = data['customer_id']
    if 'is_primary' in data:
        contact.is_primary = _coerce_bool(data['is_primary'], contact.is_primary)

    db.session.commit()

    return jsonify({'message': 'Contact updated successfully', 'contact': _serialize_contact(contact)})

@api_bp.route('/contacts/<int:id>', methods=['DELETE'])
@login_required
@role_required(RoleEnum.ADMIN.value, RoleEnum.MANAGER.value)
def delete_contact(id):
    """Delete a contact"""
    contact = Contact.query.get_or_404(id)
    serialized = _serialize_contact(contact)
    db.session.delete(contact)
    db.session.commit()

    return jsonify({'message': 'Contact deleted successfully', 'contact': serialized})

@api_bp.route('/leads', methods=['GET'])
@login_required
def get_leads():
    """Get all leads"""
    leads = Lead.query.all()
    return jsonify([{
        'id': lead.id,
        'title': lead.title,
        'description': lead.description,
        'source': lead.source,
        'status': lead.status,
        'value': lead.value,
        'probability': lead.probability,
        'customer': lead.customer.name if lead.customer else None,
        'customer_id': lead.customer_id,
        'assigned_user': lead.assigned_user.get_full_name() if lead.assigned_user else None,
        'assigned_user_id': lead.assigned_user_id,
        'expected_close_date': lead.expected_close_date.isoformat() if lead.expected_close_date else None,
        'created_at': lead.created_at.isoformat() if getattr(lead, 'created_at', None) else None,
        'updated_at': lead.updated_at.isoformat() if getattr(lead, 'updated_at', None) else None
    } for lead in leads])

@api_bp.route('/leads', methods=['POST'])
@login_required
@role_required(RoleEnum.ADMIN.value, RoleEnum.MANAGER.value, RoleEnum.EMPLOYEE.value)
def create_lead():
    """Create a new lead"""
    data = request.get_json()

    lead = Lead(
        title=data['title'],
        description=data.get('description'),
        source=data.get('source'),
        status=data.get('status', 'new'),
        value=data.get('value'),
        probability=data.get('probability', 0),
        customer_id=data.get('customer_id'),
        assigned_user_id=data.get('assigned_user_id'),
        expected_close_date=datetime.fromisoformat(data['expected_close_date']) if data.get('expected_close_date') else None
    )

    db.session.add(lead)
    db.session.commit()

    return jsonify({'message': 'Lead created successfully', 'id': lead.id}), 201

@api_bp.route('/leads/<int:id>', methods=['PUT'])
@login_required
@role_required(RoleEnum.ADMIN.value, RoleEnum.MANAGER.value, RoleEnum.EMPLOYEE.value)
def update_lead(id):
    """Update a lead"""
    lead = Lead.query.get_or_404(id)
    data = request.get_json()

    lead.title = data.get('title', lead.title)
    lead.description = data.get('description', lead.description)
    lead.source = data.get('source', lead.source)
    lead.status = data.get('status', lead.status)
    lead.value = data.get('value', lead.value)
    lead.probability = data.get('probability', lead.probability)
    lead.expected_close_date = datetime.fromisoformat(data['expected_close_date']) if data.get('expected_close_date') else lead.expected_close_date

    db.session.commit()

    return jsonify({'message': 'Lead updated successfully'})

@api_bp.route('/leads/<int:id>', methods=['DELETE'])
@login_required
@role_required(RoleEnum.ADMIN.value, RoleEnum.MANAGER.value)
def delete_lead(id):
    """Delete a lead"""
    lead = Lead.query.get_or_404(id)
    db.session.delete(lead)
    db.session.commit()

    return jsonify({'message': 'Lead deleted successfully'})

@api_bp.route('/opportunities', methods=['GET'])
@login_required
def get_opportunities():
    """Get all opportunities"""
    opportunities = Opportunity.query.all()
    return jsonify([{
        'id': opportunity.id,
        'name': opportunity.name,
        'description': opportunity.description,
        'amount': opportunity.amount,
        'probability': opportunity.probability,
        'status': opportunity.status,
        'customer': opportunity.customer.name if opportunity.customer else None,
        'customer_id': opportunity.customer_id,
        'lead_id': opportunity.lead_id,
        'lead': opportunity.lead.name if opportunity.lead else None,
        'assigned_user': opportunity.assigned_user.get_full_name() if opportunity.assigned_user else None,
        'assigned_user_id': opportunity.assigned_user_id,
        'expected_close_date': opportunity.expected_close_date.isoformat() if opportunity.expected_close_date else None,
        'created_at': opportunity.created_at.isoformat() if getattr(opportunity, 'created_at', None) else None,
        'updated_at': opportunity.updated_at.isoformat() if getattr(opportunity, 'updated_at', None) else None,
        'closed_date': opportunity.closed_date.isoformat() if getattr(opportunity, 'closed_date', None) else None
    } for opportunity in opportunities])

@api_bp.route('/opportunities', methods=['POST'])
@login_required
@role_required(RoleEnum.ADMIN.value, RoleEnum.MANAGER.value, RoleEnum.EMPLOYEE.value)
def create_opportunity():
    """Create a new opportunity"""
    data = request.get_json()

    opportunity = Opportunity(
        name=data['name'],
        description=data.get('description'),
        amount=data['amount'],
        probability=data.get('probability', 0),
        status=data.get('status', 'open'),
        customer_id=data['customer_id'],
        lead_id=data.get('lead_id'),
        assigned_user_id=data.get('assigned_user_id'),
        expected_close_date=datetime.fromisoformat(data['expected_close_date']) if data.get('expected_close_date') else None
    )

    db.session.add(opportunity)
    db.session.commit()

    return jsonify({'message': 'Opportunity created successfully', 'id': opportunity.id}), 201

@api_bp.route('/opportunities/<int:id>', methods=['PUT'])
@login_required
@role_required(RoleEnum.ADMIN.value, RoleEnum.MANAGER.value, RoleEnum.EMPLOYEE.value)
def update_opportunity(id):
    """Update an opportunity"""
    opportunity = Opportunity.query.get_or_404(id)
    data = request.get_json()

    opportunity.name = data.get('name', opportunity.name)
    opportunity.description = data.get('description', opportunity.description)
    opportunity.amount = data.get('amount', opportunity.amount)
    opportunity.probability = data.get('probability', opportunity.probability)
    opportunity.status = data.get('status', opportunity.status)
    opportunity.expected_close_date = datetime.fromisoformat(data['expected_close_date']) if data.get('expected_close_date') else opportunity.expected_close_date
    opportunity.closed_date = datetime.utcnow() if data.get('status') in ['won', 'lost'] and not opportunity.closed_date else opportunity.closed_date

    db.session.commit()

    return jsonify({'message': 'Opportunity updated successfully'})

@api_bp.route('/opportunities/<int:id>', methods=['DELETE'])
@login_required
@role_required(RoleEnum.ADMIN.value, RoleEnum.MANAGER.value)
def delete_opportunity(id):
    """Delete an opportunity"""
    opportunity = Opportunity.query.get_or_404(id)
    db.session.delete(opportunity)
    db.session.commit()

    return jsonify({'message': 'Opportunity deleted successfully'})

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

@api_bp.route('/activities/<int:id>', methods=['PUT'])
@login_required
def update_activity(id):
    """Update an activity"""
    activity = Activity.query.get_or_404(id)

    # Only allow user to update their own activities or admins/managers to update any
    if not (current_user.is_admin or current_user.is_manager or activity.user_id == current_user.id):
        return jsonify({'error': 'Permission denied'}), 403

    data = request.get_json()

    activity.title = data.get('title', activity.title)
    activity.description = data.get('description', activity.description)
    activity.activity_type = data.get('activity_type', activity.activity_type)
    activity.due_date = datetime.fromisoformat(data['due_date']) if data.get('due_date') else activity.due_date
    activity.completed = data.get('completed', activity.completed)

    db.session.commit()

    return jsonify({'message': 'Activity updated successfully'})

@api_bp.route('/activities/<int:id>', methods=['DELETE'])
@login_required
def delete_activity(id):
    """Delete an activity"""
    activity = Activity.query.get_or_404(id)

    # Only allow user to delete their own activities or admins/managers to delete any
    if not (current_user.is_admin or current_user.is_manager or activity.user_id == current_user.id):
        return jsonify({'error': 'Permission denied'}), 403

    db.session.delete(activity)
    db.session.commit()

    return jsonify({'message': 'Activity deleted successfully'})

# Dashboard API endpoints
@api_bp.route('/dashboard/stats')
@login_required
def dashboard_stats():
    """Get dashboard statistics"""
    from sqlalchemy import func

    # Filter based on role
    if current_user.is_admin or current_user.is_manager:
        customer_count = Customer.query.count()
        lead_count = Lead.query.count()
        opportunity_count = Opportunity.query.count()
        total_opportunity_value = db.session.query(func.sum(Opportunity.amount)).scalar() or 0
    else:
        customer_count = Customer.query.filter_by(assigned_user_id=current_user.id).count()
        lead_count = Lead.query.filter_by(assigned_user_id=current_user.id).count()
        opportunity_count = Opportunity.query.filter_by(assigned_user_id=current_user.id).count()
        total_opportunity_value = db.session.query(func.sum(Opportunity.amount))\
            .filter_by(assigned_user_id=current_user.id).scalar() or 0

    return jsonify({
        'customer_count': customer_count,
        'lead_count': lead_count,
        'opportunity_count': opportunity_count,
        'total_opportunity_value': float(total_opportunity_value)
    })

@api_bp.route('/dashboard/recent-activities')
@login_required
def recent_activities():
    """Get recent activities for dashboard"""
    activities = Activity.query.filter_by(user_id=current_user.id)\
        .order_by(Activity.created_at.desc()).limit(10).all()

    return jsonify([{
        'id': a.id,
        'title': a.title,
        'activity_type': a.activity_type.value,
        'created_at': a.created_at.isoformat(),
        'customer': a.customer.name if a.customer else None,
        'contact': f"{a.contact.first_name} {a.contact.last_name}" if a.contact else None
    } for a in activities])

# Error handlers
@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500
