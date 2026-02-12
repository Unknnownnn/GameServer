#!/usr/bin/env python3
"""
Database reset script - can run once or continuously every 15 minutes.
Usage: 
  python test_reset.py          # Run once
  python test_reset.py --loop   # Run every 15 minutes (900 seconds)
"""

import os
import sys
import time
from datetime import datetime
import pymysql
from pymysql.cursors import DictCursor

# Configuration for local execution
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_ROOT_PASSWORD = 'super_secure_root_password_123'
INIT_SQL_PATH = os.path.join(os.path.dirname(__file__), 'init.sql')

def test_reset():
    """Perform a one-time database reset for testing."""
    print("=" * 70)
    print("🧪 Testing Database Reset (Local Mode)")
    print(f"   MySQL Host: {MYSQL_HOST}:{MYSQL_PORT}")
    print(f"   Init SQL: {INIT_SQL_PATH}")
    print("=" * 70)
    
    # Check if init.sql exists
    if not os.path.exists(INIT_SQL_PATH):
        print(f"❌ ERROR: init.sql not found at {INIT_SQL_PATH}")
        return False
    
    # Read init.sql
    print("\n📝 Reading init.sql...")
    with open(INIT_SQL_PATH, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
    print(f"   Found {len(statements)} SQL statements")
    
    # Connect to MySQL
    print(f"\n🔌 Connecting to MySQL at {MYSQL_HOST}:{MYSQL_PORT}...")
    try:
        connection = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user='root',
            password=MYSQL_ROOT_PASSWORD,
            charset='utf8mb4',
            cursorclass=DictCursor
        )
        print("   ✅ Connected successfully")
    except pymysql.Error as e:
        print(f"   ❌ Connection failed: {e}")
        print("\n💡 Make sure MySQL container is running:")
        print("   docker-compose up -d db")
        return False
    
    # Execute reset
    print("\n🔄 Executing database reset...")
    try:
        with connection.cursor() as cursor:
            # Step 1: Explicitly drop the database for a clean slate
            print("   🗑️  Dropping existing database...")
            cursor.execute("DROP DATABASE IF EXISTS ctop_university")
            connection.commit()
            print("   ✅ Database dropped")
            
            # Step 2: Remove comments and clean SQL
            print("   📝 Cleaning SQL statements...")
            cleaned_statements = []
            for line in sql_script.split('\n'):
                line = line.strip()
                # Skip empty lines and comment-only lines
                if not line or line.startswith('--'):
                    continue
                cleaned_statements.append(line)
            
            # Join and split by semicolons
            cleaned_sql = ' '.join(cleaned_statements)
            statements = [stmt.strip() for stmt in cleaned_sql.split(';') if stmt.strip()]
            
            print(f"   📝 Executing {len(statements)} SQL statements...")
            
            # Step 3: Execute all statements
            executed = 0
            errors = 0
            for idx, statement in enumerate(statements, 1):
                if not statement or len(statement) < 5:
                    continue
                
                try:
                    cursor.execute(statement)
                    executed += 1
                except pymysql.Error as e:
                    errors += 1
                    if errors <= 3:  # Only show first 3 errors
                        print(f"   ⚠️  Statement {idx} warning: {e}")
            
            connection.commit()
            print(f"   ✅ Executed {executed} statements successfully ({errors} warnings)")
        
        # Verify the reset
        print("\n🔍 Verifying database state...")
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM ctop_university.users")
            user_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM ctop_university.secrets")
            secret_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM ctop_university.messages")
            message_count = cursor.fetchone()['count']
            
            print(f"   Users: {user_count}")
            print(f"   Secrets: {secret_count}")
            print(f"   Messages: {message_count}")
        
        print("\n" + "=" * 70)
        print("✅ Database reset completed successfully!")
        print("=" * 70)
        return True
        
    except pymysql.Error as e:
        print(f"\n❌ Reset failed: {e}")
        return False
    finally:
        connection.close()

if __name__ == '__main__':
    # Check if loop mode is requested
    loop_mode = '--loop' in sys.argv or '-l' in sys.argv
    reset_interval = 900  # 15 minutes in seconds
    
    if loop_mode:
        print("=" * 70)
        print("🔄 CONTINUOUS RESET MODE")
        print(f"   Reset Interval: {reset_interval} seconds ({reset_interval/60:.1f} minutes)")
        print("   Press Ctrl+C to stop")
        print("=" * 70)
        print()
        
        reset_count = 0
        try:
            while True:
                reset_count += 1
                print(f"\n{'=' * 70}")
                print(f"⏰ SCHEDULED RESET #{reset_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'=' * 70}\n")
                
                success = test_reset()
                
                if success:
                    print(f"\n⏰ Next reset in {reset_interval} seconds ({reset_interval/60:.1f} minutes)...")
                    print(f"   Next reset at: {datetime.fromtimestamp(time.time() + reset_interval).strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    print(f"\n⚠️  Reset failed, will retry in {reset_interval} seconds...")
                
                time.sleep(reset_interval)
                
        except KeyboardInterrupt:
            print(f"\n\n⚠️  Continuous reset stopped by user after {reset_count} resets")
            exit(0)
    else:
        # Single run mode
        try:
            success = test_reset()
            exit(0 if success else 1)
        except KeyboardInterrupt:
            print("\n\n⚠️  Operation cancelled by user")
            exit(1)
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            exit(1)
