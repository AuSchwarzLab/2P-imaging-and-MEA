"""
@File    :   piezo_motor.py
@Time    :   2024/11/27 10:29:37
@Author  :   Paul Glaeser
@Version :   1.0
@Contact :   paul.glaeser@stud.h-da.de
@License :   <>
@Desc    :  Class for handling a Thorlabs PA13 piezo actuator
"""

from pylablib.devices import Thorlabs
import atexit
import warnings

class PiezoStage:
    """
    Class for controlling the Thorlabs PA13 piezo actuator
    
    """
    def __init__(self) -> None:
        warnings.filterwarnings("ignore")
        atexit.register(self.close)
        connected_devices = Thorlabs.list_kinesis_devices()
        if not len(connected_devices):
            raise ConnectionError("Error: No devices connected!")
        print("Found compatible Thorlabs device(s):")
        for e, device in enumerate(connected_devices):
            print(f"\t{device[1]} with serial number {device[0]}")
            try:
                # look for the index of the device list containing the stage name
                _ = device.index("Piezo Motor Controller")
                serialnumber = connected_devices[e][0]
            except ValueError:
                pass
        try:
            self.stage = Thorlabs.KinesisPiezoMotor(serialnumber)
            if self.stage.get_enabled_channels == None:
                self.stage.enable_channels(1)
                self.stage.setup_drive(max_voltage=120, velocity=500, acceleration=1000)
        except (Thorlabs.ThorlabsError, NameError):
            print("The device was probably opened before or is not even connected!")
            raise ConnectionError
        print("Initialization complete")
                    

    def _move(self, direction: str = "+", steps: float = 1) -> None:
        self.stage.setup_drive(max_voltage=115, velocity=500, acceleration=1000)
        self.stage.move_by(int(direction + str(steps)))

    def small_move(self, direction: str = "+"):
        """
        Move stage for a single step, typically equalling 20 nanometers of travel
        """
        self.stage.setup_drive(max_voltage=80, velocity=400, acceleration=600)
        current_pos = self.stage.get_position()
        self.stage.move_to(current_pos + int(direction + str(1)))
        #self.stage.move_by(int(direction + str(10)))
    
    def big_move(self, direction: str = "+"):
        """
        Move stage for multiple steps (N = 50)
        """
        #self.stage.setup_drive(max_voltage=120, velocity=500, acceleration=1000)
        current_pos = self.stage.get_position()
        self.stage.move_to(current_pos + int(direction + str(50)))
        #self.stage.move_by(int(direction + str(500)))

    def get_position(self) -> float:
        """
        Get the current position of the piezo motor in number of steps
        """
        return self.stage.get_position()
    
    def stop(self) -> None:
        self.stage.stop()

    def close(self):
        self.stage.close()
