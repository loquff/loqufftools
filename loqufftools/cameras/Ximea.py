try:
    from ximea import xiapi
except:
    raise ImportError("""There seems to be a problem with your instalation. \n
                      Check https://www.ximea.com/support/wiki/apis/Python_inst_win for details.""")

import loqufftools.cameras.AbstractCamera as AbstractCamera
from multimethod import multimethod
import numpy as np
from PIL import Image


class XimeaCamera(AbstractCamera.Camera):
    def __init__(self, resX, resY):
        self.resX = resX
        self.resY = resY
        self.camera = xiapi.Camera()
        self.camera.open_device()
        self.camera.set_exposure(1000)
        self.image = xiapi.Image()
        self.camera.start_acquisition()

    @multimethod
    def capture(self, roi=None):
        self.camera.get_image(self.image)
        if roi is None:
            return self.image.get_image_data_numpy()
        else:
            return self.image.get_image_data_numpy()[roi[0]:roi[1], roi[2]:roi[3]]

    @multimethod
    def capture(self, saving_path: str, roi=None):
        Image.fromarray(self.capture(roi=roi)).save(saving_path)

    def set_exposure(self, exposure):
        self.camera.set_exposure(exposure)

    def close(self):
        self.camera.stop_acquisition()
        self.camera.close_device()
