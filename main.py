"""
FastAPI Dance Skeleton Application
-----------------------------------
A web application that processes dance videos and displays original + skeleton side-by-side.
"""
# Import Necessary Modules
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import cv2
import numpy as np
from pathlib import Path
import tempfile
import shutil
from typing import List, Tuple, Optional
import uuid

# Try importing mediapipe
try:
    import mediapipe as mp
    _HAS_MEDIAPIPE = True
except ImportError:
    mp = None
    _HAS_MEDIAPIPE = False

Keypoint = Tuple[float, float, float]

# Create directories
UPLOAD_DIR = Path("uploads")
PROCESSED_DIR = Path("processed")
UPLOAD_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Dance Analyzer")
templates = Jinja2Templates(directory="templates")
# connecting folders to the url path
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/processed", StaticFiles(directory="processed"), name="processed")

class DanceSkeletonProcessor:
    """Processes a dance video and creates side-by-side comparison (original | skeleton)."""

    def __init__(self):
        self._mp_pose = mp.solutions.pose
        self._mp_drawing = mp.solutions.drawing_utils
        self._pose = self._mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def _mediapipe_detector(self, frame: np.ndarray) -> List:
        """Detect body keypoints using MediaPipe."""
        results = self._pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if results.pose_landmarks:
            return results.pose_landmarks.landmark
        return []

    def draw_skeleton(self, frame_shape, keypoints):
        """Draws skeleton on black background."""
        black_frame = np.zeros(frame_shape, dtype=np.uint8)
        h, w, _ = frame_shape

        # Draw connections (green lines)
        for connection in self._mp_pose.POSE_CONNECTIONS:
            start_idx, end_idx = connection
            if (keypoints[start_idx].visibility > 0.5 and keypoints[end_idx].visibility > 0.5):
                start = (int(keypoints[start_idx].x * w), int(keypoints[start_idx].y * h))
                end = (int(keypoints[end_idx].x * w), int(keypoints[end_idx].y * h))
                cv2.line(black_frame, start, end, (0, 255, 0), 2)  # green line

        # Draw keypoints (red dots)
        for lm in keypoints:
            if lm.visibility > 0.5:
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(black_frame, (cx, cy), 4, (0, 0, 255), -1)  # red dot

        return black_frame

    def process_video(self, input_path: str, output_path: str) -> dict:
        """Processes the input video and saves side-by-side comparison."""
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video {input_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Double the width for side-by-side view
        output_width = width * 2
        
        # Use H.264 codec for better browser compatibility
        fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264 codec
        out = cv2.VideoWriter(output_path, fourcc, fps, (output_width, height))

        frame_count = 0
        processed_frames = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            keypoints = self._mediapipe_detector(frame)
            
            if keypoints:
                skeleton_frame = self.draw_skeleton(frame.shape, keypoints)
                processed_frames += 1
            else:
                # black frame if no keypoints found
                skeleton_frame = np.zeros_like(frame)
            
            # Combine original (left) and skeleton (right) side by side
            combined_frame = np.hstack([frame, skeleton_frame])
            
            # Add labels
            cv2.putText(combined_frame, "Original", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(combined_frame, "Skeleton", (width + 10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            out.write(combined_frame)
            frame_count += 1

        cap.release()
        out.release()
        cv2.destroyAllWindows()
        
        return {
            "frames": frame_count,
            "processed_frames": processed_frames,
            "fps": fps,
            "width": output_width,
            "height": height
        }

    def __del__(self):
        if hasattr(self, '_pose'):
            self._pose.close()

# home page
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})
    

@app.post("/process")
async def process_video(file: UploadFile = File(...)):
    """Process uploaded dance video and return path to side-by-side video."""
    
    if not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Generate unique ID for this video
    video_id = str(uuid.uuid4())[:8]
    
    # Save uploaded file temporarily
    temp_filename = f"{video_id}_temp{Path(file.filename).suffix}"
    temp_path = UPLOAD_DIR / temp_filename
    
    try:
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Process video to create side-by-side output
    output_filename = f"{video_id}_sidebyside.mp4"
    output_path = PROCESSED_DIR / output_filename
    
    try:
        processor = DanceSkeletonProcessor()
        info = processor.process_video(str(temp_path), str(output_path))
    except Exception as e:
        # Clean up files on error
        temp_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        # Clean up temporary uploaded file
        temp_path.unlink(missing_ok=True)
    
    # return processed video path
    return {
        "output_path": f"processed/{output_filename}",
        "info": info
    }


@app.get("/health")
async def health_check():
    """Check if the service is running and MediaPipe is available."""
    return {
        "status": "healthy",
        "mediapipe_available": _HAS_MEDIAPIPE
    }


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Dance Skeleton Analyzer...")
    print("📍 Open http://localhost:8000 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8000)