"""
@File    :   xyz_controlscript.py
@Time    :   2024/11/27 10:38:01
@Author  :   Paul Glaeser
@Version :   1.0
@Contact :   paul.glaeser@stud.h-da.de
@License :   <>
@Desc    :   Python script for manipulating multiple optomechanical stages using a gaming controller
"""

from pyjoystick.sdl2 import Key, Joystick, run_event_loop
import pyjoystick
import cv2, numpy as np
from numpy.typing import NDArray
from functools import partial
from typing import Tuple
from standa_xy_stage import Standa_XY
from thorlabs_z_stage import Z_Stage
from piezo_motor import PiezoStage


class ZStageHandler:
    """
    Handling the controls of two stages for the movement in z-direction
    (Thorlabs Labjack & Piezo Motor)
    """
    def __init__(self, labjack, piezo):
        self.big_step = False
        self.piezo_activated = False
        self.labjack = labjack
        self.piezo = piezo

    def move_up(self):
        if self.big_step:
            self._big_move(direction="+")
        else:
            self._small_move(direction="+")
    
    def move_down(self):
        if self.big_step:
            self._big_move(direction="-")
        else:
            self._small_move(direction="-")

    def _small_move(self, direction: str = "+"):
        if self.piezo_activated:
            self.piezo.small_move(direction)
        else:
            self.labjack.small_move(direction)
    
    def _big_move(self, direction: str = "+"):
        if self.piezo_activated:
            self.piezo.big_move(direction)
        else:
            self.labjack.big_move(direction)

    def get_stepsize(self):
        if self.piezo_activated:
            return None
        else:
            return self.labjack.get_stepsize_mm()

    def change_z_stage(self):
        self.piezo_activated = not self.piezo_activated

    def change_stepsize(self):
        self.big_step = not self.big_step

    def get_stage_selection(self):
        return self.piezo_activated
    
    def get_position(self):
        if self.piezo_activated:
            return None
        else:
            return self.labjack.get_position()
    
    def stop(self):
        if self.piezo_activated:
            self.piezo.stop()
        else: 
            self.labjack.stop()


def initialize_hardware():
    controller = Joystick()
    if controller.get_name() == "":
        raise ConnectionError("No controller connected!")
    print(f"Found this controller:\n\t{controller.get_name()}")
    print("\nInitializing Labjack Z-stage ...")
    thorlabs_stage = Z_Stage()    
    print("\nInitializing Standa XY-stage ...")
    standa_stage = Standa_XY()
    print("\nInitializing Piezo Z-stage ...")
    piezo_stage = PiezoStage()
    print("Hardware initialized")
    return thorlabs_stage, standa_stage, piezo_stage

def initialize_display() -> NDArray:
    layout_img = cv2.imread("./documentation/layout_controller.png", cv2.IMREAD_COLOR)
    layout_img = cv2.resize(layout_img, (0,0), fx=380/layout_img.shape[0],
                        fy=380/layout_img.shape[0])
    return np.hstack((np.zeros((380, 450, 3), dtype=np.uint8), layout_img))

def display_position(
                    display: NDArray,
                    xy_pos: Tuple, 
                    z_pos: float, 
                    stepsize_z: float,
                    stepsize_xy: float,
                    piezo_activated: bool,
                    ):
    display[:380, :450] = (0, 0, 0)
    display[152:154,:450] = (255,255,255)
    display[302:304,:450] = (255,255,255)
    cv2.putText(display, f"X: {xy_pos[0]:.3f} mm", (90,50), thickness=2, lineType=cv2.LINE_AA,
                fontFace = cv2.FONT_HERSHEY_SIMPLEX, fontScale=1.1, color=(255,255,255))
    cv2.putText(display, f"Y: {xy_pos[1]:.3f} mm", (90,90), thickness=2, lineType=cv2.LINE_AA,
                    fontFace = cv2.FONT_HERSHEY_SIMPLEX, fontScale=1.1, color=(255, 255, 255))
    
    cv2.putText(display, f"X stepsize: {stepsize_xy*1e3:.1f} um", (40,200), thickness=2, lineType=cv2.LINE_AA,
                fontFace = cv2.FONT_HERSHEY_SIMPLEX, fontScale=1.1, color=(255, 255, 255))
    cv2.putText(display, f"Y stepsize: {stepsize_xy*1e3:.1f} um", (40,240), thickness=2, lineType=cv2.LINE_AA,
                fontFace = cv2.FONT_HERSHEY_SIMPLEX, fontScale=1.1, color=(255,255,255))
    cv2.putText(display, f"z-stage: piezo Labjack", (20,350), thickness=2, lineType=cv2.LINE_AA,
            fontFace = cv2.FONT_HERSHEY_SIMPLEX, fontScale=1.1, color=(255, 255, 255))
    if piezo_activated:
        cv2.putText(display, f"Z: NA", (90,130), thickness=2, lineType=cv2.LINE_AA,
                fontFace = cv2.FONT_HERSHEY_SIMPLEX, fontScale=1.1, color=(0,0,255) if piezo_activated else (255,255,255))
        cv2.putText(display, f"Z stepsize: NA", (50,280), thickness=2, lineType=cv2.LINE_AA,
                fontFace = cv2.FONT_HERSHEY_SIMPLEX, fontScale=1.1, color=(0,0,255) if piezo_activated else (255,255,255))
        cv2.rectangle(display, (180,315), (290, 370), (0,120,255), thickness=2, lineType=cv2.LINE_AA)
    else:
        cv2.putText(display, f"Z: {z_pos:.3f} mm", (90,130), thickness=2, lineType=cv2.LINE_AA,
                fontFace = cv2.FONT_HERSHEY_SIMPLEX, fontScale=1.1, color=(0,0,255) if piezo_activated else (255,255,255))
        cv2.putText(display, f"Z stepsize: {stepsize_z*1e3:.1f} um", (40,280), thickness=2, lineType=cv2.LINE_AA,
                fontFace = cv2.FONT_HERSHEY_SIMPLEX, fontScale=1.1, color=(0,0,255) if piezo_activated else (255,255,255))
        cv2.rectangle(display, (290,315), (435, 370), (0,120,255), thickness=2, lineType=cv2.LINE_AA)
    cv2.imshow("XYZ control", display)
    cv2.waitKey(1)

def key_received(key, standa_stage, z_handler, display):
    #print(f"Keytype: {key.keytype}\nKey number: {key.number}\nKey value: {key.value}\n")
    if key.keytype == Key.HAT:
        if key.value == Key.HAT_UP:
            standa_stage.small_move(axis="y", direction="+")
        if key.value == Key.HAT_DOWN:
            standa_stage.small_move(axis="y", direction="-")
        if key.value == Key.HAT_LEFT:
           standa_stage.small_move(axis="x", direction="-")
        if key.value == Key.HAT_RIGHT:
            standa_stage.small_move(axis="x", direction="+")
    if key.keytype == Key.AXIS:
        if key.number == 0:
            if key.value < 0:
                # left joystick right
                standa_stage.big_move(axis="x", distance_mm=-1)
            if key.value > 0:
                # left joystick left
                standa_stage.big_move(axis="x", distance_mm=1)
        if key.number == 1:
            if key.value < 0:
                # left joystick up
                standa_stage.big_move(axis="y", distance_mm=1)
            if key.value > 0:
                # left joystick down
                standa_stage.big_move(axis="y", distance_mm=-1)
        if key.number == 3:
            if key.value < 0:
                # right joystick left
                pass
                # standa_stage.big_move(axis="x", distance_mm=-1)
            if key.value > 0:
                # right joystick right  
                pass
                # standa_stage.big_move(axis="x", distance_mm=1)   
        if key.number == 4:
            if key.value < 0:
                # right joystick up
                pass
                # standa_stage.big_move(axis="y", distance_mm=1)
            if key.value > 0:
                # right joystick down
                pass
                #standa_stage.big_move(axis="y", distance_mm=-1)
        if key.number == 5:
            # R2
            pass
            # z_handler.big_move("+")
        if key.number == 2:
            # L2
            pass
            # z_handler.big_move("-")
    if key.keytype == Key.BUTTON:
        if key.number == 1:
            # B-Button
            if key.value:
                z_handler.labjack.stepsize = min(10*1228800, z_handler.labjack.stepsize + 123)
                standa_stage.stepsize_mm = min(1, standa_stage.stepsize_mm + 0.0001)
        if key.number == 2:
            # X-Button
            if key.value:
                z_handler.labjack.stepsize = max(123, z_handler.labjack.stepsize - 123)
                standa_stage.stepsize_mm = max(0.0001, standa_stage.stepsize_mm - 0.0001)
        if key.number == 3:
            # Y-Button
            if key.value:
                z_handler.move_up()
        if key.number == 10:
            # HOME Button
            if key.value:
                standa_stage.to_zero()
                z_handler.labjack.to_zero()
        if key.number == 4:
            # L1
            if key.value:
                pass
                # z_handler.small_move(direction="-")
        if key.number == 5:
            # R1
            if key.value:
                pass
                # z_handler.small_move(direction="+")
        if key.number == 6:
            # SELECT-Button
            if key.value:
                z_handler.change_z_stage()
        if key.number == 7:
            # START Button
            if key.value:
                z_handler.change_stepsize()
        if key.number == 0:
            # A-Button
            if key.value:
                z_handler.move_down()
    # display position and step size data in a cv2 window
    xy_pos = standa_stage.get_position()
    z_pos = z_handler.get_position()
    stepsize_z = z_handler.labjack.get_stepsize_mm()
    stepsize_xy = standa_stage.get_stepsize_mm()
    display_position(display=display, xy_pos=xy_pos, z_pos=z_pos, 
                     stepsize_z=stepsize_z, stepsize_xy=stepsize_xy,
                     piezo_activated=z_handler.get_stage_selection())


if __name__ == "__main__":
    z_stage, xy_stage, piezo_stage = initialize_hardware()
    z_handler = ZStageHandler(labjack=z_stage, piezo=piezo_stage)
    display = initialize_display()
    arg_handler = partial(key_received, 
                          standa_stage=xy_stage, 
                          z_handler=z_handler,
                          display=display)
    repeater = pyjoystick.Repeater(first_repeat_timeout=1, 
                                   repeat_timeout=0.03,
                                   check_timeout=0.01)
    mngr = pyjoystick.ThreadEventManager(event_loop=run_event_loop,
                                        handle_key_event=arg_handler,
                                        button_repeater=repeater,
                                        alive=None)
    mngr.start()
    input()