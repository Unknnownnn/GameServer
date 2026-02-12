#!/usr/bin/env python3
"""
CTF Database Reset & Watchdog Service
=====================================
Automated database reset service with manual trigger endpoint.

Features:
- Automatic database reset every 15 minutes
- Manual reset trigger via HTTP POST /reset
- Health check endpoint at GET /health
- Comprehensive logging and error handling
"""

import os
import sys
import time
import logging
import threading
from datetime import datetime
from flask import Flask, jsonify, request
import pymysql
from pymysql.cursors import DictCursor

# ============================================================================
# Configuration
# ============================================================================
MYSQL_HOST = os.getenv('MYSQL_HOST', 'db')
MYSQL_ROOT_PASSWORD = os.getenv('MYSQL_ROOT_PASSWORD', 'super_secure_root_password_123')
RESET_INTERVAL = int(os.getenv('RESET_INTERVAL', 900))  # Default: 15 minutes (900 seconds)
INIT_SQL_PATH = os.getenv('INIT_SQL_PATH', '/docker-entrypoint-initdb.d/init.sql')
FLASK_PORT = 5001

# ============================================================================
# Logging Configuration
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# Flask Application
# ============================================================================
app = Flask(__name__)

# Global state tracking
last_reset_time = None
reset_count = 0
reset_lock = threading.Lock()

# ============================================================================
# Database Operations
# ============================================================================

def wait_for_database(max_retries=30, retry_delay=2):
    """
    Wait for MySQL to be ready before proceeding.
    """
    logger.info(f"Waiting for MySQL server at {MYSQL_HOST} to be ready...")
    
    for attempt in range(1, max_retries + 1):
        try:
            connection = pymysql.connect(
                host=MYSQL_HOST,
                user='root',
                password=MYSQL_ROOT_PASSWORD,
                connect_timeout=5
            )
            connection.close()
            logger.info("✅ MySQL server is ready!")
            return True
        except pymysql.Error as e:
            logger.warning(f"Attempt {attempt}/{max_retries}: MySQL not ready yet - {e}")
            if attempt < max_retries:
                time.sleep(retry_delay)
    
    logger.error("❌ Failed to connect to MySQL after maximum retries")
    return False


def reset_database():
    """
    Drop the ctf_db database and reload from init.sql.
    Returns: (success: bool, message: str)
    """
    global last_reset_time, reset_count
    
    with reset_lock:
        try:
            logger.info("=" * 70)
            logger.info("🔄 Starting database reset operation...")
            
            # Read the init.sql file
            if not os.path.exists(INIT_SQL_PATH):
                error_msg = f"init.sql not found at {INIT_SQL_PATH}"
                logger.error(f"❌ {error_msg}")
                return False, error_msg
            
            with open(INIT_SQL_PATH, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            # Connect to MySQL as root
            connection = pymysql.connect(
                host=MYSQL_HOST,
                user='root',
                password=MYSQL_ROOT_PASSWORD,
                charset='utf8mb4',
                cursorclass=DictCursor
            )
            
            try:
                with connection.cursor() as cursor:
                    # Split SQL script by semicolons and execute each statement
                    statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
                    
                    logger.info(f"📝 Executing {len(statements)} SQL statements...")
                    
                    for idx, statement in enumerate(statements, 1):
                        # Skip comments and empty statements
                        if statement.startswith('--') or not statement:
                            continue
                        
                        try:
                            cursor.execute(statement)
                        except pymysql.Error as e:
                            # Some statements like USE might fail, log but continue
                            logger.debug(f"Statement {idx} note: {e}")
                    
                    connection.commit()
                
                # Update state
                last_reset_time = datetime.now()
                reset_count += 1
                
                success_msg = f"Database reset completed successfully (Reset #{reset_count})"
                logger.info(f"✅ {success_msg}")
                logger.info("=" * 70)
                
                return True, success_msg
                
            finally:
                connection.close()
        
        except pymysql.Error as e:
            error_msg = f"MySQL error during reset: {e}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
        
        except Exception as e:
            error_msg = f"Unexpected error during reset: {e}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg


# ============================================================================
# Periodic Reset Task
# ============================================================================

def periodic_reset_task():
    """
    Background thread that resets the database every RESET_INTERVAL seconds.
    """
    logger.info(f"🕐 Periodic reset task started (interval: {RESET_INTERVAL} seconds / {RESET_INTERVAL/60:.1f} minutes)")
    
    while True:
        time.sleep(RESET_INTERVAL)
        logger.info("⏰ Scheduled reset triggered")
        success, message = reset_database()
        
        if not success:
            logger.error(f"Scheduled reset failed: {message}")


# ============================================================================
# Flask Routes
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    """
    uptime = None
    if last_reset_time:
        uptime = (datetime.now() - last_reset_time).total_seconds()
    
    return jsonify({
        'status': 'healthy',
        'service': 'CTF Database Reset Service',
        'last_reset': last_reset_time.isoformat() if last_reset_time else 'Never',
        'reset_count': reset_count,
        'seconds_since_last_reset': uptime,
        'reset_interval_seconds': RESET_INTERVAL
    }), 200


@app.route('/reset', methods=['POST'])
def manual_reset():
    """
    Manual database reset trigger endpoint.
    """
    logger.info("🔧 Manual reset triggered via HTTP POST /reset")
    
    # Optional: Add authentication here if needed
    # auth_token = request.headers.get('Authorization')
    # if auth_token != 'Bearer your_secret_token':
    #     return jsonify({'error': 'Unauthorized'}), 401
    
    success, message = reset_database()
    
    if success:
        return jsonify({
            'status': 'success',
            'message': message,
            'reset_count': reset_count,
            'timestamp': last_reset_time.isoformat()
        }), 200
    else:
        return jsonify({
            'status': 'error',
            'message': message
        }), 500


@app.route('/', methods=['GET'])
def index():
    """
    Service information endpoint.
    """
    return jsonify({
        'service': 'CTF Database Reset & Watchdog Service',
        'version': '1.0.0',
        'endpoints': {
            'health_check': 'GET /health',
            'manual_reset': 'POST /reset',
            'info': 'GET /',
            'vulnerable_endpoints': {
                'search_secrets': 'GET /api/search-secrets?search_term=<query>',
                'get_message': 'GET /api/messages/<id>',
                'list_messages': 'GET /api/messages',
                'redeem_coupon': 'POST /api/coupons/<code>/redeem',
                'list_coupons': 'GET /api/coupons',
                'register_user': 'POST /api/register',
                'login_user': 'POST /api/login',
                'database_info': 'GET /api/info'
            }
        },
        'configuration': {
            'mysql_host': MYSQL_HOST,
            'reset_interval_minutes': RESET_INTERVAL / 60,
            'automatic_reset': True
        }
    }), 200


# ============================================================================
# CTF Vulnerable API Endpoints
# ============================================================================

def get_db_connection():
    """Get MySQL connection for API endpoints (uses ctf_player credentials)."""
    return pymysql.connect(
        host=MYSQL_HOST,
        user='ctf_player',
        password='player_password_456',
        database='ctf_db',
        charset='utf8mb4',
        cursorclass=DictCursor
    )


@app.route('/api/search-secrets', methods=['GET'])
def search_secrets():
    """
    INTENTIONALLY VULNERABLE: SQL INJECTION
    Search secrets by keyword with unvalidated input.
    """
    search_term = request.args.get('search_term', '')
    
    if not search_term:
        return jsonify({'error': 'search_term parameter required'}), 400
    
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # INTENTIONALLY VULNERABLE: String concatenation allows SQL injection
            query = f"SELECT id, secret_name, secret_value FROM secrets WHERE secret_name LIKE '%{search_term}%'"
            logger.info(f"[SQL INJECTION] Executing: {query}")
            
            cursor.execute(query)
            results = cursor.fetchall()
        
        connection.close()
        
        return jsonify({
            'results': results,
            'count': len(results),
            'query_executed': query
        }), 200
        
    except pymysql.Error as e:
        return jsonify({
            'error': 'Database error',
            'details': str(e)
        }), 500


@app.route('/api/messages/<int:message_id>', methods=['GET'])
def get_message(message_id):
    """
    INTENTIONALLY VULNERABLE: IDOR
    Get message by ID without authorization check.
    """
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM messages WHERE id = %s", (message_id,))
            message = cursor.fetchone()
        
        connection.close()
        
        if message:
            return jsonify({
                'message': message,
                'vulnerability': 'IDOR - No authorization check'
            }), 200
        else:
            return jsonify({'error': 'Message not found'}), 404
            
    except pymysql.Error as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/messages', methods=['GET'])
def list_messages():
    """
    INTENTIONALLY VULNERABLE: IDOR (Mass data exposure)
    List all messages without filtering by user.
    """
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM messages")
            messages = cursor.fetchall()
        
        connection.close()
        
        return jsonify({
            'messages': messages,
            'count': len(messages),
            'vulnerability': 'IDOR - All messages visible'
        }), 200
        
    except pymysql.Error as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/coupons/<coupon_code>/redeem', methods=['POST'])
def redeem_coupon(coupon_code):
    """
    INTENTIONALLY VULNERABLE: RACE CONDITION
    Redeem coupon with non-atomic check-then-update.
    """
    data = request.get_json() or {}
    user_id = data.get('user_id', 1)
    
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Step 1: Check availability (NON-ATOMIC)
            cursor.execute("SELECT * FROM coupons WHERE code = %s", (coupon_code,))
            coupon = cursor.fetchone()
            
            if not coupon:
                connection.close()
                return jsonify({'error': 'Coupon not found'}), 404
            
            # VULNERABLE: Race condition window
            if coupon['current_uses'] >= coupon['max_uses']:
                connection.close()
                return jsonify({
                    'error': 'Coupon fully redeemed',
                    'current_uses': coupon['current_uses'],
                    'max_uses': coupon['max_uses']
                }), 400
            
            # Simulate processing delay
            time.sleep(0.1)
            
            # Step 2: Increment usage (SEPARATE QUERY)
            cursor.execute(
                "UPDATE coupons SET current_uses = current_uses + 1 WHERE code = %s",
                (coupon_code,)
            )
            connection.commit()
            
            # Fetch updated coupon
            cursor.execute("SELECT * FROM coupons WHERE code = %s", (coupon_code,))
            updated_coupon = cursor.fetchone()
        
        connection.close()
        
        return jsonify({
            'message': 'Coupon redeemed successfully',
            'coupon': updated_coupon,
            'vulnerability': 'RACE CONDITION - Non-atomic update'
        }), 200
        
    except pymysql.Error as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/coupons', methods=['GET'])
def list_coupons():
    """List all available coupons."""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM coupons")
            coupons = cursor.fetchall()
        
        connection.close()
        
        return jsonify({
            'coupons': coupons,
            'hint': 'Try redeeming with multiple concurrent requests'
        }), 200
        
    except pymysql.Error as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/register', methods=['POST'])
def register_user():
    """
    INTENTIONALLY VULNERABLE: SQL TRUNCATION ATTACK
    Register user with potential truncation.
    """
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'username and password required'}), 400
    
    import hashlib
    hashed_password = hashlib.md5(password.encode()).hexdigest()
    
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # VULNERABLE: No length validation before insert
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, hashed_password)
            )
            connection.commit()
            
            # Check what was actually stored
            cursor.execute(
                "SELECT username, LENGTH(username) as len FROM users WHERE username = %s",
                (username[:20],)
            )
            stored_user = cursor.fetchone()
        
        connection.close()
        
        return jsonify({
            'message': 'User registered',
            'submitted_username': username,
            'submitted_length': len(username),
            'stored_username': stored_user['username'] if stored_user else None,
            'stored_length': stored_user['len'] if stored_user else None,
            'warning': 'Username truncated if > 20 chars'
        }), 201
        
    except pymysql.Error as e:
        return jsonify({
            'error': 'Registration failed',
            'details': str(e)
        }), 400


@app.route('/api/login', methods=['POST'])
def login_user():
    """Login using GameServer credentials."""
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'username and password required'}), 400
    
    import hashlib
    hashed_password = hashlib.md5(password.encode()).hexdigest()
    
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE username = %s AND password = %s",
                (username, hashed_password)
            )
            user = cursor.fetchone()
        
        connection.close()
        
        if user:
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': user['id'],
                    'username': user['username']
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except pymysql.Error as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/info', methods=['GET'])
def database_info():
    """Get database schema and statistics."""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Get table list
            cursor.execute("SHOW TABLES")
            tables = [list(row.values())[0] for row in cursor.fetchall()]
            
            # Get record counts
            stats = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                stats[table] = cursor.fetchone()['count']
        
        connection.close()
        
        return jsonify({
            'database': 'ctf_db',
            'tables': tables,
            'record_counts': stats,
            'message': 'Database resets every 15 minutes'
        }), 200
        
    except pymysql.Error as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """
    Main application entry point.
    """
    logger.info("=" * 70)
    logger.info("🚀 CTF Database Reset Service Starting...")
    logger.info(f"   MySQL Host: {MYSQL_HOST}")
    logger.info(f"   Reset Interval: {RESET_INTERVAL} seconds ({RESET_INTERVAL/60:.1f} minutes)")
    logger.info(f"   Flask Port: {FLASK_PORT}")
    logger.info("=" * 70)
    
    # Wait for MySQL to be ready
    if not wait_for_database():
        logger.error("Cannot start service without database connection")
        sys.exit(1)
    
    # Perform initial reset
    logger.info("🔄 Performing initial database reset...")
    success, message = reset_database()
    if not success:
        logger.error(f"Initial reset failed: {message}")
        logger.warning("Service will continue, but database may not be in correct state")
    
    # Start periodic reset thread
    reset_thread = threading.Thread(target=periodic_reset_task, daemon=True)
    reset_thread.start()
    
    # Start Flask server
    logger.info(f"🌐 Starting Flask server on port {FLASK_PORT}...")
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=False)


if __name__ == '__main__':
    main()
