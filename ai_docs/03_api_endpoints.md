# API Endpoints and Data Structures Documentation

## Overview

This document describes the REST API endpoints, request/response formats, and data structures used in the HFE Pose Analysis System.

## Base Configuration

### API Base URL
- **Development**: `http://localhost:5008/api/v1/`
- **Frontend Proxy**: `/api/v1/` (proxied through Nuxt.js)

### Authentication
- **Type**: None (open API for development)
- **Future**: Flask-AppBuilder supports JWT authentication

### Content Types
- **Request**: `multipart/form-data` (file uploads)
- **Response**: `application/json`

## Endpoints

### POST /api/v1/poseanalysisapi/analyze

Analyzes pose from uploaded image and returns scoring results.

#### Request

**Method**: `POST`  
**Content-Type**: `multipart/form-data`

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image` | File | Yes | Image file (PNG, JPG, etc.) |

**Example**:
```javascript
const formData = new FormData()
formData.append('image', selectedFile)

const response = await fetch('/api/v1/poseanalysisapi/analyze', {
  method: 'POST',
  body: formData
})
```

#### Response

**Success Response** (200 OK):
```json
{
  "left_arm": {
    "theta_raise": 100.5,
    "theta_elbow": 159.2,
    "desc": "90° < θ_raise < 170°",
    "score": 7
  },
  "right_arm": {
    "theta_raise": 103.3,
    "theta_elbow": 160.1,
    "desc": "90° < θ_raise < 170°",
    "score": 7
  },
  "best_side": "LEFT",
  "best_score": {
    "theta_raise": 100.5,
    "theta_elbow": 159.2,
    "desc": "90° < θ_raise < 170°",
    "score": 7
  },
  "processed_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
}
```

**Error Responses**:

*400 Bad Request - No image provided*:
```json
{
  "message": "No image file provided"
}
```

*400 Bad Request - No file selected*:
```json
{
  "message": "No image file selected"
}
```

*400 Bad Request - Invalid format*:
```json
{
  "message": "Invalid image format"
}
```

*400 Bad Request - No pose detected*:
```json
{
  "message": "No pose detected in image"
}
```

*500 Internal Server Error*:
```json
{
  "message": "Error processing image: [detailed error message]"
}
```

## Data Structures

### ArmAnalysis Object

Represents the analysis result for a single arm (left or right).

```typescript
interface ArmAnalysis {
  theta_raise: number;    // Arm raise angle in degrees (0-180)
  theta_elbow: number;    // Elbow bend angle in degrees (0-180)
  desc: string;          // Human-readable description
  score: number;         // Risk score (1-10, higher is better)
}
```

**Field Descriptions**:

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `theta_raise` | number | 0-180° | Angle between upper arm and torso |
| `theta_elbow` | number | 0-180° | Angle at elbow joint |
| `desc` | string | - | Ergonomic assessment description |
| `score` | number | 1-10 | Risk score (10=optimal, 1=high risk) |

### PoseAnalysisResponse Object

Complete response from the pose analysis API.

```typescript
interface PoseAnalysisResponse {
  left_arm: ArmAnalysis;     // Left arm analysis
  right_arm: ArmAnalysis;    // Right arm analysis
  best_side: "LEFT" | "RIGHT"; // Side with higher score
  best_score: ArmAnalysis;   // Best arm analysis (copy)
  processed_image: string;   // Base64 encoded PNG with annotations
}
```

### Score Interpretation

| Score Range | Risk Level | Color Code | Description |
|-------------|------------|------------|-------------|
| 8-10 | Very Low | Green | Optimal posture |
| 7 | Low | Green | Good posture |
| 5-6 | Moderate | Yellow | Acceptable with minor issues |
| 4 | Moderate-High | Yellow | Concerning posture |
| 2-3 | High | Red | Poor posture |
| 1 | Very High | Red | Very poor posture |

## Image Processing

### Input Requirements
- **Formats**: PNG, JPG, JPEG, GIF, BMP
- **Size**: No explicit limits (processed in memory)
- **Content**: Must contain at least one human figure
- **Quality**: Higher resolution improves pose detection accuracy

### Output Format
- **Type**: PNG image encoded as base64 data URL
- **Format**: `data:image/png;base64,[base64_string]`
- **Annotations**: Red pose landmarks and connections
- **Labels**: LEFT/RIGHT arm labels, score overlay

### Processing Pipeline
1. **Upload**: Multipart form data
2. **Validation**: File type and format checking
3. **Conversion**: PIL → NumPy → OpenCV format
4. **Detection**: MediaPipe pose estimation
5. **Analysis**: Angle calculation and scoring
6. **Annotation**: Drawing landmarks and labels
7. **Encoding**: PNG → base64 for JSON response

## Error Handling

### Client-Side Validation
```javascript
const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file && file.type.startsWith('image/')) {
    // Valid image file
    selectedFile.value = file
  } else {
    // Invalid file type
    error.value = 'Please select a valid image file'
  }
}
```

### Server-Side Validation
```python
# File presence check
if 'image' not in request.files:
    return self.response_400("No image file provided")

# File selection check  
file = request.files['image']
if file.filename == '':
    return self.response_400("No image file selected")

# Format validation
try:
    image = Image.open(file.stream)
    img_array = np.array(image)
except Exception:
    return self.response_400("Invalid image format")
```

## Rate Limiting and Performance

### Current Limitations
- **Concurrent Requests**: Single-threaded Flask dev server
- **Memory Usage**: ~200-500MB per request
- **Processing Time**: 1-3 seconds per image
- **No Caching**: Each request processed independently

### Production Considerations
- **WSGI Server**: Gunicorn for concurrent handling
- **Load Balancing**: Multiple worker processes
- **Caching**: Redis for repeated image analysis
- **Rate Limiting**: Flask-Limiter for API protection

## CORS Configuration

### Allowed Origins
```python
CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:3008']
```

### Headers
- **Access-Control-Allow-Origin**: Configured origins
- **Access-Control-Allow-Methods**: GET, POST, OPTIONS
- **Access-Control-Allow-Headers**: Content-Type

## Integration Examples

### Frontend Integration (Vue.js)
```javascript
const uploadAndAnalyze = async () => {
  try {
    const formData = new FormData()
    formData.append('image', selectedFile.value)

    const response = await $fetch('/api/v1/poseanalysisapi/analyze', {
      method: 'POST',
      body: formData
    })

    result.value = response
  } catch (err) {
    error.value = err.data?.message || 'Error processing image'
  }
}
```

### Python Client Example
```python
import requests

url = "http://localhost:5008/api/v1/poseanalysisapi/analyze"
files = {"image": open("test_image.jpg", "rb")}

response = requests.post(url, files=files)
data = response.json()

print(f"Best score: {data['best_score']['score']}")
print(f"Best side: {data['best_side']}")
```

---
*Generated: 2025-01-20*
*API Version: v1*