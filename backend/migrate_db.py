#!/usr/bin/env python3
"""
Database migration script to add custom_audio_filename column.
Run this once to update the production database.
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.config import settings

print("Database Migration: Add custom_audio_filename column")
print("=" * 60)

# Connect to database
engine = create_engine(settings.database_url)

with engine.connect() as conn:
    # Check if column already exists
    if settings.database_url.startswith("sqlite"):
        result = conn.execute(text("PRAGMA table_info(jobs)"))
        columns = [row[1] for row in result]
    else:
        # PostgreSQL
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='jobs' AND column_name='custom_audio_filename'
        """))
        columns = [row[0] for row in result]

    if 'custom_audio_filename' in columns:
        print("✓ Column 'custom_audio_filename' already exists. No migration needed.")
    else:
        print("Adding column 'custom_audio_filename' to jobs table...")
        try:
            conn.execute(text("""
                ALTER TABLE jobs
                ADD COLUMN custom_audio_filename VARCHAR
            """))
            conn.commit()
            print("✓ Migration successful! Column added.")
        except Exception as e:
            print(f"✗ Migration failed: {e}")
            sys.exit(1)

print("=" * 60)
print("Migration complete!")
