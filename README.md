# 🕺 Dance Skeleton Analyzer

A FastAPI-based web application that processes dance videos using AI to extract skeletal movements and displays them side-by-side with the original video. Perfect for dance analysis, movement studies, and choreography review.

![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![MediaPipe](https://img.shields.io/badge/MediaPipe-pose-orange.svg)

## ✨ Features

- 🎥 **Real-time Video Processing**: Upload dance videos and get skeleton analysis
- 🤖 **AI-Powered Pose Detection**: Uses Google MediaPipe for accurate body tracking
- 📊 **Side-by-Side Comparison**: View original and skeleton overlay simultaneously
- 🐳 **Docker Ready**: Fully containerized for easy deployment
- ☁️ **Cloud Deployable**: Optimized for AWS EC2 and other cloud platforms
- 🎨 **Responsive UI**: Clean, modern interface built with Jinja2 templates
- 📦 **Automatic Scaling**: Handles videos up to Full HD (1920x1080) resolution

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Python 3.12+ (for local development)
- 4GB+ RAM recommended
- Git installed

### Local Development

```bash
# Clone the repository
git clone https://github.com/yourusername/dance-skeleton-analyzer.git
cd dance-skeleton-analyzer

# Build and run with Docker Compose
docker-compose build
docker-compose up

# Access the application
# Open browser: http://localhost:8000
```

### Without Docker (Development)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py

# Access at http://localhost:8000
```

## 📦 Project Structure

```
dance-skeleton-analyzer/
├── main.py                 # FastAPI application & video processing logic
├── Dockerfile             # Docker container configuration
├── docker-compose.yml     # Docker Compose orchestration
├── requirements.txt       # Python dependencies
├── templates/             # Jinja2 HTML templates
│   └── home.html         # Main upload interface
├── uploads/              # Temporary uploaded videos (auto-created)
├── processed/            # Output processed videos (auto-created)
└── README.md             # This file
```

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **OpenCV (cv2)**: Video processing and computer vision
- **MediaPipe**: Google's ML solution for pose detection
- **Uvicorn**: ASGI server for running FastAPI

### Frontend
- **Jinja2**: Template engine for HTML rendering
- **HTML5 Video**: Native video playback
- **Tailwind CSS** (optional): For styling

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **FFmpeg**: Video codec support (included in container)

## 📋 Requirements

### System Requirements
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended for large videos
- **Storage**: 10GB+ free space
- **OS**: Linux (Ubuntu/Debian), macOS, or Windows with WSL2

### Python Dependencies
```txt
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
python-multipart>=0.0.6
opencv-python>=4.8.0
opencv-contrib-python>=4.8.0
mediapipe>=0.10.0
numpy>=1.24.0
jinja2>=3.1.0
```

## 🎬 How It Works

1. **Upload**: User uploads a dance video through the web interface
2. **Processing**: 
   - Video is resized to optimal resolution (max 1920px width)
   - MediaPipe analyzes each frame for body pose landmarks
   - Skeleton overlay is drawn on a black background
   - Original and skeleton frames are combined side-by-side
3. **Output**: Processed MP4 video is generated and displayed
4. **Cleanup**: Temporary files are automatically removed

### Video Processing Pipeline

```
Input Video (MP4/MOV/AVI)
    ↓
Resize (if > 1920px width)
    ↓
Frame-by-frame Analysis
    ↓
Pose Detection (MediaPipe)
    ↓
Skeleton Drawing
    ↓
Side-by-Side Composition
    ↓
MP4 Output (mp4v codec)
    ↓
Browser Playback
```

## 🔧 Configuration

### Video Processing Settings

Edit `main.py` to customize:

```python
# Maximum video width (main.py, line ~110)
MAX_WIDTH = 1920  # Full HD

# MediaPipe pose detection settings (main.py, line ~65)
self._pose = self._mp_pose.Pose(
    model_complexity=1,        # 0, 1, or 2 (higher = more accurate, slower)
    min_detection_confidence=0.5,  # 0.0 to 1.0
    min_tracking_confidence=0.5     # 0.0 to 1.0
)

# Skeleton drawing colors (main.py, line ~85)
cv2.line(black_frame, start, end, (0, 255, 0), 2)  # Green lines
cv2.circle(black_frame, (cx, cy), 4, (0, 0, 255), -1)  # Red points
```

### Docker Resource Limits

Edit `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '4'      # Max CPU cores
      memory: 8G     # Max RAM
    reservations:
      cpus: '2'      # Guaranteed CPU
      memory: 4G     # Guaranteed RAM
```

## 🌐 AWS EC2 Deployment

### Step 1: Launch EC2 Instance

```bash
# Recommended: t3.large or t3.xlarge
# OS: Ubuntu 22.04 LTS
# Storage: 20GB+ EBS volume
# Security Group: Allow port 8000 (or 80/443)
```

### Step 2: Connect and Setup

```bash
# SSH into instance
ssh -i your-key.pem ec2-user@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install docker.io docker-compose -y
sudo usermod -aG docker $USER
sudo systemctl enable docker
sudo systemctl start docker

# Logout and login again for group changes
exit
ssh -i your-key.pem ec2-user@your-ec2-ip
```

### Step 3: Deploy Application

```bash
# Clone repository
git clone https://github.com/yourusername/dance-skeleton-analyzer.git
cd dance-skeleton-analyzer

# Create required directories
mkdir -p uploads processed

# Set permissions
chmod 777 uploads processed

# Build and run
docker-compose build --no-cache
docker-compose up -d

# Check status
docker-compose logs -f
docker ps
```

### Step 4: Configure Security Group

```bash
# In AWS Console:
# EC2 → Security Groups → Your SG
# Add Inbound Rule:
# Type: Custom TCP
# Port: 8000
# Source: 0.0.0.0/0 (or your IP)
```

### Step 5: Access Application

```
http://your-ec2-public-ip:8000
```

### Optional: Setup Nginx Reverse Proxy

```bash
# Install Nginx
sudo apt install nginx -y

# Create config
sudo nano /etc/nginx/sites-available/dance-analyzer

# Add:
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/dance-analyzer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔄 Updating the Application

### Method 1: Git Pull (Recommended)

```bash
# On EC2 instance
cd /path/to/dance-skeleton-analyzer

# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Verify
docker-compose logs -f
```

### Method 2: Manual Update

```bash
# Stop containers
docker-compose down

# Update code files manually
nano main.py  # Make your changes

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

## 🐛 Troubleshooting

### Issue: Video shows black screen

**Solution 1**: Check codec support
```bash
docker exec -it dance-skeleton-analyzer python -c "import cv2; print(cv2.getBuildInformation())"
```

**Solution 2**: Check file permissions
```bash
docker exec -it dance-skeleton-analyzer ls -la /app/processed/
sudo chmod 777 processed/
```

**Solution 3**: Check logs
```bash
docker-compose logs -f
```

### Issue: "No space left on device"

```bash
# Clean Docker
docker system prune -a --volumes -f

# Check disk space
df -h

# Increase EBS volume in AWS Console
# Then extend filesystem:
sudo growpart /dev/xvda 1
sudo resize2fs /dev/xvda1
```

### Issue: Container keeps restarting

```bash
# Check logs
docker-compose logs

# Check resource usage
docker stats

# Reduce video size or increase RAM in docker-compose.yml
```

### Issue: Processing timeout

**Solution**: Reduce video resolution or length
```python
# In main.py, reduce MAX_WIDTH
MAX_WIDTH = 1280  # HD instead of Full HD
```

### Issue: Port already in use

```bash
# Find process using port 8000
sudo lsof -i :8000
sudo kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "8080:8000"  # Use 8080 instead
```

## 📊 API Endpoints

### `GET /`
Main upload interface (HTML page)

### `POST /process`
Process uploaded video
- **Input**: multipart/form-data with video file
- **Output**: JSON with processed video path
```json
{
  "output_path": "/processed/abc123_sidebyside.mp4",
  "info": {
    "frames": 180,
    "processed_frames": 175,
    "fps": 25,
    "width": 3840,
    "height": 1080,
    "file_size": 15728640
  }
}
```

### `GET /health`
Health check endpoint
```json
{
  "status": "healthy",
  "mediapipe_available": true,
  "opencv_version": "4.8.1",
  "ffmpeg_available": true
}
```

### `GET /debug/files`
List uploaded and processed files (debug only)
```json
{
  "processed_files": ["abc123_sidebyside.mp4"],
  "upload_files": [],
  "processed_dir": "/app/processed",
  "upload_dir": "/app/uploads"
}
```

## 🔒 Security Considerations

### For Production Deployment:

1. **Add file size limits**:
```python
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
```

2. **Add file type validation**:
```python
ALLOWED_EXTENSIONS = {'.mp4', '.mov', '.avi', '.webm'}
```

3. **Use environment variables**:
```python
import os
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
```

4. **Setup HTTPS**:
```bash
# Use Let's Encrypt with Certbot
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

5. **Add rate limiting**:
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

6. **Implement authentication** (if needed):
```python
from fastapi.security import HTTPBasic, HTTPBasicCredentials
security = HTTPBasic()
```

## 📈 Performance Optimization

### For Better Performance:

1. **Use GPU acceleration** (if available):
```dockerfile
# In Dockerfile, use CUDA base image
FROM nvidia/cuda:11.8-runtime-ubuntu22.04
```

2. **Reduce video resolution**:
```python
MAX_WIDTH = 1280  # HD instead of Full HD
```

3. **Process fewer frames**:
```python
# Skip frames for faster processing
if frame_count % 2 == 0:  # Process every other frame
    continue
```

4. **Use multiprocessing**:
```python
from multiprocessing import Pool
# Process frames in parallel
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Google MediaPipe**: For the excellent pose detection ML model
- **OpenCV**: For powerful video processing capabilities
- **FastAPI**: For the modern, fast web framework
- **Docker**: For making deployment seamless

## 📧 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Email: your-email@example.com
- Documentation: [Wiki](https://github.com/yourusername/dance-skeleton-analyzer/wiki)

## 🗺️ Roadmap

- [ ] Add support for multiple people detection
- [ ] Implement real-time webcam processing
- [ ] Add 3D pose visualization
- [ ] Support batch video processing
- [ ] Add custom skeleton color themes
- [ ] Export skeleton data as JSON/CSV
- [ ] Comparison mode for two dancers
- [ ] Mobile app version

## 📸 Screenshots

### Upload Interface
![Upload Interface](Screenshots\Interface.png)

### Processing in Progress
![Processing](Screenshots\Processing.png)

### Side-by-Side Result
![Result](Screenshots\Sidebyside_out.png)

---

**Built with ❤️ for dancers and movement enthusiasts**

**Version**: 1.0.0  
**Last Updated**: November 2025