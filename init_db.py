#!/usr/bin/env python3
"""
Database initialization script for CRM
"""
from app import create_app, db
from app.models import User, UserRole, RoleEnum
from werkzeug.security import generate_password_hash

def init_database():
    """Initialize database with default roles and admin user"""
    app = create_app()

    with app.app_context():
        # Create roles if they don't exist
        roles = {}
        for role_enum in RoleEnum:
            role = UserRole.query.filter_by(name=role_enum.value).first()
            if not role:
                role = UserRole(
                    name=role_enum.value,
                    description=f'{role_enum.value.title()} role'
                )
                db.session.add(role)
                print(f'Created role: {role_enum.value}')
            roles[role_enum.value] = role

        # Create admin user if it doesn't exist
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@crm.com',
                first_name='System',
                last_name='Administrator',
                role=roles[RoleEnum.ADMIN.value],
                is_active=True
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            print('Created admin user: admin/admin123')

        # Create sample manager and employee users
        manager_user = User.query.filter_by(username='manager').first()
        if not manager_user:
            manager_user = User(
                username='manager',
                email='manager@crm.com',
                first_name='John',
                last_name='Manager',
                role=roles[RoleEnum.MANAGER.value],
                is_active=True
            )
            manager_user.set_password('manager123')
            db.session.add(manager_user)
            print('Created manager user: manager/manager123')

        employee_user = User.query.filter_by(username='employee').first()
        if not employee_user:
            employee_user = User(
                username='employee',
                email='employee@crm.com',
                first_name='Jane',
                last_name='Employee',
                role=roles[RoleEnum.EMPLOYEE.value],
                is_active=True
            )
            employee_user.set_password('employee123')
            db.session.add(employee_user)
            print('Created employee user: employee/employee123')

        db.session.commit()
        print('Database initialized successfully!')

if __name__ == '__main__':
    init_database()
