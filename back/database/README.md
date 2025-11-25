# Database Setup Guide

## Prerequisites

1. **PostgreSQL 12+** installed and running
2. **Python packages**: `psycopg2-binary`, `sqlalchemy`

## Quick Setup

### 1. Create Database

```bash
# Option A: Using psql command
psql -U postgres
CREATE DATABASE leak_detector;
\q

# Option B: Using createdb utility
createdb -U postgres leak_detector
```

### 2. Run Schema SQL

```bash
psql -U postgres -d leak_detector -f back/database/schema.sql
```

### 3. Configure Connection

Set the `DATABASE_URL` environment variable:

```bash
# Windows PowerShell
$env:DATABASE_URL = "postgresql://postgres:your_password@localhost:5432/leak_detector"

# Linux/Mac
export DATABASE_URL="postgresql://postgres:your_password@localhost:5432/leak_detector"
```

Or update the default in `back/database/database.py`:
```python
DATABASE_URL = "postgresql://your_user:your_password@localhost:5432/leak_detector"
```

### 4. Test Connection

```bash
cd back
python -c "from database import test_connection; test_connection()"
```

## Database Schema

### Tables

1. **uploads** - Uploaded file metadata
   - Tracks CSV files uploaded by users
   - Stores file path, row/column counts, status

2. **anomalies** - Detected anomalies
   - One row per detected anomaly
   - Stores anomaly score, severity, feature values
   - SHAP values cached as JSONB

3. **actions** - User actions on anomalies
   - Tracks what actions users took (reviewed, work order, export)
   - Links to specific anomalies

4. **processing_jobs** - ML job tracking
   - Tracks async ML processing jobs
   - Stores progress, status, errors

### Indexes

- Optimized for common query patterns
- GIN indexes on JSONB columns for fast JSON queries
- Time-based indexes for sorting by date

### View

- **dashboard_metrics** - Aggregated metrics for dashboard
  - Total uploads, samples, anomalies
  - Severity breakdown
  - Last updated timestamp

## Alternative: SQLite for Development

If you want to use SQLite for local development:

1. Update `back/database/database.py`:
```python
DATABASE_URL = "sqlite:///./leak_detector.db"
```

2. Remove PostgreSQL-specific features from schema:
   - UUID extension (use string UUIDs)
   - JSONB (use JSON)
   - Remove triggers

3. Run:
```python
from database import init_db
init_db()
```

## Migrations (Future)

For production deployments, use Alembic for database migrations:

```bash
pip install alembic
alembic init alembic
# Configure alembic.ini with DATABASE_URL
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

## Troubleshooting

### Connection Refused
- Check PostgreSQL is running: `pg_isready`
- Verify port 5432 is open
- Check `pg_hba.conf` authentication settings

### Permission Denied
- Grant privileges: `GRANT ALL PRIVILEGES ON DATABASE leak_detector TO your_user;`

### Schema Not Found
- Ensure you're connected to the correct database
- Run schema.sql again
