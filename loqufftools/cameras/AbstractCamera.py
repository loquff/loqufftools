from abc import ABC, abstractmethod
from multimethod import multimethod
import numpy as np
from PIL import Image


class Camera(ABC):
    def __init__(self, resX, resY):
        self.resX = resX
        self.resY = resY

    @abstractmethod
    def capture(self):
        pass

    @abstractmethod
    def close(self):
        pass


class TestCamera(Camera):
    def __init__(self, resX, resY):
        super().__init__(resX, resY)

    @multimethod
    def capture(self, saving_path: str, roi=None):
        image = self.capture(roi=roi)
        image.save(saving_path)

    @multimethod
    def capture(self, roi=None):
        size = (self.resY, self.resX) if roi is None else (
            roi[1]-roi[0], roi[3]-roi[2])
        return np.random.randint(0, 255, size=size, dtype='uint8')

    def close(self):
        pass
