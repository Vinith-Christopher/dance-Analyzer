"""
FastAPI Dance Skeleton Application (Docker-safe)
------------------------------------------------
Processes dance videos and displays original + skeleton side-by-side.
"""
import os
import cv2
import numpy as np
import shutil
import uuid
from pathlib import Path
from typing import List, Tuple

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# ✅ Run OpenCV & MediaPipe in headless mode (no GUI)
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# ✅ Import MediaPipe safely
try:
    import mediapipe as mp
    _HAS_MEDIAPIPE = True
except ImportError:
    mp = None
    _HAS_MEDIAPIPE = False


Keypoint = Tuple[float, float, float]

# ✅ Absolute paths for Docker consistency
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
PROCESSED_DIR = BASE_DIR / "processed"
UPLOAD_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Dance Analyzer")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ✅ Serve static folders
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/processed", StaticFiles(directory=PROCESSED_DIR), name="processed")


class DanceSkeletonProcessor:
    """Processes a dance video and creates side-by-side comparison (original | skeleton)."""

    def __init__(self):
        if not _HAS_MEDIAPIPE:
            raise RuntimeError("MediaPipe not installed in container.")
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
        return results.pose_landmarks.landmark if results.pose_landmarks else []

    def draw_skeleton(self, frame_shape, keypoints):
        """Draws skeleton on black background."""
        black_frame = np.zeros(frame_shape, dtype=np.uint8)
        h, w, _ = frame_shape
        for connection in self._mp_pose.POSE_CONNECTIONS:
            start_idx, end_idx = connection
            if keypoints[start_idx].visibility > 0.5 and keypoints[end_idx].visibility > 0.5:
                start = (int(keypoints[start_idx].x * w), int(keypoints[start_idx].y * h))
                end = (int(keypoints[end_idx].x * w), int(keypoints[end_idx].y * h))
                cv2.line(black_frame, start, end, (0, 255, 0), 2)
        for lm in keypoints:
            if lm.visibility > 0.5:
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(black_frame, (cx, cy), 4, (0, 0, 255), -1)
        return black_frame

    def process_video(self, input_path: str, output_path: str) -> dict:
        """Processes the input video and saves side-by-side comparison."""
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {input_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        output_width = width * 2

        # ✅ Use mp4v instead of avc1 (more reliable in Docker)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (output_width, height))

        frame_count = 0
        processed_frames = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            keypoints = self._mediapipe_detector(frame)
            skeleton_frame = (
                self.draw_skeleton(frame.shape, keypoints)
                if keypoints
                else np.zeros_like(frame)
            )

            combined_frame = np.hstack([frame, skeleton_frame])
            cv2.putText(combined_frame, "Original", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(combined_frame, "Skeleton", (width + 10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            out.write(combined_frame)
            frame_count += 1
            processed_frames += bool(keypoints)

        cap.release()
        out.release()

        return {
            "frames": frame_count,
            "processed_frames": processed_frames,
            "fps": fps,
            "width": output_width,
            "height": height,
        }

    def __del__(self):
        if hasattr(self, "_pose"):
            self._pose.close()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.post("/process")
async def process_video(file: UploadFile = File(...)):
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")

    video_id = str(uuid.uuid4())[:8]
    temp_path = UPLOAD_DIR / f"{video_id}_temp{Path(file.filename).suffix}"
    output_path = PROCESSED_DIR / f"{video_id}_sidebyside.mp4"

    try:
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        processor = DanceSkeletonProcessor()
        info = processor.process_video(str(temp_path), str(output_path))
    except Exception as e:
        temp_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")
    finally:
        temp_path.unlink(missing_ok=True)

    return {"output_path": f"processed/{output_path.name}", "info": info}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "mediapipe_available": _HAS_MEDIAPIPE}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
