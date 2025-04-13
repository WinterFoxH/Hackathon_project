import cv2
import torch
from models.experimental import attempt_load

# Load custom YOLOv5 model
model = attempt_load("C:/Hackcarpathia2025/Hackathon_project/AI/yolov5/runs/train/exp5/weights/best.pt")
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = model.to(device)
model.eval()

# Open webcam
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Convert frame to RGB (YOLOv5 expects RGB)
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Run inference
    results = model(img)  # Detect objects

    # Get detections
    detections = results.pandas().xyxy[0]

    # Blur each detected region
    for _, det in detections.iterrows():
        if det['confidence'] > 0.7:
            x1, y1, x2, y2 = map(int, [det['xmin'], det['ymin'], det['xmax'], det['ymax']])
            frame[y1:y2, x1:x2] = cv2.GaussianBlur(frame[y1:y2, x1:x2], (51, 51), 0)

    cv2.imshow('YOLOv5 Blur Detection', frame)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()