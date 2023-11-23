try:
    # Import PyhtonNet
    import sys
    import os
    import clr
    # Load IC Imaging Control .NET
    ic35path = os.getenv('IC35PATH')
    if ic35path is None:
        raise OSError(
            """The 'IC35PATH' enviroment variable seems not to be set. \n
            On Windows, it should point to the full path of the folder Documents/IC Imaging Control 3.5. \n
            You can set this variable manually, but remember to restart your computer.""")
    else:
        sys.path.append(ic35path + "/redist/dotnet/x64")
    clr.AddReference('TIS.Imaging.ICImagingControl35')
    clr.AddReference('System')

    # Import the IC Imaging Control namespace.
    import TIS.Imaging
    from System import TimeSpan
except:
    raise Exception(("""
        There appears to be some sort of problem with the installation of the ImagingSource software. \n
        Check https://github.com/TheImagingSource/IC-Imaging-Control-Samples/tree/master/Python/Python%20NET for more information.
        """))

import loqufftools.cameras.AbstractCamera as AbstractCamera
from multimethod import multimethod
import ctypes as C
from tqdm import tqdm
from loqufftools.hdf5_utils import *
from slmcontrol import *
import configparser
import h5py
import numpy as np


class ImagingSourceCamera(AbstractCamera.Camera):
    def __init__(self, resX, resY):
        super().__init__(resX, resY)
        self.imaging_control = TIS.Imaging.ICImagingControl()

        # Create the sink for snapping images on demand.
        snapsink = TIS.Imaging.FrameSnapSink(TIS.Imaging.MediaSubtypes.Y800)
        self.imaging_control.Sink = snapsink

        self.imaging_control.LiveDisplay = False

        # Try to open the last used video capture device.
        try:
            self.imaging_control.LoadDeviceStateFromFile("device.xml", True)
            if self.imaging_control.DeviceValid is True:
                self.imaging_control.LiveStart()

        except Exception as ex:
            self.imaging_control.ShowDeviceSettingsDialog()
            if self.imaging_control.DeviceValid is True:
                self.imaging_control.SaveDeviceStateToFile("device.xml")
                self.imaging_control.LiveStart()
            pass

    @multimethod
    def capture(self, roi=None):
        image = self.imaging_control.Sink.SnapSingle(TimeSpan.FromSeconds(5))
        imgcontent = C.cast(image.GetIntPtr().ToInt64(), C.POINTER(
            C.c_ubyte * image.FrameType.BufferSize))
        result = np.ndarray(buffer=imgcontent.contents,
                            dtype=np.uint8,
                            shape=(image.FrameType.Height,
                                   image.FrameType.Width))

        if roi == None:
            return result
        else:
            return result[slice(roi[0], roi[1]), slice(roi[2], roi[3])]

    @multimethod
    def capture(self, saving_path: str, roi=None):
        image = self.imaging_control.Sink.SnapSingle(TimeSpan.FromSeconds(5))
        TIS.Imaging.FrameExtensions.SaveAsBitmap(image, saving_path)

    def loop_capture_as_hdf5(self, saving_path, slm, config_path, source_key, saving_key, roi=None, calculate_mean=False):
        try:
            with h5py.File(saving_path, 'a') as file:
                check_safety(file, saving_key)

                config = configparser.ConfigParser()
                config.read(config_path)
                x, y = build_grid(config_path)

                max = config['slm'].getint('max')
                xoffset = config['input'].getint('xoffset')
                yoffset = config['input'].getint('yoffset')
                waist = config['input'].getfloat('waist')
                xperiod = config['grating'].getfloat('xperiod')
                yperiod = config['grating'].getfloat('yperiod')

                input = hg(x, y, 0, 0, waist)

                fields = file[source_key]
                if roi == None:
                    result = np.zeros(
                        (fields.shape[0], self.resY, self.resX), dtype='uint8')
                else:
                    result = np.zeros(
                        (fields.shape[0], roi[1]-roi[0], roi[3]-roi[2]), dtype='uint8')

                for n, desired in tqdm(enumerate(fields)):
                    holo = generate_hologram(
                        desired, input, x, y, max, xperiod, yperiod, xoffset, yoffset)
                    slm.updateArray(holo)

                    result[n, :, :] = self.capture(roi=roi)

                file.create_dataset(saving_key, data=result)

            if calculate_mean:
                directory_path, old_filename = os.path.split(saving_path)
                new_path = os.path.join(directory_path, 'mean_' + old_filename)
                with h5py.File(new_path, 'a') as file:
                    check_safety(file, saving_key)
                    file[saving_key] = np.mean(result, axis=0)

        except Exception as e:
            print(e)
        finally:
            self.close()
            file.close()

    def close(self):
        self.imaging_control.LiveStop()
        self.imaging_control.Dispose()
