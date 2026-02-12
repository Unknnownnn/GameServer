#!/usr/bin/env python3
"""
Simple test script to perform a one-time database reset from host machine.
Usage: python test_reset.py
"""

import os
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
            executed = 0
            for idx, statement in enumerate(statements, 1):
                # Skip comments and empty statements
                if statement.startswith('--') or not statement:
                    continue
                
                try:
                    cursor.execute(statement)
                    executed += 1
                except pymysql.Error as e:
                    # Log but continue (some statements like USE might fail)
                    if 'syntax' in str(e).lower() or 'error' in str(e).lower():
                        print(f"   ⚠️  Statement {idx} warning: {e}")
            
            connection.commit()
            print(f"   ✅ Executed {executed} statements successfully")
        
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
    try:
        success = test_reset()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)
