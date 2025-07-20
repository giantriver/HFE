# HFE Pose Analysis System - Architecture Documentation

## System Overview

The HFE (Human Factors Engineering) Pose Analysis System is a web-based application that analyzes human posture from uploaded images using MediaPipe and provides ergonomic scoring based on arm positioning and angles.

## Architecture Components

### High-Level Architecture

```
┌─────────────────┐    HTTP/REST API    ┌─────────────────┐
│                 │ ◄─────────────────► │                 │
│   Frontend      │                     │   Backend       │
│   (Nuxt.js)     │                     │   (Flask)       │
│                 │                     │                 │
└─────────────────┘                     └─────────────────┘
                                                │
                                                ▼
                                        ┌─────────────────┐
                                        │   MediaPipe     │
                                        │   Pose Model    │
                                        └─────────────────┘
```

### Technology Stack

#### Frontend
- **Framework**: Nuxt.js 3 (Vue.js)
- **UI Library**: PrimeVue with Tailwind CSS
- **Build Tool**: Vite
- **Language**: TypeScript/JavaScript

#### Backend
- **Framework**: Flask with Flask-AppBuilder
- **API Style**: REST API
- **Image Processing**: OpenCV + MediaPipe
- **Data Format**: JSON responses with base64 images
- **Language**: Python 3.12+

#### Core Dependencies
- **MediaPipe**: Google's ML framework for pose detection
- **OpenCV**: Computer vision library for image processing
- **NumPy**: Numerical computations for angle calculations
- **Pillow**: Python image processing

## System Flow

### 1. Image Upload Flow
```
User selects image → Frontend validates → FormData created → API call to backend
```

### 2. Processing Flow
```
Backend receives image → MediaPipe processes → Pose landmarks extracted → 
Angle calculations → Scoring algorithm → Image annotation → Response generation
```

### 3. Response Flow
```
Backend returns JSON → Frontend displays results → Original vs Processed comparison → 
Click-to-enlarge modal
```

## Directory Structure

```
HFE/
├── web/
│   ├── frontend/           # Nuxt.js application
│   │   ├── pages/
│   │   │   └── index.vue   # Main pose analysis interface
│   │   ├── nuxt.config.ts  # Nuxt configuration
│   │   └── package.json    # Frontend dependencies
│   └── backend/            # Flask application
│       ├── app/
│       │   ├── __init__.py # Flask app initialization
│       │   └── views.py    # API endpoints
│       ├── config.py       # Flask configuration
│       ├── run.py         # Development server
│       └── pyproject.toml  # Backend dependencies
├── code/                   # Original research code
│   └── pose_score_from_image.ipynb
└── ai_docs/               # Technical documentation
```

## Port Configuration

- **Frontend Development**: Port 3008 (Nuxt.js dev server)
- **Backend API**: Port 5008 (Flask development server)
- **Proxy Configuration**: Frontend proxies `/api` requests to backend

## Data Flow

### Input
- Image files (PNG, JPG, etc.)
- Uploaded via HTML file input

### Processing
1. **Image Conversion**: PIL → NumPy array → OpenCV format
2. **Pose Detection**: MediaPipe extracts 33 body landmarks
3. **Angle Calculation**: Vector mathematics for arm angles
4. **Scoring**: Ergonomic evaluation based on angle ranges
5. **Visualization**: Red landmarks and connections drawn on image

### Output
```json
{
  "left_arm": {
    "theta_raise": 100.5,
    "theta_elbow": 159.2,
    "desc": "90° < θ_raise < 170°",
    "score": 7
  },
  "right_arm": { /* similar structure */ },
  "best_side": "LEFT",
  "best_score": { /* best arm data */ },
  "processed_image": "data:image/png;base64,..."
}
```

## Security Considerations

- **CORS**: Configured for specific frontend origins
- **File Validation**: Image type checking before processing
- **Error Handling**: Graceful failure with error messages
- **No File Storage**: Images processed in memory only

## Performance Characteristics

- **GPU Acceleration**: NVIDIA CUDA support via MediaPipe
- **Processing Time**: ~2-3 seconds per image
- **Memory Usage**: Images processed in memory, no persistent storage
- **Concurrent Requests**: Flask development server (single-threaded)

## Scalability Notes

- Current setup suitable for development/testing
- For production: Consider WSGI server (Gunicorn), Redis for caching
- GPU memory management for multiple concurrent requests
- Database integration for result storage if needed

---
*Generated: 2025-01-20*
*Last Updated: 2025-01-20*