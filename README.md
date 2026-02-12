# 🎯 Vulnerable CTF Database Server

A **portable, Dockerized MySQL environment** designed for Capture The Flag (CTF) educational platforms. This system includes purposefully vulnerable database configurations and an automated self-healing mechanism for continuous challenge availability.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Vulnerabilities](#vulnerabilities)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Security Considerations](#security-considerations)

---

## 🎓 Overview

This project provides a complete, containerized database environment specifically designed for security education and CTF challenges. It demonstrates common web application vulnerabilities in a controlled, resettable environment.

### Key Components

- **MySQL 5.7 Database**: Configured with intentionally vulnerable settings
- **Automated Reset Service**: Python-based watchdog that resets the database every 15 minutes
- **Manual Reset API**: HTTP endpoint for on-demand database resets
- **Pre-seeded Data**: Users, secrets, messages, and coupons with embedded flags

---

## ✨ Features

- ✅ **Portable**: Runs anywhere Docker is available (Windows, Linux, macOS)
- 🔄 **Self-Healing**: Automatic database reset every 15 minutes
- 🔧 **Manual Control**: HTTP API for on-demand resets
- 🎯 **Educational**: Contains 4+ vulnerability types for learning
- 📊 **Monitoring**: Health check endpoints and comprehensive logging
- 🚀 **Quick Deploy**: Single `docker-compose up` command

---

## 🚀 Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 2GB available RAM

### Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd GameServer
   ```

2. **Start the platform**:
   ```bash
   docker-compose up -d
   ```

3. **Verify services are running**:
   ```bash
   docker-compose ps
   ```

4. **Check reset service health**:
   ```bash
   curl http://localhost:5001/health
   ```

### Connection Details

#### MySQL Database
- **Host**: `localhost`
- **Port**: `3306`
- **Database**: `ctf_db`
- **User**: `ctf_player`
- **Password**: `player_password_456`

#### Root Access (for reset service only)
- **User**: `root`
- **Password**: `super_secure_root_password_123`

#### Reset API
- **URL**: `http://localhost:5001`
- **Health Check**: `GET /health`
- **Manual Reset**: `POST /reset`

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Network (ctf_network)            │
│                                                             │
│  ┌──────────────────┐              ┌───────────────────┐  │
│  │   MySQL 5.7      │              │  Reset Service    │  │
│  │   Container      │◄─────────────┤  (Python/Flask)   │  │
│  │                  │              │                   │  │
│  │  - ctf_db        │              │  - Auto Reset     │  │
│  │  - sql_mode=''   │              │    (15 min)       │  │
│  │  - Port 3306     │              │  - HTTP API       │  │
│  │                  │              │  - Port 5001      │  │
│  └──────────────────┘              └───────────────────┘  │
│          │                                   │              │
└──────────┼───────────────────────────────────┼──────────────┘
           │                                   │
           │                                   │
    ┌──────▼──────┐                     ┌─────▼─────┐
    │   MySQL     │                     │   HTTP    │
    │ Application │                     │ Requests  │
    │  (Port)     │                     │ (cURL)    │
    └─────────────┘                     └───────────┘
```

### Service Flow

1. **Startup**: MySQL initializes with `init.sql`, creating tables and seeding data
2. **Reset Service**: Connects to MySQL and performs an initial database reset
3. **Monitoring**: Reset service continuously monitors and logs activity
4. **Auto-Reset**: Every 15 minutes, the database is dropped and recreated
5. **Manual Reset**: Admins can trigger resets via HTTP POST to `/reset`

---

## 🔓 Vulnerabilities

This platform includes **intentional vulnerabilities** for educational purposes:

### 1. SQL Injection
**Target**: `secrets` table  
**Description**: Unvalidated input allows direct SQL command execution  
**Example Attack**:
```sql
' OR 1=1 --
' UNION SELECT secret_value FROM secrets --
```

### 2. SQL Truncation Attack
**Target**: `users` table  
**Description**: 20-character username limit enables privilege escalation  
**Example Attack**:
```python
# Register as: "admin              x" (20 chars)
# MySQL truncates to "admin" on constraint check
# Allows duplicate 'admin' user creation
```

### 3. Insecure Direct Object Reference (IDOR)
**Target**: `messages` table  
**Description**: Sequential IDs allow unauthorized access to other users' messages  
**Example Attack**:
```sql
SELECT * FROM messages WHERE id = 1;  -- Access any message by guessing ID
```

### 4. Race Condition
**Target**: `coupons` table  
**Description**: Non-atomic update operations allow multiple redemptions  
**Example Attack**:
```bash
# Send multiple concurrent redemption requests
# current_uses increments may race, bypassing max_uses check
```

### Database Tables

#### `users` (6 users)
- **admin**: `admin123` ⚠️ Admin account
- **demo_user**: `demo123`
- **alice**, **bob**, **charlie**, **eve**: `password123`

#### `secrets` (5 flags)
- `FLAG{SQL_INJECTION_MASTER}`
- `FLAG{HIDDEN_ADMIN_CREDENTIALS}`
- `FLAG{Y0U_F0UND_TH3_K3Y}`

#### `messages` (8 messages)
Contains sensitive admin verification codes and reward codes

#### `coupons` (5 coupons)
- `SUMMER2024`: 50% off (1 use max)
- `LIMITEDEDITION`: 90% off (1 use max)

---

## 📡 API Reference

### Reset Service Endpoints

#### `GET /health`
Health check endpoint for monitoring.

**Response**:
```json
{
  "status": "healthy",
  "service": "CTF Database Reset Service",
  "last_reset": "2024-02-11T10:30:00",
  "reset_count": 5,
  "seconds_since_last_reset": 450.5,
  "reset_interval_seconds": 900
}
```

#### `POST /reset`
Manually trigger a database reset.

**Request**:
```bash
curl -X POST http://localhost:5001/reset
```

**Response**:
```json
{
  "status": "success",
  "message": "Database reset completed successfully (Reset #6)",
  "reset_count": 6,
  "timestamp": "2024-02-11T10:35:00"
}
```

#### `GET /`
Service information and available endpoints.

**Response**:
```json
{
  "service": "CTF Database Reset & Watchdog Service",
  "version": "1.0.0",
  "endpoints": {
    "health_check": "GET /health",
    "manual_reset": "POST /reset",
    "info": "GET /"
  }
}
```

---

## ⚙️ Configuration

### Environment Variables

Edit [docker-compose.yml](docker-compose.yml) to customize:

```yaml
# Database credentials
MYSQL_ROOT_PASSWORD: super_secure_root_password_123

# Reset interval (in seconds)
RESET_INTERVAL: 900  # 15 minutes
# Options: 300 (5min), 600 (10min), 1800 (30min)
```

### MySQL Configuration

The database runs with these intentionally insecure settings:

```bash
--sql-mode=''  # Disables strict mode (enables truncation)
--max-connections=200
--default-authentication-plugin=mysql_native_password
```

### Persistent vs. Ephemeral Storage

**Default**: Persistent storage via Docker volume `mysql_data`

**To make fully ephemeral** (database resets on container restart):
```yaml
# Comment out in docker-compose.yml:
# volumes:
#   - mysql_data:/var/lib/mysql
```

---

## 💻 Usage Examples

### Connect to MySQL

**Using MySQL CLI**:
```bash
mysql -h 127.0.0.1 -P 3306 -u ctf_player -pplayer_password_456 ctf_db
```

**Using Python**:
```python
import pymysql

connection = pymysql.connect(
    host='localhost',
    user='ctf_player',
    password='player_password_456',
    database='ctf_db'
)

with connection.cursor() as cursor:
    cursor.execute("SELECT * FROM secrets")
    print(cursor.fetchall())
```

**Using Node.js**:
```javascript
const mysql = require('mysql2');

const connection = mysql.createConnection({
  host: 'localhost',
  user: 'ctf_player',
  password: 'player_password_456',
  database: 'ctf_db'
});

connection.query('SELECT * FROM users', (err, results) => {
  console.log(results);
});
```

### Trigger Manual Reset

```bash
# Simple reset
curl -X POST http://localhost:5001/reset

# With formatted output
curl -X POST http://localhost:5001/reset | python -m json.tool
```

### Monitor Service Health

```bash
# Check health status
curl http://localhost:5001/health

# Monitor logs
docker-compose logs -f refresher

# Check database status
docker-compose logs -f db
```

### Stop and Clean Up

```bash
# Stop services
docker-compose down

# Stop and remove volumes (full cleanup)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

---

## 🔒 Security Considerations

### ⚠️ WARNING: Educational Use Only

This platform contains **intentional security vulnerabilities** and should **NEVER** be deployed in production or on public networks.

### Safe Usage Guidelines

1. ✅ **Isolated Network**: Run only on isolated/internal networks
2. ✅ **Firewall**: Block external access to ports 3306 and 5001
3. ✅ **Local Only**: Use for local CTF labs and training environments
4. ✅ **Supervised**: Deploy only in controlled educational settings
5. ❌ **No Public Internet**: Never expose to the public internet
6. ❌ **No Real Data**: Never use with production or sensitive data

### Network Security

**Recommended Firewall Rules**:
```bash
# Windows (allow local only)
netsh advfirewall firewall add rule name="CTF MySQL" dir=in action=allow protocol=TCP localport=3306 remoteip=127.0.0.1

# Linux (iptables)
iptables -A INPUT -p tcp --dport 3306 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 3306 -j DROP
```

### Docker Network Isolation

The platform uses a dedicated bridge network (`ctf_network`) to isolate services. Only explicitly mapped ports are accessible from the host.

---

## 🛠️ Troubleshooting

### Database Not Starting

```bash
# Check logs
docker-compose logs db

# Verify volume permissions (Linux)
sudo chown -R $(whoami) ./

# Remove old volumes
docker-compose down -v
docker-compose up -d
```

### Reset Service Connection Issues

```bash
# Check if DB is healthy
docker-compose ps

# Verify network connectivity
docker exec ctf_db_refresher ping db

# Check environment variables
docker exec ctf_db_refresher env | grep MYSQL
```

### Port Already in Use

```bash
# Find process using port
# Windows
netstat -ano | findstr :3306

# Linux/Mac
lsof -i :3306

# Change port in docker-compose.yml
ports:
  - "3307:3306"  # Use different host port
```

---

## 📚 Additional Resources

- [MySQL 5.7 Documentation](https://dev.mysql.com/doc/refman/5.7/en/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

## 📝 License

This project is provided for **educational purposes only**. Use at your own risk.

---

## 🤝 Contributing

This is an educational project. If you find issues or have suggestions for additional vulnerability scenarios, please submit feedback.

---

**Built with ❤️ for Security Education**
