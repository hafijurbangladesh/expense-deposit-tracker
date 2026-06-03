# Quick Start Guide - House Expense Manager

## Project Setup Complete! ✅

Your Django House Expense & Income Management System is ready for development.

## Next Steps

### 1. Create a Superuser Account
```bash
cd d:\MyPy\Assignments\FSCM
.venv\Scripts\python.exe manage.py createsuperuser
```

Follow the prompts to create your admin account with:
- Username
- Email
- Password

### 2. Create Initial Data (Optional)
Run the Django shell to add expense and deposit categories:

```bash
.venv\Scripts\python.exe manage.py shell
```

Then run:
```python
from houseexpense.core.models import ExpenseCategory, DepositCategory

# Create expense categories
categories = ['Water Bill', 'Gas Bill', 'Electricity Bill', 'Caretaker Salary', 'Waste Management', 'Maintenance', 'Other']
for cat in categories:
    ExpenseCategory.objects.create(name=cat)

# Create deposit categories
deposit_cats = ['Monthly Service Charge', 'Garage Fare', 'Other Income']
for cat in deposit_cats:
    DepositCategory.objects.create(name=cat)

exit()
```

### 3. Start the Development Server
```bash
.venv\Scripts\python.exe manage.py runserver
```

The application will be available at: **http://localhost:8000**

### 4. Access the Application
- **Home**: http://localhost:8000
- **Admin**: http://localhost:8000/admin
- **Dashboard**: http://localhost:8000/dashboard
- **Reports**: http://localhost:8000/reports

## Project Structure
```
d:\MyPy\Assignments\FSCM\
├── manage.py                 # Django management command
├── requirements.txt          # Project dependencies
├── README.md                 # Full documentation
├── .env.example             # Environment template
├── db.sqlite3               # Database (created after migration)
│
├── houseexpense/            # Main project package
│   ├── settings.py          # Django settings
│   ├── urls.py              # URL routing
│   ├── wsgi.py/asgi.py      # Application entry points
│   │
│   ├── core/                # Core app - Models & Auth
│   │   ├── models.py        # All data models
│   │   ├── admin.py         # Admin interface
│   │   ├── views.py         # Core views
│   │   ├── urls.py          # Core URLs
│   │   └── signals.py       # Auto-calculations
│   │
│   ├── accounts/            # User authentication
│   │   ├── views.py         # Login/Register/Profile
│   │   ├── forms.py         # Auth forms
│   │   └── urls.py          # Account URLs
│   │
│   ├── dashboard/           # Dashboard & Transactions
│   │   ├── views.py         # Dashboard views
│   │   └── urls.py          # Dashboard URLs
│   │
│   ├── reports/             # Reporting & Analytics
│   │   ├── views.py         # Report views & APIs
│   │   └── urls.py          # Report URLs
│   │
│   ├── static/              # CSS, JS, Images
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── script.js
│   │
│   └── templates/           # HTML Templates
│       ├── base.html        # Base template
│       ├── core/            # Core app templates
│       ├── accounts/        # Auth templates
│       ├── dashboard/       # Dashboard templates
│       └── reports/         # Report templates
│
├── .github/
│   └── copilot-instructions.md  # Project guidelines
└── static/                  # Collected static files (production)
```

## Key Features Implemented

✅ **Multi-flat Management**: Support for houses with multiple flats
✅ **Role-Based Access**: Manager (full access) and Flat Owner (view-only)
✅ **Expense Tracking**: Categorized expenses with amounts and dates
✅ **Income Management**: Track deposits and service charges
✅ **Monthly Reconciliation**: Auto-calculated monthly summaries
✅ **Comprehensive Reports**: Category-wise, annual, and flat-wise reports
✅ **Dashboard**: Real-time statistics and transactions
✅ **Mobile Responsive UI**: Bootstrap 5 design
✅ **Data Visualization**: Chart.js graphs and analytics
✅ **Audit Logging**: Track all changes
✅ **User Authentication**: Secure login and role management

## Database Models

### CustomUser
- Extends Django User model
- Roles: Manager, Flat Owner
- Contact information: Phone, Address

### House
- Property/Building details
- Manager assignment
- Multiple flats support

### Flat
- Individual units in a house
- Owner assignment
- Occupancy status
- Monthly charge

### Expense
- Categorized expenses
- Amount, date, description
- Auto-summarized monthly

### Deposit
- Income from flat owners
- Service charges, garage fares
- Flat-wise tracking

### MonthlySummary
- Auto-generated summaries
- Total income/expenses/balance
- For reporting and analytics

## Common Django Commands

```bash
# Start development server
.venv\Scripts\python.exe manage.py runserver

# Create migrations
.venv\Scripts\python.exe manage.py makemigrations

# Apply migrations
.venv\Scripts\python.exe manage.py migrate

# Create superuser
.venv\Scripts\python.exe manage.py createsuperuser

# Access shell
.venv\Scripts\python.exe manage.py shell

# Collect static files (production)
.venv\Scripts\python.exe manage.py collectstatic

# Run tests
.venv\Scripts\python.exe manage.py test

# Reset database
.venv\Scripts\python.exe manage.py flush
```

## Default Admin Credentials
- **URL**: http://localhost:8000/admin
- **Username/Email**: (Created by you during superuser setup)
- **Password**: (Created by you during superuser setup)

## Environment Configuration
Edit `.env` file for sensitive settings:
- `SECRET_KEY`: Change to a random string
- `DEBUG`: Set to False in production
- `ALLOWED_HOSTS`: Add your domain names
- `DATABASE_URL`: Database connection string
- `EMAIL_*`: Email configuration

## API Endpoints
- **Reports**: `/reports/api/chart-data/` - Get data for charts

## Troubleshooting

### Problem: Module Not Found
**Solution**: Ensure virtual environment is activated:
```bash
.venv\Scripts\activate
```

### Problem: Database Errors
**Solution**: Run migrations:
```bash
.venv\Scripts\python.exe manage.py migrate
```

### Problem: Static Files Not Loading
**Solution**: Collect static files:
```bash
.venv\Scripts\python.exe manage.py collectstatic --noinput
```

### Problem: Port Already in Use
**Solution**: Use a different port:
```bash
.venv\Scripts\python.exe manage.py runserver 8001
```

## Support & Documentation
- See **README.md** for comprehensive documentation
- See **CHANGELOG** for version history
- Check Django documentation: https://docs.djangoproject.com

## Next Deployment Steps
1. Set `DEBUG = False` in production
2. Use PostgreSQL instead of SQLite
3. Configure secure SECRET_KEY
4. Set up proper ALLOWED_HOSTS
5. Use Gunicorn + Nginx
6. Enable HTTPS/SSL
7. Set up proper logging
8. Configure database backups

---

**Happy developing! 🚀**
