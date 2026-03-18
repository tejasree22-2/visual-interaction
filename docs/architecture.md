# Architecture Documentation

This document provides a comprehensive overview of the system architecture for the Projectile Motion Visual Simulator.

## Table of Contents

- [High-Level Architecture](#high-level-architecture)
- [System Components](#system-components)
- [Data Flow](#data-flow)
- [Component Details](#component-details)
- [API Architecture](#api-architecture)
- [Data Models](#data-models)
- [Caching Strategy](#caching-strategy)
- [Audio Processing Pipeline](#audio-processing-pipeline)
- [Project Structure](#project-structure)
- [Technology Decisions](#technology-decisions)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      Flutter Application                         │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │    │
│  │  │   UI Layer  │  │  Services   │  │   Models    │              │    │
│  │  │  (Widgets)  │  │ (API/TTS)   │  │   (Data)    │              │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ HTTP/REST
                                 │ CORS Enabled
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            SERVICE LAYER                                 │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                        Flask Backend                             │    │
│  │  ┌─────────────────────────────────────────────────────────┐    │    │
│  │  │                    Routes Layer                          │    │    │
│  │  │  ┌─────────────────┐  ┌─────────────────────────────┐  │    │    │
│  │  │  │ SimulationRoutes │  │ HealthCheck                 │  │    │    │
│  │  │  └─────────────────┘  └─────────────────────────────┘  │    │    │
│  │  └─────────────────────────────────────────────────────────┘    │    │
│  │  ┌─────────────────────────────────────────────────────────┐    │    │
│  │  │                  Services Layer                         │    │    │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │    │    │
│  │  │  │   Physics   │  │    Cache   │  │     Speech     │  │    │    │
│  │  │  │  Service    │  │  Service   │  │    Service     │  │    │    │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────┘  │    │    │
│  │  │  ┌─────────────────────────────────────────────────────┐│    │    │
│  │  │  │              Supabase Client                        ││    │    │
│  │  │  └─────────────────────────────────────────────────────┘│    │    │
│  │  └─────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
┌─────────────────────────┐     ┌─────────────────────────────────┐
│       DATA LAYER        │     │         EXTERNAL APIs           │
│                         │     │                                 │
│  ┌─────────────────┐   │     │  ┌─────────────────────────┐    │
│  │     Redis        │   │     │  │   Sarvam AI TTS API    │    │
│  │   (Cache)        │   │     │  │                        │    │
│  │   Port: 6379     │   │     │  │   Text-to-Speech       │    │
│  └─────────────────┘   │     │  │   Multilingual         │    │
│                        │     │  └─────────────────────────┘    │
│  ┌─────────────────┐   │     │                                 │
│  │   Supabase      │   │     │                                 │
│  │  (PostgreSQL)   │   │     │                                 │
│  │   Database      │   │     │                                 │
│  └─────────────────┘   │     │                                 │
└─────────────────────────┘     └─────────────────────────────────┘
```

---

## System Components

### 1. Frontend (Flutter)

| Component | Responsibility |
|-----------|---------------|
| `SimulationScreen` | Main UI screen, state management |
| `ControlPanel` | User input controls (angle, velocity, gravity) |
| `Graph2D` | 2D trajectory visualization |
| `Graph3D` | 3D trajectory visualization |
| `AudioChunkPlayer` | Audio playback controls |
| `SpeechService` | Text-to-Speech integration |
| `ApiService` | Backend communication |

**Technology Stack:**
- Flutter 3.x
- `flutter_tts` - Native TTS
- `http` - HTTP client
- `audioplayers` - Audio playback

### 2. Backend (Flask)

| Component | Responsibility |
|-----------|---------------|
| `app.py` | Application entry point, CORS setup |
| `simulation_routes.py` | API endpoint handlers |
| `physics_service.py` | Projectile motion calculations |
| `cache_service.py` | Redis caching operations |
| `speech_service.py` | Sarvam TTS integration |
| `supabase_client.py` | Database operations |

**Technology Stack:**
- Flask 2.0+
- Flask-CORS
- psycopg2 (PostgreSQL)
- redis-py
- requests
- pydub

### 3. Data Layer

| Component | Technology | Purpose |
|-----------|------------|---------|
| Cache | Redis | Simulation result caching |
| Database | Supabase (PostgreSQL) | Simulation history storage |
| Media Storage | Local filesystem | Generated audio files |

---

## Data Flow

### Simulation Request Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SIMULATION FLOW                                  │
└─────────────────────────────────────────────────────────────────────────┘

1. User Interaction
┌──────────────┐
│ User adjusts │
│ sliders      │
└──────┬───────┘
       │ angle, velocity, gravity
       ▼
2. Frontend Request
┌─────────────────────────────────────────┐
│ POST /api/simulation                    │
│ {                                       │
│   "angle": 45,                          │
│   "velocity": 20,                       │
│   "gravity": 9.81,                      │
│   "language": "te-IN"                   │
│ }                                       │
└────────────┬────────────────────────────┘
             │
             ▼
3. Cache Check
┌─────────────────────────────────────────┐
│ Generate cache key:                     │
│ MD5("45:20:9.81::te-IN")               │
│                                         │
│ Check Redis for existing result         │
└────────────┬────────────────────────────┘
             │
     ┌───────┴───────┐
     │               │
     ▼               ▼
  Cache HIT       Cache MISS
     │               │
     ▼               ▼
4a. Return        4b. Calculate
Cached Data          │
     │          ┌────┴────────────────────┐
     │          │                         │
     │          ▼                         ▼
     │    ┌─────────────┐         ┌─────────────┐
     │    │   Physics  │         │  Generate   │
     │    │  Service   │         │ Explanation │
     │    └─────────────┘         └──────┬──────┘
     │          │                         │
     │          │ trajectory,             │
     │          │ max_height,             ▼
     │          │ range,                  ┌─────────────┐
     │          │ time_of_flight         │   Sarvam   │
     │          │                        │  TTS API   │
     │          │                        └──────┬─────┘
     │          │                               │
     │          │              ┌────────────────┘
     │          │              │ audio_url
     │          └──────────────┤
     │                         ▼
     │               ┌─────────────┐
     │               │   Store    │
     │               │  in Redis  │
     │               └─────────────┘
     │                         │
     │                         ▼
     │               ┌─────────────────┐
     └──────────────►│   Response      │
                     │ JSON            │
                     └────────┬────────┘
                              │
                              ▼
5. Frontend Update
┌─────────────────────────────────────────┐
│ Update Graph2D/Graph3D with trajectory │
│ Update metrics display                 │
│ Enable audio playback                  │
└─────────────────────────────────────────┘
```

### Audio Processing Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      AUDIO PROCESSING FLOW                               │
└─────────────────────────────────────────────────────────────────────────┘

1. Text Generation
┌─────────────────────────────────────┐
│ SpeechService.generate_explanation_ │
│ text_telugu(angle, velocity, ...)   │
└──────────────────┬──────────────────┘
                   │ "Ipudu projectile..."
                   ▼
2. Chunking (Optional)
┌─────────────────────────────────────┐
│ generate_chunked_explanations()     │
│ - Split long text into chunks       │
│ - Max ~500 chars per Sarvam limit   │
└──────────────────┬──────────────────┘
                   │
     ┌─────────────┴─────────────┐
     │                           │
     ▼                           ▼
3a. Single Request          3b. Parallel Requests
(synthesize_speech)         (ThreadPoolExecutor)
     │                           │
     │                           ▼
     │                   ┌───────────────┐
     │                   │ Chunk 1: TTS  │
     │                   │ Chunk 2: TTS  │
     │                   │ Chunk 3: TTS  │
     │                   └───────┬───────┘
     │                           │
     └─────────────┬─────────────┘
                   │ audio_base64[]
                   ▼
4. Audio Conversion
┌─────────────────────────────────────┐
│ pydub.AudioSegment                  │
│ - Decode base64 WAV                │
│ - Export as MP3                    │
│ - Save to /media/                  │
└──────────────────┬──────────────────┘
                   │ /media/speech_xxx.mp3
                   ▼
5. Combine Chunks (if needed)
┌─────────────────────────────────────┐
│ combine_audio_chunks()             │
│ - Concatenate audio segments        │
│ - Add crossfade (150ms)            │
│ - Add silence between chunks        │
└──────────────────┬──────────────────┘
                   │ /media/combined_xxx.mp3
                   ▼
6. Return to Client
┌─────────────────────────────────────┐
│ {                                   │
│   "audio_url": "/media/combined_xxx"│
│ }                                   │
└─────────────────────────────────────┘
```

---

## Component Details

### Physics Service

The `physics_service.py` module implements projectile motion equations:

```python
def calculate_trajectory(angle, velocity, gravity):
    # Convert angle to radians
    angle_rad = math.radians(angle)
    
    # Calculate velocity components
    vx = velocity * math.cos(angle_rad)  # Horizontal
    vy = velocity * math.sin(angle_rad)  # Vertical
    
    # Time of flight
    time_of_flight = 2 * vy / gravity
    
    # Maximum height
    max_height = (vy ** 2) / (2 * gravity)
    
    # Range (horizontal distance)
    range_distance = velocity ** 2 * math.sin(2 * angle_rad) / gravity
    
    # Generate trajectory points
    trajectory = []
    for i in range(101):
        t = (i / 100) * time_of_flight
        x = vx * t
        y = vy * t - 0.5 * gravity * t ** 2
        y = max(0, y)  # Floor at y=0
        trajectory.append([x, y])
    
    return {
        "trajectory": trajectory,
        "max_height": max_height,
        "range": range_distance,
        "time_of_flight": time_of_flight
    }
```

**Key Physics Equations:**

| Parameter | Formula |
|-----------|---------|
| Horizontal Velocity | `vx = v * cos(θ)` |
| Vertical Velocity | `vy = v * sin(θ)` |
| Time of Flight | `T = 2v * sin(θ) / g` |
| Max Height | `H = v² * sin²(θ) / 2g` |
| Range | `R = v² * sin(2θ) / g` |

### Cache Service

Implements Redis caching with TTL:

```python
CACHE_TTL = 3600  # 1 hour

def _generate_cache_key(angle, velocity, gravity, custom_formula, language):
    key_str = f"{angle}:{velocity}:{gravity}:{custom_formula}:{language}"
    return f"simulation:{hashlib.md5(key_str.encode()).hexdigest()}"
```

**Cache Strategy:**
- **TTL:** 3600 seconds (1 hour)
- **Key Format:** `simulation:{MD5_HASH}`
- **Value:** JSON serialized simulation result
- **Invalidation:** Manual flush or TTL expiry

### Speech Service

Handles TTS via Sarvam AI:

```python
SARVAM_API_URL = "https://api.sarvam.ai/text-to-speech"

def synthesize_speech(text, target_language_code, save_file=True):
    # 1. Validate API key
    # 2. Truncate text if > 500 chars
    # 3. Call Sarvam API with retry logic
    # 4. Convert base64 audio to MP3
    # 5. Save to /media/ directory
    # 6. Return audio URL
```

**Supported Languages:**
- English (en-IN)
- Telugu (te-IN)

---

## API Architecture

### Endpoint Overview

```
/                           Flask App
├── /health                 Health Check
├── /media/<path>          Static Media Files
└── /api/
    ├── POST /simulation   Run Full Simulation
    ├── POST /simulate     Alias for /simulation
    ├── POST /chunks       Get Audio in Chunks
    ├── POST /chunk/<id>   Get Single Chunk Audio
    └── POST /combine-chunks  Combine Audio URLs
```

### API Request/Response Schemas

#### POST /api/simulation

**Request:**
```json
{
  "angle": 45,           // float, launch angle in degrees
  "velocity": 20,        // float, initial velocity in m/s
  "gravity": 9.81,       // float, gravitational acceleration
  "custom_formula": "",  // string (optional), custom formula
  "include_formula": false, // boolean, include formula in explanation
  "language": "te-IN"     // string, target language
}
```

**Response:**
```json
{
  "trajectory": [[0,0], [1.4, 1.4], ...],
  "max_height": 10.23,
  "range": 40.82,
  "time_of_flight": 2.87,
  "explanation_text": "Ipudu projectile motion...",
  "speech_audio_url": "/media/speech_abc123.mp3"
}
```

#### POST /api/chunks

**Request:** Same as `/simulation`

**Response:**
```json
{
  "chunks": [
    {
      "chunk_id": "main",
      "title": "Projectile Motion Basics",
      "title_te": "ప్రొజెక్టైల్ మోషన్ ప్రాథమికాలు",
      "text": "Let's learn about projectile...",
      "text_te": "Niiku projectile motion...",
      "audio_url_en": "/media/chunk_main_en.mp3",
      "audio_url_te": "/media/chunk_main_te.mp3"
    }
  ],
  "total_chunks": 1,
  "combined_audio_url": "/media/combined_xyz789.mp3"
}
```

### Error Handling

```python
# Standard error response format
{
  "error": "Error message description"
}

# HTTP Status Codes
200 - Success
400 - Bad Request (missing/invalid parameters)
404 - Resource Not Found
500 - Server Error
```

---

## Data Models

### Frontend Models

```dart
// lib/models/simulation_model.dart
class SimulationModel {
  double angle;        // 0-90 degrees
  double velocity;      // m/s
  double gravity;       // m/s²
  String? customFormula;
  bool includeFormula;
  String language;
  
  // Computed properties
  List<List<double>> trajectory;
  double maxHeight;
  double range;
  double timeOfFlight;
}
```

### Backend Models

```python
# No formal ORM; raw SQL with psycopg2

# simulations table
CREATE TABLE simulations (
    id SERIAL PRIMARY KEY,
    angle DECIMAL NOT NULL,
    velocity DECIMAL NOT NULL,
    gravity DECIMAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Audio Chunk Model

```python
class AudioChunk:
    chunk_id: str       # "main", "formula", etc.
    title: str          # English title
    title_te: str       # Telugu title
    text: str           # English explanation
    text_te: str        # Telugu explanation
    category: str       # "general", "formula", etc.
    audio_url_en: str   # English audio URL
    audio_url_te: str   # Telugu audio URL
```

---

## Caching Strategy

### Cache Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     CACHING STRATEGY                        │
└─────────────────────────────────────────────────────────────┘

Request ─► Generate Key ─► Check Redis ─► Cache HIT?
                                     │
                    ┌────────────────┴────────────────┐
                    │                              │
                  YES                              NO
                    │                              │
                    ▼                              ▼
            Return Cached                   Execute Pipeline:
            Response                       ┌─────────────────┐
                    │                     │ 1. Calculate   │
                    │                     │    Physics     │
                    │                     ├─────────────────┤
                    │                     │ 2. Generate    │
                    │                     │    Explanation │
                    │                     ├─────────────────┤
                    │                     │ 3. TTS API     │
                    │                     ├─────────────────┤
                    │                     │ 4. Store in DB │
                    │                     ├─────────────────┤
                    │                     │ 5. Cache Result │
                    │                     └────────┬────────┘
                    │                              │
                    │                              ▼
                    │                     Return & Cache
                    │                     Response
                    └──────────────────────────┘
```

### Cache Key Generation

```python
def _generate_cache_key(angle, velocity, gravity, custom_formula=None, language=None):
    key_str = f"{angle}:{velocity}:{gravity}:{custom_formula or ''}:{language or ''}"
    return f"simulation:{hashlib.md5(key_str.encode()).hexdigest()}"
```

**Example:**
```
Input: angle=45, velocity=20, gravity=9.81, language="te-IN"
Key:   simulation:a56ffc3e89ef2c3d7e2f1a0b5c4d3e2f
```

---

## Audio Processing Pipeline

### Sarvam API Integration

```python
# API Configuration
SARVAM_API_URL = "https://api.sarvam.ai/text-to-speech"

# Request Payload
payload = {
    "inputs": [text],              # Max 500 characters
    "target_language_code": "te-IN", # or "en-IN"
    "speaker": "shruti",
    "model": "bulbul:v3",
    "speech_sample_rate": 16000
}

# Headers
headers = {
    "api-subscription-key": SARVAM_API_KEY,
    "Content-Type": "application/json"
}
```

### Audio Processing Steps

1. **Text Preparation**
   - Convert formulas to speech-readable format
   - Convert numbers to words
   - Handle multilingual text (English/Telugu)

2. **API Call**
   - Retry logic (3 attempts)
   - Timeout: 60 seconds

3. **Audio Conversion**
   - Decode base64 WAV
   - Convert to MP3 (64kbps)
   - Save to `backend/media/`

4. **Chunking (for long explanations)**
   - Split into ~500 char chunks
   - Parallel synthesis via ThreadPool
   - Crossfade concatenation (150ms)

---

## Project Structure

```
visual-interaction/
├── backend/
│   ├── app.py                      # Flask app entry point
│   ├── routes/
│   │   └── simulation_routes.py    # API endpoints
│   ├── services/
│   │   ├── physics_service.py       # Physics calculations
│   │   ├── cache_service.py         # Redis caching
│   │   ├── speech_service.py       # Sarvam TTS
│   │   └── supabase_client.py      # Database operations
│   ├── media/                       # Generated audio files
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── lib/
│   │   ├── main.dart                # App entry point
│   │   ├── screens/
│   │   │   └── simulation_screen.dart
│   │   ├── widgets/
│   │   │   ├── control_panel.dart
│   │   │   ├── graph_2d.dart
│   │   │   ├── graph_3d.dart
│   │   │   ├── view_toggle.dart
│   │   │   └── audio_chunk_player.dart
│   │   ├── services/
│   │   │   ├── api_service.dart
│   │   │   └── speech_service.dart
│   │   └── models/
│   │       └── simulation_model.dart
│   ├── pubspec.yaml
│   └── test/
├── docs/
│   ├── setup-guide.md
│   └── architecture.md
├── entire.yaml                      # Entire CLI config
├── .env                            # Environment variables
├── requirements.txt
└── README.md
```

---

## Technology Decisions

### Why Flask?

| Pros | Cons |
|------|------|
| Lightweight, simple | Less features than Django |
| Easy to learn | Less built-in auth |
| Good for small-mid apps | Smaller ecosystem |

### Why Flutter?

| Pros | Cons |
|------|------|
| Single codebase | Larger app size |
| Native performance | Dart learning curve |
| Rich UI components | Smaller community than React |

### Why Redis?

| Pros | Cons |
|------|------|
| Sub-millisecond latency | In-memory (data loss on crash) |
| Simple key-value API | Not ideal for complex queries |
| Supports TTL | Requires additional persistence setup |

### Why Supabase?

| Pros | Cons |
|------|------|
| Managed PostgreSQL | Vendor lock-in |
| Free tier available | Latency for distant regions |
| Real-time subscriptions | Rate limits on free tier |

### Why Sarvam AI?

| Pros | Cons |
|------|------|
| Indian languages support | API rate limits |
| Free tier available | Dependency on third-party |
| Good quality TTS | Quota restrictions |

---

## Security Considerations

1. **API Keys**: Stored in `.env`, never committed to git
2. **CORS**: Enabled for all origins in development
3. **Database**: Connection via environment variables
4. **Input Validation**: Server-side validation in routes
5. **Audio Files**: Served locally, not from cloud

---

## Performance Optimizations

1. **Caching**: Redis reduces redundant calculations
2. **Chunking**: Parallel audio processing
3. **Lazy Loading**: Audio generated on-demand
4. **Compression**: MP3 at 64kbps for reasonable quality/size

---

## Scalability Considerations

### Horizontal Scaling

```
                    ┌─────────────┐
                    │   Nginx     │
                    │  Load Balancer│
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
   ┌──────────┐      ┌──────────┐      ┌──────────┐
   │ Backend 1 │      │ Backend 2 │      │ Backend 3 │
   └─────┬────┘      └─────┬────┘      └─────┬────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        ┌────────┐   ┌────────┐   ┌────────┐
        │  Redis  │   │  Redis │   │  Redis │
        │ Cluster │   │ Cluster │   │ Cluster │
        └────────┘   └────────┘   └────────┘
```

### Database Scaling

- Use connection pooling
- Read replicas for queries
- Index on `simulations.created_at`

---

## Monitoring & Logging

### Backend Logging

```python
import logging
logger = logging.getLogger(__name__)

@app.route('/api/simulation')
def simulate():
    logger.info(f"Slider Changed: angle={angle}, velocity={velocity}")
    # ...
```

### Health Checks

```python
@app.route('/health')
def health():
    return {'status': 'healthy'}
```

---

## Future Enhancements

1. **WebSocket Support**: Real-time simulation updates
2. **More Languages**: Hindi, Tamil, Kannada TTS
3. **Export**: Save trajectory as CSV/PDF
4. **Social**: Share simulations
5. **Analytics**: Track user interactions
