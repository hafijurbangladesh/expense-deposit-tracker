# House Expense & Income Management System

A comprehensive Django-based system for managing house expenses and income with multiple flats, user roles, and detailed reporting.

## Features

- **Multi-flat Management**: Manage expenses and income for houses with multiple flats
- **Role-based Access Control**: Two user types - Manager (full access) and Flat Owner (view-only)
- **Expense Tracking**: Track various expense categories (water, gas, electricity, caretaker salary, waste management, etc.)
- **Income Management**: Record deposits and service charges from flat owners
- **Monthly Reconciliation**: Automatic monthly summaries and balance calculations
- **Comprehensive Reports**: 
  - Category-wise expense analysis
  - Annual trends and reports
  - Flat-wise deposit tracking
  - Charts and visualizations
- **Mobile Responsive UI**: Bootstrap 5 design that works on all devices
- **Professional Dashboard**: Real-time statistics and transaction history
- **Audit Logging**: Track all changes for security and compliance

## Technology Stack

- **Backend**: Django 4.2+
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: Bootstrap 5, HTML5, CSS3
- **Charts**: Chart.js for data visualization
- **Authentication**: Django built-in with custom roles

## Project Structure

```
houseexpense/
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── db.sqlite3               # SQLite database (generated after migration)
│
├── houseexpense/            # Main project settings
│   ├── settings.py          # Django configuration
│   ├── urls.py              # URL routing
│   ├── wsgi.py              # WSGI application
│   └── asgi.py              # ASGI application
│
├── core/                    # Core app with models
│   ├── models.py            # Data models
│   ├── admin.py             # Django admin configuration
│   ├── views.py             # Core views
│   ├── urls.py              # Core URL patterns
│   └── signals.py           # Signal handlers for auto-calculations
│
├── accounts/                # Authentication and user management
│   ├── views.py             # Login, register, profile views
│   ├── forms.py             # Custom forms
│   ├── urls.py              # Account URL patterns
│   └── decorators.py        # Role-based decorators
│
├── dashboard/               # Dashboard and transaction views
│   ├── views.py             # Dashboard and transaction views
│   └── urls.py              # Dashboard URL patterns
│
├── reports/                 # Reporting and analytics
│   ├── views.py             # Report views and APIs
│   └── urls.py              # Report URL patterns
│
├── static/                  # Static files
│   ├── css/
│   │   └── style.css        # Custom styles
│   └── js/
│       └── script.js        # Custom scripts
│
└── templates/               # HTML templates
    ├── base.html            # Base template
    ├── core/                # Core app templates
    ├── accounts/            # Auth templates
    ├── dashboard/           # Dashboard templates
    └── reports/             # Report templates
```

## Installation & Setup

### 1. Prerequisites
- Python 3.9 or higher
- pip (Python package manager)
- Git (optional, for cloning)

### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the root directory (copy from `.env.example`):
```bash
cp .env.example .env
```

Edit `.env` and update sensitive information:
- `SECRET_KEY` - Change to a unique, random string
- `DEBUG` - Set to `False` in production
- `ALLOWED_HOSTS` - Add your domain names

### 5. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

Follow the prompts to create your admin account.

### 7. Create Expense & Deposit Categories (Optional but Recommended)
Run Django shell to add initial data:
```bash
python manage.py shell
```

Then in the shell:
```python
from core.models import ExpenseCategory, DepositCategory

# Add expense categories
categories = ['Water Bill', 'Gas Bill', 'Electricity Bill', 'Caretaker Salary', 'Waste Management', 'Maintenance']
for cat in categories:
    ExpenseCategory.objects.create(name=cat)

# Add deposit categories
deposit_cats = ['Monthly Service Charge', 'Garage Fare', 'Other Income']
for cat in deposit_cats:
    DepositCategory.objects.create(name=cat)

exit()
```

### 8. Collect Static Files (Production)
```bash
python manage.py collectstatic --noinput
```

### 9. Run Development Server
```bash
python manage.py runserver
```

Access the application at `http://localhost:8000`

## Usage Guide

### Admin Access
- Navigate to `http://localhost:8000/admin`
- Login with superuser credentials
- Manage houses, flats, users, and categories

### Manager Functions
1. **Dashboard**: View overall statistics and recent transactions
2. **Add House**: Create new properties to manage
3. **Add Flats**: Add flats to houses and assign owners
4. **Record Expenses**: Add expenses with categories and amounts
5. **Record Deposits**: Add income from flat owners
6. **View Reports**: Generate and view various reports
7. **Export Data**: (Can be extended) Export data for further analysis

### Flat Owner Functions
1. **View Dashboard**: See assigned flats and their details
2. **View Summaries**: Check monthly expense/income summaries
3. **View Reports**: Access house-level reports (read-only)

## Models Overview

### CustomUser
Extended Django user model with roles and contact information.

### House
Represents a property with multiple flats.

### Flat
Individual unit within a house with owner assignment.

### Expense
Monthly expense entries with category and amount.

### Deposit
Income entries (service charges, garage fares, etc.) from flat owners.

### ExpenseCategory & DepositCategory
Predefined categories for expenses and deposits.

### MonthlySummary
Auto-generated monthly summaries for easy reporting.

### AuditLog
Tracks all changes for compliance and audit purposes.

## Database Schema

### Key Fields

**House**
- name (unique)
- address, city, state, pincode
- total_flats, manager (ForeignKey)
- created_at, updated_at

**Flat**
- house (ForeignKey)
- flat_number, owner (ForeignKey)
- carpet_area, monthly_charge
- is_occupied (Boolean)

**Expense**
- house (ForeignKey)
- category (ForeignKey)
- amount, description
- bill_date, payment_date, month
- added_by (ForeignKey)

**Deposit**
- house (ForeignKey)
- flat (ForeignKey, optional)
- category (ForeignKey)
- amount, description
- deposit_date, month
- added_by (ForeignKey)

## API Endpoints

### Report APIs
- `GET /reports/api/chart-data/` - Get chart data for visualizations
  - Parameters: `house_id`, `type` (monthly/category)

## Security Features

- CSRF protection on all forms
- SQL injection prevention (Django ORM)
- XSS protection in templates
- Role-based access control
- Audit logging for all changes
- Secure password hashing
- HTTPS ready (WhiteNoise middleware)

## Performance Optimization

- Database indexes on frequently queried fields
- Monthly summary caching
- Pagination on list views
- Static file compression (production)

## Deployment

### Production Checklist

1. **Security**
   ```python
   DEBUG = False
   SECRET_KEY = os.environ.get('SECRET_KEY')
   ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
   SECURE_SSL_REDIRECT = True
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   ```

2. **Database**
   - Use PostgreSQL instead of SQLite
   - Set up proper backups
   - Configure connection pooling

3. **Web Server**
   ```bash
   gunicorn houseexpense.wsgi:application --bind 0.0.0.0:8000
   ```

4. **Reverse Proxy**
   - Use Nginx or Apache
   - Enable compression
   - Configure SSL/TLS

5. **Monitoring**
   - Set up error logging
   - Monitor application performance
   - Set up uptime monitoring

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt`

2. **Database Errors**
   - Run migrations: `python manage.py migrate`
   - Check database file permissions

3. **Static Files Not Loading**
   - Run: `python manage.py collectstatic`
   - Check `STATIC_ROOT` configuration

4. **Login Issues**
   - Clear browser cookies
   - Ensure user account is active
   - Check role assignments

## Contributing

To contribute to this project:

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## Future Enhancements

- [ ] Payment gateway integration
- [ ] SMS/Email notifications
- [ ] Mobile app (React Native)
- [ ] Advanced analytics and forecasting
- [ ] Multi-language support
- [ ] PDF report generation
- [ ] Bulk data import
- [ ] Expense approval workflow

## License

This project is provided as-is for educational and business use.

## Support

For issues, questions, or suggestions, please contact the development team or create an issue in the project repository.

## Changelog

### Version 1.0.0 (Initial Release)
- Basic expense and income tracking
- User authentication with roles
- Dashboard and reports
- Mobile-responsive UI
- Audit logging

---

**Last Updated**: May 2024
**Version**: 1.0.0
