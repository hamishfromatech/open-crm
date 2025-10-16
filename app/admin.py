from flask import redirect, url_for, request
from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from wtforms import validators
from app.models import User, UserRole, Customer, Contact, Lead, Opportunity, Activity, Document, RoleEnum

class SecureModelView(ModelView):
    """Base model view with role-based access control"""

    def is_accessible(self):
        """Check if user can access admin"""
        return current_user.is_authenticated and (
            current_user.is_admin or current_user.is_manager
        )

    def inaccessible_callback(self, name, **kwargs):
        """Redirect to login or dashboard if access denied"""
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        return redirect(url_for('main.dashboard'))

class AdminOnlyModelView(ModelView):
    """Model view accessible only to admins"""

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        return redirect(url_for('main.dashboard'))

class UserAdmin(SecureModelView):
    """Admin view for users"""
    column_list = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'last_login')
    column_searchable_list = ('username', 'email', 'first_name', 'last_name')
    column_filters = ('role', 'is_active')
    form_columns = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')

    def on_model_change(self, form, model, is_created):
        """Hash password when creating/updating user"""
        if 'password' in form.data and form.data['password']:
            model.set_password(form.data['password'])

class RoleAdmin(AdminOnlyModelView):
    """Admin view for roles"""
    column_list = ('name', 'description', 'users')
    form_columns = ('name', 'description', 'permissions')

class CustomerAdmin(SecureModelView):
    """Admin view for customers"""
    column_list = ('name', 'email', 'company', 'phone', 'assigned_user', 'created_at')
    column_searchable_list = ('name', 'email', 'company')
    column_filters = ('assigned_user', 'created_at')
    form_columns = ('name', 'email', 'phone', 'company', 'address', 'website',
                   'industry', 'notes', 'assigned_user')

class ContactAdmin(SecureModelView):
    """Admin view for contacts"""
    column_list = ('first_name', 'last_name', 'email', 'phone', 'position', 'customer')
    column_searchable_list = ('first_name', 'last_name', 'email')
    form_columns = ('first_name', 'last_name', 'email', 'phone', 'position',
                   'department', 'notes', 'customer', 'is_primary')

class LeadAdmin(SecureModelView):
    """Admin view for leads"""
    column_list = ('title', 'status', 'value', 'probability', 'customer', 'assigned_user')
    column_searchable_list = ('title',)
    column_filters = ('status', 'assigned_user', 'customer')
    form_columns = ('title', 'description', 'source', 'status', 'value',
                   'probability', 'customer', 'assigned_user', 'expected_close_date')

class OpportunityAdmin(SecureModelView):
    """Admin view for opportunities"""
    column_list = ('name', 'amount', 'probability', 'status', 'customer', 'assigned_user')
    column_searchable_list = ('name',)
    column_filters = ('status', 'assigned_user', 'customer')
    form_columns = ('name', 'description', 'amount', 'probability', 'status',
                   'customer', 'lead', 'assigned_user', 'expected_close_date')

class ActivityAdmin(SecureModelView):
    """Admin view for activities"""
    column_list = ('title', 'activity_type', 'user', 'customer', 'created_at')
    column_searchable_list = ('title',)
    column_filters = ('activity_type', 'user', 'customer', 'completed')
    form_columns = ('title', 'description', 'activity_type', 'user', 'customer',
                   'contact', 'lead', 'opportunity', 'due_date', 'completed')

class DocumentAdmin(SecureModelView):
    """Admin view for documents"""
    column_list = ('filename', 'original_filename', 'file_size', 'customer', 'uploaded_by', 'created_at')
    column_searchable_list = ('filename', 'original_filename')
    form_columns = ('filename', 'customer', 'description', 'is_public')

    def _list_thumbnail(self, context, model, name):
        """Show file type icon"""
        if model.filename:
            return f'<i class="fa fa-file"></i> {model.filename}'
        return ''

class SecureAdminIndexView(AdminIndexView):
    """Secure admin index view"""

    @expose('/')
    def index(self):
        """Admin dashboard"""
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))

        if not (current_user.is_admin or current_user.is_manager):
            return redirect(url_for('main.dashboard'))

        return super(SecureAdminIndexView, self).index()

def init_admin_views(admin_instance):
    """Initialize Flask-Admin views"""
    # Import db from the main app module
    from app import db

    # Add model views with appropriate permissions
    admin_instance.add_view(UserAdmin(User, db.session, category='Users'))
    admin_instance.add_view(RoleAdmin(UserRole, db.session, category='Users'))

    admin_instance.add_view(CustomerAdmin(Customer, db.session, category='CRM'))
    admin_instance.add_view(ContactAdmin(Contact, db.session, category='CRM'))
    admin_instance.add_view(LeadAdmin(Lead, db.session, category='CRM'))
    admin_instance.add_view(OpportunityAdmin(Opportunity, db.session, category='CRM'))
    admin_instance.add_view(ActivityAdmin(Activity, db.session, category='CRM'))
    admin_instance.add_view(DocumentAdmin(Document, db.session, category='CRM'))

    # Set admin index view
    admin_instance._set_admin_index_view(SecureAdminIndexView(name='Admin'))
