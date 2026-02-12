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
            'info': 'GET /'
        },
        'configuration': {
            'mysql_host': MYSQL_HOST,
            'reset_interval_minutes': RESET_INTERVAL / 60,
            'automatic_reset': True
        }
    }), 200


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
