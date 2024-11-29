"""
@File    :   thorlabs_z_stage.py
@Time    :   2024/11/27 10:30:01
@Author  :   Paul Glaeser
@Version :   1.0
@Contact :   paul.glaeser@stud.h-da.de
@License :   <>
@Desc    :  Class for handling a Thorlabs MLJ250
"""

from pylablib.devices import Thorlabs
import atexit
import warnings

class Z_Stage:
    """
    Class for controlling Thorlabs Z-stage MLJ250
    When moving continously, command _move_by_ leads to unpredictable behavior
    --> instead get current position and increment / decrement it respectively
    1228800 steps = 1 mm
    """
    def __init__(self) -> None:
        """
        Constructor for initializing Labjack Z-stage
        Homing procedure at the start only if stage is not homed already
        """
        warnings.simplefilter("ignore")
        atexit.register(self.close)
        connected_devices = Thorlabs.list_kinesis_devices()
        if not len(connected_devices):
            raise ConnectionError("Error: No devices connected!")
        print("Found compatible Thorlabs device(s):")
        for e, device in enumerate(connected_devices):
            print(f"\t{device[1]} with serial number {device[0]}")
            try:
                # look for the index of the device list containing the stage name
                _ = device.index("APT Labjack")
                serialnumber = connected_devices[e][0]
            except ValueError:
                pass
        try:
            self.stage = Thorlabs.KinesisMotor(serialnumber)
        except (Thorlabs.ThorlabsError, NameError):
            print("The device was probably opened before or is not even connected!")
            raise ConnectionError
        print("Initialization complete, homing the Z-stage ...")
        self.stage.home(force=False)
        # stepsize is only applicable for small moves --> initialized with a 0.01 mm stepsize
        self.stepsize = 1228800 / 100

    def small_move(self, direction: str = "+") -> None:
        """
        Move stage for an amount of steps

        Parameters
        ---------
        str direction: select direction (+ / -) of movement

        Returns
        ---------
        None
        """
        try:
            self.stage.setup_velocity(acceleration=50e3, max_velocity=50e6, scale=False)
            current_pos = self.stage.get_position(scale=False)
            if current_pos <= 0 and direction == "-":
                print("You are at the end of the stage, you can only move upwards")
                return
            self.stage.move_to(min(current_pos + float(direction + str(self.stepsize)), 61440000))
        except Thorlabs.ThorlabsError:
            print("You are probably at the limit of the moving range, aborting ...")
            return
        
    def big_move(self, direction: str = "+") -> None:
        """
        Move stage for an amount of steps

        Parameters
        ---------
        str direction: select direction (+ / -) of movement

        Returns
        ---------
        None
        """
        try:
            self.stage.setup_velocity(acceleration=100e3, max_velocity=200e6, scale=False)
            # self.stage.move_by(float(direction + str(500e3)), scale=False)
            current_pos = self.stage.get_position(scale=False)
            if current_pos <= 0 and direction == "-":
                print("You are at the end of the stage, you can only move upwards")
                return
            self.stage.move_to(min(current_pos + float(direction + str(1e6)), 61440000))
        except Thorlabs.ThorlabsError:
            print("You are probably at the limit of the moving range, aborting ...")
            return
        
    def to_zero(self):
        self.stage.setup_velocity(acceleration=100e3, max_velocity=200e6, scale=False)
        self.stage.move_to(0, scale=False)

    def stop(self) -> None:
        self.stage.stop()

    def get_position(self) -> float:
        """
        Return the current position of the stage in millimeters
        """
        return self.stage.get_position(scale=False) / 1228800

    def get_stepsize_mm(self) -> float:
        return self.stepsize / 1228800
        
    def close(self):
        self.stage.close()