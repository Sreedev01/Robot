# decision/logic.py

class DecisionEngine:
    def __init__(self, movement_controller):
        self.movement = movement_controller

    def process(self, detections, location):
        if detections is not None and len(detections) > 0:
            print("Person detected!")
            self.movement.stop()