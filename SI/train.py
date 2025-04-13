from ultralytics import YOLO
def main():
    model = YOLO("yolo11n.pt")
    model.train(
        data="C:/Hackcarpathia2025/Hackathon_project/SI/ultralytics/data.yaml",
        epochs=50,
        imgsz=500,
        batch=8,
        workers=8,
        device=0  # Force CPU training
    )

if __name__ == '__main__':
    main()