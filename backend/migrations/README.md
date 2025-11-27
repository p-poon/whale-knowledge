# Database Migrations

This directory contains SQL migration scripts for the Whale Knowledge Base.

## Running Migrations

To apply a migration, run it against your PostgreSQL database:

```bash
psql $DATABASE_URL -f migrations/001_add_api_usage_audit_table.sql
```

Or if using the database URL from .env:

```bash
# Load environment variables
source .env

# Run migration
psql "$database_url" -f migrations/001_add_api_usage_audit_table.sql
```

## Available Migrations

- `001_add_api_usage_audit_table.sql` - Creates the API usage audit table for tracking JINA tokens and Pinecone loads

## Future: Alembic Integration

For automatic migration management, consider setting up Alembic:

```bash
pip install alembic
alembic init alembic
```

Then configure `alembic.ini` with your database URL and create migrations with:

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```
