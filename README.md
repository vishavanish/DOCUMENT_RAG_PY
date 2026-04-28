# News Collection API

Automated news collection system using Flask, MySQL, Celery, and Redis.

## Setup Instructions

### 1. Prerequisites
- Python 3.8+
- MySQL Server
- Redis Server

### 2. Installation
```bash
# Run setup script
./setup.sh

# Or manual setup:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Database Setup
```bash
# Start MySQL and run as root:
mysql -u root -p < setup_database.sql
```

### 4. Start Services
```bash
# Option 1: Use run script
./run_services.sh

# Option 2: Manual start (in separate terminals)
redis-server
celery -A tasks worker --loglevel=info
celery -A tasks beat --loglevel=info
python app.py
```

## API Endpoints

- `GET /` - Health check
- `GET /init-db` - Initialize database tables
- `GET /fetch-news` - Manually trigger news fetch
- `GET /articles` - Get latest articles

## Features

- ✅ Secure API key management via environment variables
- ✅ MySQL database with unique constraints
- ✅ Automated news fetching every minute
- ✅ Duplicate prevention
- ✅ Dedicated database user with restricted permissions
- ✅ Background task processing with Celery
- ✅ Redis message broker

## Configuration

Edit `.env` file to customize:
- NEWS_API_KEY
- MySQL credentials
- Redis URL