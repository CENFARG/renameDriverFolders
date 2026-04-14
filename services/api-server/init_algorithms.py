#!/usr/bin/env python3
"""
Script to initialize algorithms with active field in Supabase.
Run this once to add active: true to all predefined algorithms.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core_renombrador.database_manager import DatabaseManager

def main():
    print("🔧 Initializing algorithms with active field...\n")

    # Initialize database connection
    db = DatabaseManager()

    # Get all jobs (algorithms)
    all_jobs = db.find_all()

    print(f"Found {len(all_jobs)} jobs/algorithms in database\n")

    updated_count = 0
    for job in all_jobs:
        job_id = job.get('id')
        job_name = job.get('name', 'Unknown')
        active_value = job.get('active')

        # Check if active field is missing, null or undefined
        if active_value is None or active_value == '':
            print(f"⚠️  {job_name} ({job_id}) - active field is {active_value}")

            # Update to set active = true
            db.update('id', job_id, {'active': True})
            updated_count += 1
            print(f"    ✅ Updated: active = true")
        else:
            print(f"✅ {job_name} ({job_id}) - active = {active_value}")

    print(f"\n📊 Summary:")
    print(f"  Total jobs: {len(all_jobs)}")
    print(f"  Updated: {updated_count}")
    print(f"  Already OK: {len(all_jobs) - updated_count}")
    print(f"\n✅ Done!")

if __name__ == '__main__':
    main()
