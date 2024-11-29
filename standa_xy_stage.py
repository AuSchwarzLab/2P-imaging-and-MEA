"""
@File    :   standa_xy_stage.py
@Time    :   2024/11/27 10:30:01
@Author  :   Paul Glaeser
@Version :   1.0
@Contact :   paul.glaeser@stud.h-da.de
@License :   <>
@Desc    :  Class for handling a Standa XY stage
"""

import libximc.highlevel as ximc
from typing import Tuple
import atexit

class Standa_XY:
    """
    Class for standa translational XY-stage
    
    """
    def __init__(self) -> None:
        devices = ximc.enumerate_devices(ximc.EnumerateFlags.ENUMERATE_NETWORK | ximc.EnumerateFlags.ENUMERATE_PROBE)
        atexit.register(self.close)
        self.axis_1 = None
        self.axis_2 = None
        if len(devices) == 0:
            raise ConnectionError("No devices were found, aborting.")
        else:
            print(f"Found {len(devices)} standa device(s):")
            for device in devices:
                print(f"\tTrying to connect to {device['uri']}")
        self.axis_1 = ximc.Axis(devices[1]['uri'])
        self.axis_1.open_device()
        self.axis_2 = ximc.Axis(devices[0]['uri'])
        self.axis_2.open_device()
        engine_settings = self.axis_1.get_engine_settings()
        self.conversion_coeff = 0.0025
        self.axis_1.set_calb(self.conversion_coeff, engine_settings.MicrostepMode)
        self.axis_2.set_calb(self.conversion_coeff, engine_settings.MicrostepMode)

        print("Initialization complete, homing and zeroing both axes ...")
        settings = self.axis_1.get_move_settings_calb()
        settings.Speed = 3.0
        settings.Decel = 3.0
        settings.Accel = 3.0
        self.axis_1.set_move_settings_calb(settings)
        self.axis_2.set_move_settings_calb(settings)
        # applicable for small moves, can be changed during operation!
        self.stepsize_mm = 0.01

    def small_move(self, axis: str = "x", direction: str = "+") -> None:
        """
        Move the specified axis for the parameter stepsize_mm in a given direction

        Parameters
        ---------
        str axis: select axis for x or y movement
        str direction: direction of travel

        Returns
        ---------
        None
        
        """
        if axis == "x":
            current_pos = self.axis_1.get_position_calb()
            self.axis_1.command_move_calb(current_pos.Position + float(direction + str(self.stepsize_mm)))
        if axis == "y":
            current_pos = self.axis_2.get_position_calb()
            self.axis_2.command_move_calb(current_pos.Position + float(direction + str(self.stepsize_mm)))

    def big_move(self, axis: str= "x", distance_mm: float = 1) -> None:
        """
        Move the specified axis for a certain distance in the desired direction

        Parameters
        ---------
        str axis: select axis for x or y movement
        float distance_mm: distance in millimeters to travel

        Returns
        ---------
        None
        
        """
        if axis == "x":
            current_pos = self.axis_1.get_position_calb()
            self.axis_1.command_move_calb(current_pos.Position + distance_mm)
        if axis == "y":
            current_pos = self.axis_2.get_position_calb()
            self.axis_2.command_move_calb(current_pos.Position + distance_mm)

    def close(self) -> None:
        self.axis_1.close_device()
        self.axis_2.close_device()

    def get_position(self) -> Tuple[float, float]:
        x = self.axis_1.get_position_calb().Position
        y = self.axis_2.get_position_calb().Position
        return (x, y)
    
    def get_stepsize_mm(self) -> float:
        return self.stepsize_mm
    
    def stop(self) -> None:
        self.axis_1.command_stop()
        self.axis_2.command_stop()

    def to_zero(self) -> None:
        self.axis_1.command_move_calb(0)
        self.axis_2.command_move_calb(0)
