import torch
model = torch.hub.load('ultralytics/yolov5', 'yolov5n', pretrained=True)  # 'n' for Nano