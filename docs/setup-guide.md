# Setup Guide

This guide provides detailed instructions for setting up the Projectile Motion Visual Simulator in various environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Setup](#environment-setup)
- [Backend Setup](#backend-setup)
- [Frontend Setup](#frontend-setup)
- [Database Setup](#database-setup)
- [Redis Setup](#redis-setup)
- [Entire CLI Setup](#entire-cli-setup)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.8+ | Backend runtime |
| Flutter SDK | 3.x+ | Frontend development |
| Redis | 6.x+ | Caching layer |
| PostgreSQL | 14+ | Database (via Supabase) |
| Git | 2.x+ | Version control |

### Optional Software

| Software | Purpose |
|----------|---------|
| Docker | Containerized deployment |
| VS Code | Code editor with extensions |
| Postman | API testing |

---

## Quick Start

### Option 1: Using Entire CLI (Recommended)

```bash
# Install Entire CLI
curl -sSL https://entire.io/install | bash

# Clone and setup
cd visual-interaction
entire up
```

### Option 2: Manual Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
python app.py

# Frontend (in new terminal)
cd frontend
flutter pub get
flutter run
```

---

## Environment Setup

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd visual-interaction
```

### Step 2: Create Environment File

Create a `.env` file in the project root:

```env
# Supabase Configuration (PostgreSQL connection string)
SUPABASE_CONNECTION_STRING=postgresql://postgres.qaumfxltmkrqzlhmlmel:password@host:5432/postgres

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Sarvam AI Configuration (for Text-to-Speech)
SARVAM_API_KEY=your_sarvam_api_key

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=your_secret_key_here

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:5000
```

### Step 3: Get Required API Keys

#### Supabase (Database)

1. Go to [Supabase](https://supabase.com)
2. Create a new project or use existing
3. Navigate to Settings → Database
4. Copy the Connection string (URI format)

#### Sarvam AI (Text-to-Speech)

1. Go to [Sarvam AI Dashboard](https://dashboard.sarvam.ai)
2. Sign up for free tier (5000 characters/month)
3. Generate API key
4. Add to `.env` file

---

## Backend Setup

### Manual Installation

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Verify Backend Installation

```bash
# Run the backend
python app.py
```

Expected output:
```
* Running on http://0.0.0.0:5000
* Debug mode: on
```

### Test Backend Endpoints

```bash
# Health check
curl http://localhost:5000/health

# Run simulation
curl -X POST http://localhost:5000/api/simulation \
  -H "Content-Type: application/json" \
  -d '{"angle": 45, "velocity": 20, "gravity": 9.81}'
```

### Backend Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| flask | 2.0+ | Web framework |
| flask-cors | 3.0+ | CORS handling |
| psycopg2-binary | 2.9+ | PostgreSQL adapter |
| redis | 4.5+ | Redis client |
| requests | 2.28+ | HTTP client |
| python-dotenv | 1.0+ | Environment variables |
| pydub | 0.25+ | Audio processing |

---

## Frontend Setup

### Manual Installation

```bash
# Navigate to frontend directory
cd frontend

# Get dependencies
flutter pub get

# Run the app
flutter run
```

### Flutter Requirements

```bash
# Check Flutter version
flutter --version

# Ensure Flutter is properly configured
flutter doctor
```

### Supported Platforms

| Platform | Support Level |
|----------|---------------|
| Android | Full |
| iOS | Full |
| Web | Full |
| Windows | Full |
| macOS | Full |
| Linux | Full |

### Build for Production

```bash
# Android APK
flutter build apk --release

# iOS
flutter build ios --release

# Web
flutter build web
```

---

## Database Setup

### Using Supabase (Cloud)

1. **Create Supabase Project**
   - Go to [supabase.com](https://supabase.com)
   - Create new project
   - Wait for database to provision

2. **Configure Connection**
   - Navigate to Settings → Database
   - Copy Connection string
   - Update `.env` file

3. **Create Tables**

   Connect to your database and run:

   ```sql
   CREATE TABLE simulations (
       id SERIAL PRIMARY KEY,
       angle DECIMAL NOT NULL,
       velocity DECIMAL NOT NULL,
       gravity DECIMAL NOT NULL,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

### Local PostgreSQL Setup

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database
sudo -u postgres createdb projectile_sim

# Create user
sudo -u postgres createuser -s appuser

# Set password
sudo -u postgres psql -c "ALTER USER appuser PASSWORD 'your_password';"

# Grant privileges
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE projectile_sim TO appuser;"
```

Connection string for local setup:
```
postgresql://appuser:your_password@localhost:5432/projectile_sim
```

---

## Redis Setup

### Local Installation

#### Ubuntu/Debian

```bash
# Install Redis
sudo apt update
sudo apt install redis-server

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test connection
redis-cli ping
```

Expected response: `PONG`

#### macOS

```bash
# Using Homebrew
brew install redis
brew services start redis

# Test connection
redis-cli ping
```

#### Windows

Use [WSL2](https://docs.microsoft.com/en-us/windows/wsl/) or Docker:

```bash
docker run -d -p 6379:6379 redis:alpine
```

### Redis Configuration

Default settings (usually work out of the box):
- Host: `localhost`
- Port: `6379`
- Database: `0`

### Verify Redis Connection

```python
# Test with Python
python -c "import redis; r = redis.from_url('redis://localhost:6379/0'); print(r.ping())"
```

Expected output: `True`

---

## Entire CLI Setup

[Entire CLI](https://entire.io) provides infrastructure orchestration for this project.

### Installation

```bash
# Linux/macOS
curl -sSL https://entire.io/install | bash

# Or via npm
npm install -g @entire/cli
```

### Configuration

The `entire.yaml` file defines the infrastructure:

```yaml
version: '1.0'
name: visual-interaction

services:
  frontend:
    type: flutter
    path: ./frontend
    
  backend:
    type: flask
    path: ./backend
    port: 5000
    env:
      - FLASK_ENV=development
      - FLASK_DEBUG=true
      
  redis:
    type: redis
    port: 6379

env_file: .env
```

### Commands

```bash
# Start all services
entire up

# Stop all services
entire down

# View logs
entire logs

# Check status
entire status
```

---

## Troubleshooting

### Common Issues

#### 1. Redis Connection Error

**Error:**
```
Redis connection failed: Error 111 connecting to localhost:6379
```

**Solution:**
```bash
# Check if Redis is running
sudo systemctl status redis-server

# Start Redis if not running
sudo systemctl start redis-server
```

#### 2. Supabase Connection Error

**Error:**
```
psycopg2.OperationalError: could not connect to server
```

**Solution:**
1. Check your connection string format
2. Verify Supabase project is active
3. Whitelist your IP address in Supabase settings
4. Check if password contains special characters (escape them)

#### 3. Flutter Build Error

**Error:**
```
Could not resolve: packages/flutter_tts/flutter_tts.dart
```

**Solution:**
```bash
cd frontend
flutter pub get
flutter clean
flutter pub get
```

#### 4. CORS Error

**Error:**
```
Access-Control-Allow-Origin missing
```

**Solution:**
The backend has CORS enabled by default. If issues persist, verify:
```python
# In backend/app.py
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

#### 5. Port Already in Use

**Error:**
```
OSError: [Errno 98] Address already in use
```

**Solution:**
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>
```

#### 6. Missing Environment Variables

**Error:**
```
SUPABASE_CONNECTION_STRING not found in .env
```

**Solution:**
1. Ensure `.env` file exists in project root
2. Verify variable names match exactly
3. Restart backend after creating/modifying `.env`

#### 7. Sarvam API Error

**Error:**
```
API key missing
```

**Solution:**
1. Get API key from [Sarvam Dashboard](https://dashboard.sarvam.ai)
2. Add to `.env`: `SARVAM_API_KEY=your_key`
3. Restart backend

---

## Development Workflow

### Running Development Environment

```bash
# Terminal 1: Backend
cd backend
python app.py

# Terminal 2: Frontend
cd frontend
flutter run
```

### Running Tests

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
flutter test
```

### Code Style

**Backend (Python):**
- Follow PEP 8
- Use type hints where possible

**Frontend (Flutter):**
- Follow Dart style guide
- Use `flutter_lints`

---

## Deployment

### Docker Deployment

```dockerfile
# backend/Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

### Cloud Deployment Options

| Platform | Service | Notes |
|----------|---------|-------|
| Railway | Full stack | Easy deployment |
| Render | Backend | Python support |
| Vercel | Frontend | Flutter web |
| Supabase | Database | Included |
| Redis Cloud | Redis | Managed Redis |

---

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SUPABASE_CONNECTION_STRING` | Yes | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Yes | Redis connection URL | `redis://localhost:6379/0` |
| `SARVAM_API_KEY` | Yes | TTS API key | `sk_xxxxxx` |
| `FLASK_ENV` | No | Flask environment | `development` |
| `FLASK_DEBUG` | No | Enable debug mode | `true` |
| `SECRET_KEY` | No | Flask secret key | `your_secret` |
| `NEXT_PUBLIC_API_URL` | No | Frontend API URL | `http://localhost:5000` |
