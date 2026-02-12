#!/usr/bin/env python3
"""
Local version of reset_script.py for running outside Docker container.
This script sets the correct configuration for connecting to the containerized MySQL from the host.
"""

import os
import sys

# Set configuration for local execution
os.environ['MYSQL_HOST'] = 'localhost'
os.environ['MYSQL_ROOT_PASSWORD'] = 'super_secure_root_password_123'
os.environ['RESET_INTERVAL'] = '900'
os.environ['INIT_SQL_PATH'] = os.path.join(os.path.dirname(__file__), 'init.sql')
os.environ['PYTHONUNBUFFERED'] = '1'

# Import and run the main script
if __name__ == '__main__':
    print("=" * 70)
    print("🏠 Running reset_script.py in LOCAL mode")
    print(f"   MySQL Host: {os.environ['MYSQL_HOST']}")
    print(f"   Init SQL Path: {os.environ['INIT_SQL_PATH']}")
    print("=" * 70)
    print()
    
    # Import the original script (this will execute it)
    import reset_script
