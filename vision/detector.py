from ultralytics import YOLO

class Detector:
    def __init__(self, model_path="yolov8n.pt"):
        self.model = YOLO(model_path)

    def detect(self, frame):
        results = self.model(frame, verbose=False)
        return results

    def get_person_detections(self, results):
        persons = []

        for box in results[0].boxes:
            class_id = int(box.cls[0])
            if class_id == 0:  # Class 0 = person in COCO dataset
                x1, y1, x2, y2 = box.xyxy[0]
                persons.append((int(x1), int(y1), int(x2), int(y2)))

        return persons