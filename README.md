# Projectile Motion Visual Simulator

An educational physics visualization application that helps students understand **projectile motion** through interactive simulation.

## Overview

The goal of this project is to provide a **visual learning tool** for students (Class 9–12) to understand projectile motion concepts such as trajectory, angle of projection, velocity, and gravity.

## Features

- Adjust launch angle
- Adjust initial velocity
- Visualize projectile trajectory
- Display maximum height
- Display horizontal range
- Interactive physics visualization
- Real-time calculations

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Flutter |
| Backend | Python / Flask |
| Database | PostgreSQL (Supabase) |
| Caching | Redis |
| Environment | Entire CLI (entire.io) |

## Prerequisites

- Flutter SDK (3.x or later)
- Python 3.8+
- Redis Server
- PostgreSQL (or Supabase cloud)

## Installation

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the root directory:

```env
SUPABASE_CONNECTION_STRING=postgresql://user:password@host:5432/db
REDIS_URL=redis://localhost:6379/0
SARVAM_API_KEY=your_api_key
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=your_secret_key
NEXT_PUBLIC_API_URL=http://localhost:5000
```

### Frontend Setup

```bash
cd frontend
flutter pub get
flutter run
```

## Running the Application

### Start Backend

```bash
cd backend
python app.py
```

The API server will start at `http://localhost:5000`.

### Start Frontend

```bash
cd frontend
flutter run
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/simulation` | Run simulation |

## Architecture

```
┌─────────────┐
│ Flutter App │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Backend API │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Redis Cache │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Database   │
└─────────────┘
```

## Project Structure

```
visual-interaction/
├── backend/
│   ├── app.py           # Flask application entry point
│   ├── routes/          # API routes
│   ├── services/        # Business logic
│   ├── media/           # Media files
│   └── requirements.txt
├── frontend/
│   ├── lib/             # Flutter source code
│   ├── pubspec.yaml
│   └── README.md
├── docs/                # Documentation
├── .env                 # Environment variables
├── requirements.txt     # Python dependencies
└── README.md
```

## Physics Concept

Projectile motion describes the motion of an object thrown into the air under the influence of gravity.

**Key Parameters:**
- Angle of projection
- Initial velocity
- Gravitational acceleration

**Key Equations:**
- Maximum Height: `H = (v² * sin²θ) / (2g)`
- Horizontal Range: `R = (v² * sin2θ) / g`
- Time of Flight: `T = (2v * sinθ) / g`

## Development

### Running in Development Mode

```bash
# Backend with debug
python app.py

# Frontend with hot reload
flutter run
```

## License

This project is for educational purposes.
