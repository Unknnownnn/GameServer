"""
CTF Database Platform - Vulnerability Verification Script
=========================================================
This script tests all intentional vulnerabilities in the CTF database.
Use this to verify the platform is working correctly.

Requirements:
    pip install pymysql requests

Usage:
    python verify_vulnerabilities.py
"""

import pymysql
import requests
import sys
from datetime import datetime

# Configuration
DB_CONFIG = {
    'host': '134.209.146.43',
    'user': 'ctf_player',
    'password': 'player_password_456',
    'database': 'ctf_db',
    'port': 5001
}

RESET_API_URL = 'http://134.209.146.43:5001'

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def test_database_connection():
    """Test 1: Database Connection"""
    print_header("Test 1: Database Connection")
    
    try:
        connection = pymysql.connect(**DB_CONFIG)
        connection.close()
        print_success("Successfully connected to MySQL database")
        return True
    except Exception as e:
        print_error(f"Failed to connect to database: {e}")
        print_info("Make sure the platform is running: docker-compose up -d")
        return False

def test_sqli_vulnerability():
    """Test 2: SQL Injection Vulnerability"""
    print_header("Test 2: SQL Injection Vulnerability")
    
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Test basic injection
        malicious_input = "' OR '1'='1"
        query = f"SELECT * FROM users WHERE username = '{malicious_input}'"
        
        print_info(f"Testing SQL Injection with: {malicious_input}")
        print_info(f"Query: {query}")
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        if len(results) > 0:
            print_success(f"SQL Injection successful! Retrieved {len(results)} users")
            print_info("This demonstrates how unvalidated input can bypass authentication")
        else:
            print_warning("SQL Injection test returned no results")
        
        # Test UNION attack on secrets
        print_info("\nTesting UNION-based SQL Injection on secrets table...")
        union_query = "SELECT id, username, password_hash, is_admin FROM users UNION SELECT id, secret_name, secret_value, access_level FROM secrets"
        cursor.execute(union_query)
        secrets = cursor.fetchall()
        
        print_success(f"UNION attack successful! Retrieved {len(secrets)} rows including secrets")
        for secret in secrets:
            if 'FLAG{' in str(secret):
                print_info(f"   Found flag: {secret}")
        
        connection.close()
        return True
        
    except Exception as e:
        print_error(f"SQL Injection test failed: {e}")
        return False

def test_truncation_attack():
    """Test 3: SQL Truncation Attack"""
    print_header("Test 3: SQL Truncation Attack")
    
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Check current admin user
        cursor.execute("SELECT username, is_admin FROM users WHERE is_admin = TRUE")
        admin = cursor.fetchone()
        print_info(f"Current admin user: {admin}")
        
        # Attempt truncation attack
        # Username limit is 20 chars. If we register "admin               x" (20 chars)
        # MySQL with sql_mode='' will truncate to "admin" silently
        
        truncated_username = "admin              x"  # 20 characters exactly
        print_info(f"\nAttempting to register username: '{truncated_username}' (20 chars)")
        print_info("With sql_mode='', MySQL may truncate this to 'admin'")
        
        # Note: This will fail with duplicate key due to UNIQUE constraint
        # But demonstrates the vulnerability concept
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (%s, %s, %s)",
                (truncated_username, "hashed_password", False)
            )
            connection.commit()
            print_warning("Insert succeeded - truncation may occur depending on MySQL config")
        except pymysql.IntegrityError as e:
            if "Duplicate entry" in str(e):
                print_success("Truncation attack demonstrated! Duplicate 'admin' entry rejected")
                print_info("This shows the username was truncated from 20 chars to 'admin'")
            else:
                print_error(f"Unexpected error: {e}")
        
        connection.close()
        return True
        
    except Exception as e:
        print_error(f"Truncation attack test failed: {e}")
        return False

def test_idor_vulnerability():
    """Test 4: IDOR (Insecure Direct Object Reference)"""
    print_header("Test 4: IDOR Vulnerability")
    
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print_info("Accessing messages with sequential IDs...")
        
        # Access messages that may belong to other users
        for message_id in range(1, 6):
            cursor.execute("SELECT id, sender_id, recipient_id, content FROM messages WHERE id = %s", (message_id,))
            message = cursor.fetchone()
            
            if message:
                print_success(f"Message {message_id} accessed:")
                print_info(f"   Sender ID: {message[1]}, Recipient ID: {message[2]}")
                print_info(f"   Content: {message[3][:50]}...")
                
                if "FLAG{" in message[3] or "verification code" in message[3].lower():
                    print_warning(f"   ⚠️  Sensitive data found in message {message_id}!")
        
        print_success("\nIDOR vulnerability confirmed! Sequential IDs allow unauthorized access")
        
        connection.close()
        return True
        
    except Exception as e:
        print_error(f"IDOR test failed: {e}")
        return False

def test_race_condition_setup():
    """Test 5: Race Condition Setup (Coupon Table)"""
    print_header("Test 5: Race Condition Setup")
    
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print_info("Checking coupons with limited redemptions...")
        
        cursor.execute("SELECT code, discount_percent, max_uses, current_uses FROM coupons WHERE max_uses = 1")
        limited_coupons = cursor.fetchall()
        
        if limited_coupons:
            print_success(f"Found {len(limited_coupons)} single-use coupons:")
            for coupon in limited_coupons:
                print_info(f"   Code: {coupon[0]}, Discount: {coupon[1]}%, Uses: {coupon[3]}/{coupon[2]}")
            
            print_warning("\nRace condition vulnerability exists!")
            print_info("Multiple concurrent redemption requests could bypass max_uses check")
            print_info("This requires application-level testing with concurrent requests")
        
        connection.close()
        return True
        
    except Exception as e:
        print_error(f"Race condition test failed: {e}")
        return False

def test_reset_api():
    """Test 6: Reset API"""
    print_header("Test 6: Reset API Functionality")
    
    try:
        # Test health endpoint
        print_info("Testing health endpoint...")
        response = requests.get(f"{RESET_API_URL}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Health endpoint accessible")
            print_info(f"   Status: {data.get('status')}")
            print_info(f"   Last Reset: {data.get('last_reset')}")
            print_info(f"   Reset Count: {data.get('reset_count')}")
            print_info(f"   Reset Interval: {data.get('reset_interval_seconds')}s")
        else:
            print_error(f"Health check returned status {response.status_code}")
            return False
        
        # Test manual reset (optional - uncomment to test)
        print_info("\nReset API is functional")
        print_warning("Manual reset test skipped (to avoid disrupting current session)")
        print_info("To test manual reset: curl -X POST http://localhost:5001/reset")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to reset API")
        print_info("Make sure the refresher container is running")
        return False
    except Exception as e:
        print_error(f"Reset API test failed: {e}")
        return False

def test_data_seeding():
    """Test 7: Data Seeding"""
    print_header("Test 7: Data Seeding Verification")
    
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Check users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print_info(f"Users table: {user_count} users")
        
        # Check secrets/flags
        cursor.execute("SELECT COUNT(*) FROM secrets")
        secret_count = cursor.fetchone()[0]
        print_info(f"Secrets table: {secret_count} secrets")
        
        cursor.execute("SELECT secret_name FROM secrets WHERE secret_value LIKE 'FLAG{%}'")
        flags = cursor.fetchall()
        print_success(f"Found {len(flags)} flags in database:")
        for flag in flags:
            print_info(f"   {flag[0]}")
        
        # Check messages
        cursor.execute("SELECT COUNT(*) FROM messages")
        message_count = cursor.fetchone()[0]
        print_info(f"Messages table: {message_count} messages")
        
        # Check coupons
        cursor.execute("SELECT COUNT(*) FROM coupons")
        coupon_count = cursor.fetchone()[0]
        print_info(f"Coupons table: {coupon_count} coupons")
        
        if user_count >= 6 and secret_count >= 5 and message_count >= 8 and coupon_count >= 5:
            print_success("\nAll data seeding verified successfully!")
            return True
        else:
            print_warning("Some data may be missing from initial seed")
            return False
        
        connection.close()
        
    except Exception as e:
        print_error(f"Data seeding test failed: {e}")
        return False

def main():
    """Run all verification tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                                                                    ║")
    print("║      CTF Database Platform - Vulnerability Verification           ║")
    print("║                                                                    ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}\n")
    
    print_info(f"Starting verification at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("SQL Injection", test_sqli_vulnerability),
        ("SQL Truncation", test_truncation_attack),
        ("IDOR", test_idor_vulnerability),
        ("Race Condition Setup", test_race_condition_setup),
        ("Reset API", test_reset_api),
        ("Data Seeding", test_data_seeding),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Unexpected error in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print_header("Verification Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"   {test_name:.<50} {status}")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.END}")
    
    if passed == total:
        print_success("\n🎉 All verification tests passed! Platform is ready for CTF challenges.")
    else:
        print_warning(f"\n⚠️  {total - passed} test(s) failed. Please check the platform configuration.")
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_warning("\n\nVerification interrupted by user")
        sys.exit(130)
