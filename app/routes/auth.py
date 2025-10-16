from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import db
from app.models import User, UserRole, RoleEnum
from app.forms import LoginForm, RegisterForm, UserForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact an administrator.', 'danger')
                return redirect(url_for('auth.login'))

            user.last_login = datetime.now()
            db.session.commit()
            login_user(user, remember=form.remember_me.data)

            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.dashboard')

            flash(f'Welcome back, {user.get_full_name()}!', 'success')
            return redirect(next_page)
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html', form=form, title='Sign In')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """User registration (admin only)"""
    if not current_user.is_admin:
        flash('You do not have permission to register new users.', 'danger')
        return redirect(url_for('main.dashboard'))

    form = RegisterForm()

    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('A user with this email already exists.', 'danger')
            return redirect(url_for('auth.register'))

        # Get or create role
        role = UserRole.query.filter_by(name=form.role.data).first()
        if not role:
            flash('Invalid role selected.', 'danger')
            return redirect(url_for('auth.register'))

        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role=role,
            is_active=True
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash(f'User {user.get_full_name()} has been created successfully.', 'success')
        return redirect(url_for('admin.user_list'))

    return render_template('auth/register.html', form=form, title='Register User')

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management"""
    form = UserForm(obj=current_user)

    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.email = form.email.data

        if form.password.data:
            current_user.set_password(form.password.data)

        db.session.commit()
        flash('Your profile has been updated successfully.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html', form=form, title='Profile')
