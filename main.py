import cv2
from vision.detector import Detector
from utils.logger import log_detection
from hardware.camera import Camera
from movement.controller import MovementController


def main():
    # Initialize modules
    detector = Detector()
    camera = Camera(source=0, width=640, height=480)
    movement = MovementController()

    print("Rescue Robot Vision System Started")
    print("Press 'q' to exit\n")

    while True:
        ret, frame = camera.read()

        if not ret:
            print("Failed to grab frame")
            break

        # Run detection
        results = detector.detect(frame)
        persons = detector.get_person_detections(results)

        # ===== DECISION + MOVEMENT LOGIC =====
        if len(persons) > 0:
            movement.stop()
        else:
            movement.move_forward(40)
        # =====================================

        # Draw bounding boxes
        for (x1, y1, x2, y2) in persons:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame,
                "HUMAN DETECTED",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

        # Log detections
        if len(persons) > 0:
            print("⚠ Human Detected!")
            log_detection(persons)

        # Show video
        cv2.imshow("Rescue Robot Vision", frame)

        # Exit condition
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Cleanup
    movement.stop()
    movement.cleanup()
    camera.release()
    cv2.destroyAllWindows()
    print("System Shut Down")


if __name__ == "__main__":
    main()