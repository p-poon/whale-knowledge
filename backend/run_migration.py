"""Run database migrations for the audit table."""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import Base, engine, SessionLocal
from app.core.config import settings

def run_migration():
    """Create all database tables including the new audit table."""

    print("=" * 60)
    print("Running Database Migration")
    print("=" * 60)
    print(f"\nDatabase URL: {settings.database_url}")

    try:
        print("\nCreating tables...")
        Base.metadata.create_all(bind=engine)
        print("✓ All tables created successfully")

        # Verify the audit table exists
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        if 'api_usage_audit' in tables:
            print("\n✓ Table 'api_usage_audit' verified")

            # Get column info
            columns = inspector.get_columns('api_usage_audit')
            print(f"\nTable structure ({len(columns)} columns):")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")

            # Get indexes
            indexes = inspector.get_indexes('api_usage_audit')
            print(f"\nIndexes ({len(indexes)} total):")
            for idx in indexes:
                print(f"  - {idx['name']}")
        else:
            print("\n✗ Table 'api_usage_audit' not found")
            return False

        # Test database connection
        print("\nTesting database connection...")
        db = SessionLocal()
        try:
            result = db.execute("SELECT COUNT(*) FROM api_usage_audit")
            count = result.scalar()
            print(f"✓ Connection successful - Table has {count} records")
        finally:
            db.close()

        print("\n" + "=" * 60)
        print("✓ Database migration complete!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
