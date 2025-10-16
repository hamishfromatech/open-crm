from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from functools import wraps
from app.models import RoleEnum

main_bp = Blueprint('main', __name__)

def role_required(*roles):
    """Decorator to require specific roles for access"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))

            if current_user.role.name not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('main.dashboard'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator

@main_bp.route('/')
def index():
    """Home page - redirect to dashboard if logged in, login if not"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    from app.models import Customer, Lead, Opportunity, Activity

    # Get counts for dashboard
    customer_count = Customer.query.count()
    lead_count = Lead.query.count()
    opportunity_count = Opportunity.query.count()
    activity_count = Activity.query.filter_by(user_id=current_user.id).count()

    # Recent activities
    recent_activities = Activity.query.filter_by(user_id=current_user.id)\
        .order_by(Activity.created_at.desc()).limit(5).all()

    return render_template('main/dashboard.html',
                         customer_count=customer_count,
                         lead_count=lead_count,
                         opportunity_count=opportunity_count,
                         activity_count=activity_count,
                         recent_activities=recent_activities,
                         title='Dashboard')

@main_bp.route('/customers')
@login_required
@role_required(RoleEnum.ADMIN.value, RoleEnum.MANAGER.value, RoleEnum.EMPLOYEE.value)
def customers():
    """Customer list page"""
    from app.models import Customer

    # Filter customers based on role
    if current_user.is_admin or current_user.is_manager:
        customers = Customer.query.all()
    else:
        customers = Customer.query.filter_by(assigned_user_id=current_user.id).all()

    return render_template('main/customers.html', customers=customers, title='Customers')

@main_bp.route('/leads')
@login_required
@role_required(RoleEnum.ADMIN.value, RoleEnum.MANAGER.value, RoleEnum.EMPLOYEE.value)
def leads():
    """Lead list page"""
    from app.models import Lead

    # Filter leads based on role
    if current_user.is_admin or current_user.is_manager:
        leads = Lead.query.all()
    else:
        leads = Lead.query.filter_by(assigned_user_id=current_user.id).all()

    return render_template('main/leads.html', leads=leads, title='Leads')

@main_bp.route('/opportunities')
@login_required
@role_required(RoleEnum.ADMIN.value, RoleEnum.MANAGER.value, RoleEnum.EMPLOYEE.value)
def opportunities():
    """Opportunity list page"""
    from app.models import Opportunity

    # Filter opportunities based on role
    if current_user.is_admin or current_user.is_manager:
        opportunities = Opportunity.query.all()
    else:
        opportunities = Opportunity.query.filter_by(assigned_user_id=current_user.id).all()

    return render_template('main/opportunities.html', opportunities=opportunities, title='Opportunities')

@main_bp.route('/activities')
@login_required
def activities():
    """Activity list page"""
    from app.models import Activity

    activities = Activity.query.filter_by(user_id=current_user.id)\
        .order_by(Activity.created_at.desc()).all()

    return render_template('main/activities.html', activities=activities, title='Activities')
