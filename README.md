# Flask CRM Application

A comprehensive Customer Relationship Management (CRM) system built with Flask, SQLAlchemy, and Flask-Admin.

## Features

- **User Management**: Multi-role authentication system (Admin, Manager, Employee)
- **Customer Management**: Full CRUD operations for customers and contacts
- **Lead Management**: Track and manage sales leads
- **Opportunity Management**: Handle sales opportunities and pipeline
- **Activity Tracking**: Log and track customer interactions
- **File Uploads**: Secure document management with local file storage
- **Role-Based Access Control**: Different permissions based on user roles
- **Admin Interface**: Flask-Admin powered administrative interface
- **RESTful API**: Complete API for frontend integration
- **Dashboard**: Real-time statistics and recent activities

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/hamishfromatech/open-crm.git
   cd open-crm
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize the database**
   ```bash
   python init_db.py
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

## Default Users

After running `init_db.py`, you can log in with these default accounts:

- **Admin**: admin@crm.com / admin123
- **Manager**: manager@crm.com / manager123
- **Employee**: employee@crm.com / employee123

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `GET /auth/profile` - Get user profile

### Customers
- `GET /api/customers` - List all customers
- `POST /api/customers` - Create new customer (Admin/Manager only)
- `GET /api/customers/<id>` - Get specific customer
- `PUT /api/customers/<id>` - Update customer (Admin/Manager only)
- `DELETE /api/customers/<id>` - Delete customer (Admin/Manager only)

### Contacts
- `GET /api/contacts` - List all contacts
- `POST /api/contacts` - Create new contact
- `PUT /api/contacts/<id>` - Update contact
- `DELETE /api/contacts/<id>` - Delete contact (Admin/Manager only)

### Leads
- `GET /api/leads` - List all leads
- `POST /api/leads` - Create new lead
- `PUT /api/leads/<id>` - Update lead
- `DELETE /api/leads/<id>` - Delete lead (Admin/Manager only)

### Opportunities
- `GET /api/opportunities` - List all opportunities
- `POST /api/opportunities` - Create new opportunity
- `PUT /api/opportunities/<id>` - Update opportunity
- `DELETE /api/opportunities/<id>` - Delete opportunity (Admin/Manager only)

### Activities
- `GET /api/activities` - List user's activities
- `POST /api/activities` - Create new activity
- `PUT /api/activities/<id>` - Update activity
- `DELETE /api/activities/<id>` - Delete activity

### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics
- `GET /api/dashboard/recent-activities` - Get recent activities

### File Upload
- `POST /api/upload` - Upload file

## Role Permissions

- **Admin**: Full access to all features and user management
- **Manager**: Access to all CRM features, can manage users
- **Employee**: Can view and manage assigned customers/leads/opportunities

## Configuration

The application uses the following configuration options in `.env`:

```env
FLASK_APP=run.py
FLASK_ENV=development
DATABASE_URL=sqlite:///crm.db
SECRET_KEY=your-secret-key-here
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216
```

## Database Models

- **User**: Authentication and user management
- **UserRole**: Role definitions (admin, manager, employee)
- **Customer**: Customer information and relationships
- **Contact**: Contact persons for customers
- **Lead**: Sales leads with status tracking
- **Opportunity**: Sales opportunities with value and probability
- **Activity**: Customer interaction tracking
- **Document**: File upload management

## Development

To set up for development:

1. Install development dependencies
2. Run in debug mode: `FLASK_ENV=development python run.py`
3. Access admin interface at `/admin`

## Production Deployment

For production deployment:

1. Set `FLASK_ENV=production` in `.env`
2. Use a production WSGI server like Gunicorn
3. Set up proper SECRET_KEY
4. Configure production database
5. Set up reverse proxy with HTTPS

## License

This project is open source and available under the MIT License.
