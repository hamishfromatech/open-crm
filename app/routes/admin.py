from datetime import datetime, timedelta

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import (Activity, Customer, Lead, Opportunity, OpportunityStatusEnum,
                        RoleEnum, User, UserRole)
from app.routes.main import role_required

admin_bp = Blueprint('admin_panel', __name__, url_prefix='/admin')


def _format_label(value: str) -> str:
    return value.replace('_', ' ').title()


def _serialize_user(user: User) -> dict:
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.get_full_name(),
        'role': user.role.name if user.role else None,
        'role_label': _format_label(user.role.name) if user.role else None,
        'is_active': user.is_active,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'last_login': user.last_login.isoformat() if user.last_login else None,
    }


def _gather_metrics() -> dict:
    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)

    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    new_users = User.query.filter(User.created_at >= thirty_days_ago).count()

    admin_count = User.query.join(UserRole).filter(UserRole.name == RoleEnum.ADMIN.value).count()
    manager_count = User.query.join(UserRole).filter(UserRole.name == RoleEnum.MANAGER.value).count()
    employee_count = User.query.join(UserRole).filter(UserRole.name == RoleEnum.EMPLOYEE.value).count()

    customer_count = Customer.query.count()
    lead_count = Lead.query.count()
    opportunity_count = Opportunity.query.count()
    open_opportunities = Opportunity.query.filter_by(status=OpportunityStatusEnum.OPEN).count()
    activity_count = Activity.query.count()
    recent_activities = Activity.query.order_by(Activity.created_at.desc()).limit(5).all()

    recent_logins = User.query.filter(User.last_login.isnot(None)) \
        .order_by(User.last_login.desc()).limit(5).all()

    return {
        'generated_at': now.isoformat(),
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': total_users - active_users,
        'new_users_30_days': new_users,
        'admin_count': admin_count,
        'manager_count': manager_count,
        'employee_count': employee_count,
        'customer_count': customer_count,
        'lead_count': lead_count,
        'opportunity_count': opportunity_count,
        'open_opportunities': open_opportunities,
        'activity_count': activity_count,
        'recent_logins': [
            {
                'id': user.id,
                'full_name': user.get_full_name(),
                'role': user.role.name if user.role else None,
                'role_label': _format_label(user.role.name) if user.role else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
            }
            for user in recent_logins
        ],
        'recent_activities': [
            {
                'id': activity.id,
                'title': activity.title,
                'type': activity.activity_type.value if activity.activity_type else None,
                'user': activity.user.get_full_name() if activity.user else None,
                'created_at': activity.created_at.isoformat() if activity.created_at else None,
            }
            for activity in recent_activities
        ],
    }


@admin_bp.route('/dashboard')
@login_required
@role_required(RoleEnum.ADMIN.value)
def dashboard():
    metrics = _gather_metrics()
    users = [_serialize_user(user) for user in User.query.order_by(User.created_at.desc()).all()]
    roles = [
        {
            'id': role.id,
            'name': role.name,
            'label': _format_label(role.name),
        }
        for role in UserRole.query.order_by(UserRole.name).all()
    ]

    return render_template(
        'admin/dashboard.html',
        metrics=metrics,
        users=users,
        roles=roles,
        title='Admin Dashboard',
    )


@admin_bp.route('/metrics', methods=['GET'])
@login_required
@role_required(RoleEnum.ADMIN.value)
def metrics():
    return jsonify(_gather_metrics())


@admin_bp.route('/users', methods=['GET'])
@login_required
@role_required(RoleEnum.ADMIN.value)
def list_users():
    return jsonify({'users': [_serialize_user(user) for user in User.query.order_by(User.created_at.desc()).all()]})


@admin_bp.route('/users', methods=['POST'])
@login_required
@role_required(RoleEnum.ADMIN.value)
def create_user():
    payload = request.get_json(silent=True) or {}
    required_fields = ['username', 'email', 'first_name', 'last_name', 'password', 'role']

    missing = [field for field in required_fields if not payload.get(field)]
    if missing:
        return jsonify({'error': f"Missing required fields: {', '.join(missing)}"}), 400

    role = UserRole.query.filter_by(name=payload['role']).first()
    if not role:
        return jsonify({'error': 'Invalid role supplied.'}), 400

    if User.query.filter((User.username == payload['username']) | (User.email == payload['email'])).first():
        return jsonify({'error': 'Username or email already exists.'}), 409

    user = User(
        username=payload['username'],
        email=payload['email'],
        first_name=payload['first_name'],
        last_name=payload['last_name'],
        role=role,
        is_active=payload.get('is_active', True),
    )
    user.set_password(payload['password'])

    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Unable to create user with provided details.'}), 400

    return jsonify({'message': 'User created successfully.', 'user': _serialize_user(user)}), 201


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
@role_required(RoleEnum.ADMIN.value)
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    payload = request.get_json(silent=True) or {}

    username = payload.get('username')
    email = payload.get('email')
    first_name = payload.get('first_name')
    last_name = payload.get('last_name')
    role_name = payload.get('role')
    password = payload.get('password')
    is_active = payload.get('is_active')

    if username and username != user.username and User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already in use.'}), 409
    if email and email != user.email and User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already in use.'}), 409

    if username:
        user.username = username
    if email:
        user.email = email
    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name
    if role_name:
        role = UserRole.query.filter_by(name=role_name).first()
        if not role:
            return jsonify({'error': 'Invalid role supplied.'}), 400
        user.role = role
    if isinstance(is_active, bool):
        user.is_active = is_active
    if password:
        user.set_password(password)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Unable to update user with provided details.'}), 400

    return jsonify({'message': 'User updated successfully.', 'user': _serialize_user(user)})


@admin_bp.route('/users/<int:user_id>/status', methods=['PATCH'])
@login_required
@role_required(RoleEnum.ADMIN.value)
def update_user_status(user_id):
    user = User.query.get_or_404(user_id)
    payload = request.get_json(silent=True) or {}

    if 'is_active' not in payload:
        return jsonify({'error': 'is_active field is required.'}), 400

    user.is_active = bool(payload['is_active'])
    db.session.commit()

    return jsonify({'message': 'User status updated successfully.', 'user': _serialize_user(user)})
