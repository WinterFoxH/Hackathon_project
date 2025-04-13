from ultralytics import YOLO

# Load your custom model (or default YOLOv8)
model = YOLO("C:/Hackcarpathia2025/Hackathon_project/runs/detect/train16/weights/best.pt")  # Replace with your trained model if available

# Real-time webcam detection
results = model.predict(source="0", show=True, conf=0.7)  # '0' = default webcam