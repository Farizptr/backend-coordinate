# 🏢 Building Detection Backend Service

A production-ready **FastAPI backend service** for building detection using YOLOv8. This service accepts polygon areas from frontend applications and returns detected buildings in GeoJSON format.

## 🚀 Quick Start

### 1. Installation
```bash
git clone https://github.com/Farizptr/backend-coordinate.git
cd backend-coordinate
pip install -r requirements.txt
```

### 2. Start the API Server
```bash
python run_server.py
```

### 3. Access the API
- **API Server**: http://localhost:8000
- **Interactive Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📡 API Endpoints

### 🏥 Health Check
```http
GET /health
```
Check if the API server and model are ready.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": "2024-01-01T12:00:00"
}
```

### 🔍 Building Detection
```http
POST /detect
```
Submit a polygon area for building detection.

**Request Body:**
```json
{
  "polygon": {
    "type": "Feature",
    "geometry": {
      "type": "Polygon",
      "coordinates": [[[lng, lat], [lng, lat], ...]]
    },
    "properties": {}
  },
  "zoom": 18,
  "confidence": 0.25,
  "enable_merging": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Building detection completed successfully",
  "buildings": [
    {
      "id": "building_1",
      "coordinates": [[lng, lat], [lng, lat], ...],
      "confidence": 0.85
    }
  ],
  "total_buildings": 42,
  "execution_time": 15.3
}
```

### 🤖 Model Information
```http
GET /models/info
```
Get information about the loaded YOLOv8 model.

## 🧪 Testing the API

Run the test script to verify everything works:
```bash
python test_api.py
```

## 🏗️ Frontend Integration

### JavaScript/React Example
```javascript
async function detectBuildings(polygon) {
  const response = await fetch('http://localhost:8000/detect', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      polygon: polygon,
      zoom: 18,
      confidence: 0.25,
      enable_merging: true
    })
  });
  
  const result = await response.json();
  return result.buildings;
}
```

### Python Example
```python
import requests

def detect_buildings(polygon_geojson):
    payload = {
        "polygon": polygon_geojson,
        "zoom": 18,
        "confidence": 0.25
    }
    
    response = requests.post(
        "http://localhost:8000/detect",
        json=payload
    )
    
    return response.json()
```

## ⚙️ Configuration

### Parameters
- **zoom**: Satellite image zoom level (default: 18)
- **confidence**: Detection confidence threshold (default: 0.25)
- **batch_size**: Tile processing batch size (default: 5)
- **enable_merging**: Merge overlapping detections (default: true)
- **merge_iou_threshold**: IoU threshold for merging (default: 0.1)

### Environment Variables
Create a `.env` file for custom configuration:
```bash
API_HOST=0.0.0.0
API_PORT=8000
MODEL_PATH=best.pt
LOG_LEVEL=info
```

## 📁 Project Structure

```
backend-coordinate/
├── api.py                 # FastAPI application
├── run_server.py          # Server startup script
├── test_api.py            # API testing script
├── main.py                # CLI interface (legacy)
├── config.py              # Configuration management
├── best.pt                # YOLOv8 model (excluded from git)
├── src/
│   ├── core/              # Core detection algorithms
│   ├── utils/             # Utility functions
│   ├── validation/        # Data validation
│   └── visualization/     # Plotting and maps
├── docs/                  # Technical documentation
├── examples/              # Sample files and usage
└── requirements.txt       # Python dependencies
```

## 🔧 Features

### ✨ Production Ready
- **FastAPI** framework with automatic API documentation
- **Async processing** with background task cleanup
- **CORS support** for frontend integration
- **Error handling** with proper HTTP status codes
- **Health checks** for monitoring

### 🏢 Building Detection
- **YOLOv8** state-of-the-art object detection
- **Advanced merging** algorithms for fragmented buildings
- **Batch processing** for efficient tile handling
- **Resume capability** for large area processing
- **GeoJSON output** compatible with mapping libraries

### 🗺️ Geospatial Processing
- **Satellite tile** fetching and processing
- **Coordinate transformation** between systems
- **Polygon validation** and preprocessing
- **Boundary-aware merging** for cross-tile buildings

## 🚀 Deployment

### Docker (Recommended)
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "run_server.py"]
```

### Production Server
```bash
# Using Gunicorn
pip install gunicorn
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

# Using PM2
npm install -g pm2
pm2 start run_server.py --name building-detection-api
```

## 📊 Performance

- **Processing Speed**: ~2-5 seconds per 1km² area
- **Memory Usage**: ~2-4GB RAM (depends on model and area size)
- **Scalability**: Stateless design supports horizontal scaling
- **Concurrency**: Async processing with background cleanup

## 🛠️ Development

### CLI Interface (Legacy)
The original CLI interface is still available:
```bash
python main.py examples/sample_polygon.geojson --output results/
```

### Adding New Features
1. Add endpoint to `api.py`
2. Implement logic in `src/` modules
3. Add tests to `test_api.py`
4. Update documentation

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For questions or issues:
- Create an issue on GitHub
- Check the API documentation at `/docs`
- Review the examples in `examples/`
