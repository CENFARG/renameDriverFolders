#!/usr/bin/env python3
"""
Script to fix stuck jobs and verify algorithm status.
Updates old executions with proper status and checks algorithms active state.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core_renombrador.database_manager import DatabaseManager
from datetime import datetime, timedelta

def main():
    print("🔧 Starting job fixes...\n")

    # Initialize database connection
    db = DatabaseManager()

    # ============================================================
    # 1. Check and update algorithms active status
    # ============================================================
    print("📊 Checking algorithms status...")
    jobs = db.find_all()

    inactive_count = 0
    for job in jobs:
        if not job.get('active', True):
            inactive_count += 1
            print(f"  ❌ {job.get('name', 'Unknown')} ({job.get('id')}) - INACTIVE")

    if inactive_count == 0:
        print("  ✅ All algorithms are active!\n")
    else:
        print(f"  ⚠️  Found {inactive_count} inactive algorithms\n")
        response = input("  ¿Activar todos los algoritmos inactivos? (y/n): ").lower()
        if response == 'y':
            for job in jobs:
                if not job.get('active', True):
                    job['active'] = True
                    db.update('id', job['id'], {'active': True})
                    print(f"    ✅ Activated: {job.get('name')}")
            print("  ✅ All algorithms activated!\n")

    # ============================================================
    # 2. Fix stuck executions (submitted -> completed/failed)
    # ============================================================
    print("📋 Checking for stuck executions...")

    executions = db.find_all()  # This gets all records
    stuck_count = 0
    updated_count = 0

    for exec_record in executions:
        status = exec_record.get('status', 'unknown')
        timestamp = exec_record.get('timestamp', '')

        # Check if job is stuck in "submitted" for more than 1 hour
        if status == 'submitted' and timestamp:
            try:
                exec_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_diff = datetime.now(exec_time.tzinfo) - exec_time

                if time_diff > timedelta(hours=1):
                    stuck_count += 1
                    print(f"  ⚠️  Stuck job: {exec_record.get('job_type')} from {timestamp}")

                    # Auto-mark as completed if older than 24 hours
                    if time_diff > timedelta(hours=24):
                        updated_count += 1
                        db.update('id', exec_record['id'], {
                            'status': 'completed',
                            'details': f'[AUTO-FIXED] Marked as completed. Original: {exec_record.get("details", "")}'
                        })
                        print(f"    ✅ Updated to 'completed': {exec_record.get('job_type')}")
            except Exception as e:
                print(f"  ❌ Error parsing timestamp: {e}")

    if stuck_count == 0:
        print("  ✅ No stuck jobs found!\n")
    else:
        print(f"\n  📊 Summary:")
        print(f"    - Total stuck jobs: {stuck_count}")
        print(f"    - Auto-updated (>24h): {updated_count}")
        print(f"    - Remaining (1-24h): {stuck_count - updated_count}")
        print(f"    💡 Tip: Jobs 1-24h old may still be processing\n")

    # ============================================================
    # 3. Show recent job statistics
    # ============================================================
    print("📈 Recent Job Statistics (last 7 days):")
    week_ago = datetime.now() - timedelta(days=7)

    status_counts = {'submitted': 0, 'processing': 0, 'completed': 0, 'failed': 0}
    recent_count = 0

    for exec_record in executions:
        timestamp = exec_record.get('timestamp', '')
        if timestamp:
            try:
                exec_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                if exec_time > week_ago:
                    recent_count += 1
                    status = exec_record.get('status', 'unknown')
                    if status in status_counts:
                        status_counts[status] += 1
            except:
                pass

    print(f"  Total jobs: {recent_count}")
    for status, count in status_counts.items():
        if count > 0:
            print(f"  - {status}: {count}")

    print("\n✅ Done!")

if __name__ == '__main__':
    main()
