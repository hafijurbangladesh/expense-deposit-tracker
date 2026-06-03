# SQLite to PostgreSQL Migration Guide

## Current Status

- ✅ Django settings updated to support PostgreSQL via environment variables
- ✅ PostgreSQL driver (`psycopg[binary]`) installed in virtual environment
- ✅ SQLite data exported to `sqlite_data.json` (UTF-8 encoded)
- ✅ `.env` file created with PostgreSQL defaults
- ⏳ PostgreSQL server not currently running on this machine

## Prerequisites

Before running the migration, ensure:

1. **PostgreSQL is installed and running** on your machine
   - Windows: Download from https://www.postgresql.org/download/windows/
   - Or use Docker: `docker run -d -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres`

2. **Database and user created**:
   ```sql
   CREATE DATABASE houseexpense;
   CREATE USER postgres WITH PASSWORD 'postgres';
   GRANT ALL PRIVILEGES ON DATABASE houseexpense TO postgres;
   ```

3. **Environment variables configured** in `.env`:
   ```
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=houseexpense
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_HOST=localhost
   DB_PORT=5432
   ```

## Migration Steps

Once PostgreSQL is running and configured:

### 1. Verify Connection
```bash
python manage.py dbshell
```

### 2. Run Migrations
```bash
python manage.py migrate
```

### 3. Load SQLite Data
```bash
python manage.py loaddata sqlite_data.json
```

### 4. Verify Data
```bash
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.count()
```

### 5. Test Application
```bash
python manage.py runserver
```

## Troubleshooting

### Connection Timeout
- Verify PostgreSQL is running: `psql -U postgres -h localhost`
- Check `.env` credentials match your PostgreSQL setup
- Ensure port 5432 is not blocked by firewall

### Migration Errors
- Check for unsupported data types in `sqlite_data.json`
- Review Django migration logs: `python manage.py migrate --verbosity 3`

### Data Loss During Load
- The fixture `sqlite_data.json` is preserved as backup
- You can re-run `python manage.py loaddata sqlite_data.json` anytime

## Switching Back to SQLite (if needed)

Update `.env`:
```
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
```

Then run `python manage.py migrate` to reset to SQLite.

## Files Changed

- `houseexpense/settings.py` - Updated DATABASES configuration
- `requirements.txt` - Updated PostgreSQL driver (psycopg[binary]==3.3.4)
- `.env` - Created with PostgreSQL defaults
- `.env.example` - Updated with PostgreSQL variables
- `sqlite_data.json` - Exported SQLite data fixture
- `.gitignore` - Created to exclude dev artifacts
