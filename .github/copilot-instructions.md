# House Expense & Income Management System

Django-based system for managing house expenses and income with multiple flats, user roles, and comprehensive reporting.

## Project Setup Checklist

- [x] Create .github directory and copilot-instructions.md
- [x] Create project directory structure
- [ ] Install dependencies (Django, DRF, etc.)
- [ ] Create Django manage.py and configuration
- [ ] Create database models
- [ ] Set up user authentication and roles
- [ ] Create views and URLs
- [ ] Create templates
- [ ] Run migrations
- [ ] Create superuser
- [ ] Test the application

## Technology Stack

- **Backend**: Django 4.2+
- **Database**: SQLite (development), PostgreSQL (production)
- **Frontend**: Bootstrap 5, HTML5, CSS3
- **Authentication**: Django built-in auth + custom roles
- **Charts**: Chart.js for reports and dashboard

## Project Structure

```
houseexpense/
├── manage.py
├── requirements.txt
├── .env.example
├── houseexpense/           # Main project settings
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── core/                   # Core app for models
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
├── accounts/               # User authentication
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   └── decorators.py
├── dashboard/              # Dashboard views
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── views.py
│   ├── urls.py
│   └── templates/
├── reports/                # Reports generation
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── views.py
│   ├── urls.py
│   └── forms.py
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
└── templates/
    ├── base.html
    ├── dashboard.html
    └── ...
```

## Getting Started

1. Create virtual environment: `python -m venv venv`
2. Activate: `venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Run migrations: `python manage.py migrate`
5. Create superuser: `python manage.py createsuperuser`
6. Start server: `python manage.py runserver`
