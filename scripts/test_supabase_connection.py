"""
Test Script - Verificar Conexión Supabase y Datos de Auditoría
==============================================================

Este script verifica:
1. Conexión a Supabase
2. Datos en tabla 'job_executions'
3. Datos en tabla 'jobs'
4. Registros recientes

Uso:
    python test_supabase_connection.py
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def test_supabase_connection():
    """Test connection to Supabase and query job_executions table."""

    # Try using supabase-py if available
    try:
        from supabase import create_client, Client

        # Get credentials from environment
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")  # or SERVICE_ROLE_KEY

        if not supabase_url or not supabase_key:
            print("❌ Supabase credentials not found in environment")
            print(f"   SUPABASE_URL: {'✓' if supabase_url else '✗'}")
            print(f"   SUPABASE_KEY: {'✓' if supabase_key else '✗'}")
            return

        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)

        print("✅ Supabase client created successfully")
        print(f"   URL: {supabase_url}")
        print()

        # Test 1: Query job_executions table
        print("📊 Test 1: Query job_executions table")
        print("-" * 50)

        try:
            result = supabase.table("job_executions").select("*").order("timestamp", desc=True).limit(10).execute()

            if result.data:
                print(f"✅ Found {len(result.data)} execution(s)")
                print()

                for idx, exec_data in enumerate(result.data[:5], 1):
                    print(f"   Execution #{idx}:")
                    print(f"   ├─ ID: {exec_data.get('id')}")
                    print(f"   ├─ Timestamp: {exec_data.get('timestamp')}")
                    print(f"   ├─ User: {exec_data.get('user_email')}")
                    print(f"   ├─ Folder: {exec_data.get('folder_id')}")
                    print(f"   ├─ Status: {exec_data.get('status')}")
                    print(f"   └─ Task ID: {exec_data.get('task_id', 'N/A')}")
                    print()
            else:
                print("❌ No executions found in job_executions table")
                print("   This means:")
                print("   1. No jobs have been executed yet, OR")
                print("   2. The table is empty/not being populated")
                print()

        except Exception as e:
            print(f"❌ Error querying job_executions: {e}")
            print()

        # Test 2: Query jobs table
        print("📊 Test 2: Query jobs table")
        print("-" * 50)

        try:
            result = supabase.table("jobs").select("*").limit(10).execute()

            if result.data:
                print(f"✅ Found {len(result.data)} job(s)")

                for idx, job_data in enumerate(result.data[:5], 1):
                    print(f"   Job #{idx}:")
                    print(f"   ├─ ID: {job_data.get('id')}")
                    print(f"   ├─ Name: {job_data.get('name')}")
                    print(f"   ├─ Active: {job_data.get('active')}")
                    print(f"   └─ Trigger: {job_data.get('trigger_type')}")
                    print()
            else:
                print("❌ No jobs found in jobs table")
                print()

        except Exception as e:
            print(f"❌ Error querying jobs: {e}")
            print()

        # Test 3: Count total records
        print("📊 Test 3: Total Records Count")
        print("-" * 50)

        try:
            # Count job_executions
            exec_result = supabase.table("job_executions").select("*", count="exact").execute()
            exec_count = exec_result.count if hasattr(exec_result, 'count') else len(exec_result.data)

            # Count jobs
            jobs_result = supabase.table("jobs").select("*", count="exact").execute()
            jobs_count = jobs_result.count if hasattr(jobs_result, 'count') else len(jobs_result.data)

            print(f"   job_executions: {exec_count or 'N/A'} records")
            print(f"   jobs: {jobs_count or 'N/A'} records")
            print()

        except Exception as e:
            print(f"❌ Error counting records: {e}")
            print()

    except ImportError:
        print("❌ supabase-py not installed")
        print("   Install with: pip install supabase")
        return
    except Exception as e:
        print(f"❌ Error: {e}")
        return


def main():
    print("=" * 60)
    print("🔍 Supabase Connection Test - Job Executions Audit")
    print("=" * 60)
    print(f"   Timestamp: {datetime.utcnow().isoformat()}Z")
    print()

    test_supabase_connection()

    print("=" * 60)
    print("✅ Test completed")
    print()


if __name__ == "__main__":
    main()
