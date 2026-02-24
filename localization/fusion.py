# localization/fusion.py

class Localization:
    def __init__(self):
        self.latitude = None
        self.longitude = None
        self.indoor_x = 0
        self.indoor_y = 0

    def get_position(self):
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "indoor_x": self.indoor_x,
            "indoor_y": self.indoor_y
        }