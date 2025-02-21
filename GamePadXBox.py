import pygame
from pygame.locals import *
import threading
import time

class ControllerState:
    def __init__(self, num_axes, num_buttons, num_hats):
        self.axes = [0.0] * num_axes
        if num_axes > 3:
            self.axes[4] = -1.0
        if num_axes > 4:
            self.axes[5] = -1.0
        self.buttons = [False] * num_buttons
        self.hats = [(0, 0)] * num_hats if num_hats > 0 else []

    def update_axis(self, axis, value):
        self.axes[axis] = round(value, 2)

    def update_button(self, button, pressed):
        self.buttons[button] = pressed

    def update_hat(self, hat, value):
        if self.hats:
            self.hats[hat] = value
            
controls = None

def get_controls():
    return controls

def initialize_controller():
    """Initialize Pygame joystick subsystem and select the first Xbox controller"""
    pygame.init()
    pygame.joystick.init()
    
    num_joysticks = pygame.joystick.get_count()
    if num_joysticks < 1:
        raise RuntimeError("No controller detected")
    
    for i in range(num_joysticks):
        controller = pygame.joystick.Joystick(i)
        controller.init()
        if "xbox" in controller.get_name().lower():
            return controller
    
    raise RuntimeError("No Xbox controller detected")

def display_controller_info(device):
    """Display connected controller specifications"""
    print(f"Connected device: {device.get_name()}")
    print(f"Axes: {device.get_numaxes()}")
    print(f"Buttons: {device.get_numbuttons()}")
    print(f"Hats: {device.get_numhats()}")

def check_xbox_controller_inputs(device):
    if device.get_numaxes() == 6 and device.get_numbuttons() >= 11 and device.get_numhats() == 1:
        return True

    raise RuntimeError("Uncompliant Xbox controller")

def controller_thread():
    """Thread function to handle controller events"""
    global controls
    try:
        gamepad = initialize_controller()
        check_xbox_controller_inputs(gamepad)

        display_controller_info(gamepad)
        
        # Initialize controller state
        controls = ControllerState(gamepad.get_numaxes(), gamepad.get_numbuttons(), gamepad.get_numhats())
        
        while True:
            controls_event = False
            for event in pygame.event.get():
                if event.type == QUIT:
                    return
                
                # Input type handling
                if event.type == JOYAXISMOTION:
                    controls.update_axis(event.axis, event.value)
                    controls_event = True
                
                if event.type == JOYBUTTONDOWN:
                    controls.update_button(event.button, True)
                    controls_event = True
                
                if event.type == JOYBUTTONUP:
                    controls.update_button(event.button, False)
                    controls_event = True
                
                if event.type == JOYHATMOTION:
                    controls.update_hat(event.hat, event.value)
                    controls_event = True
            
            if controls_event and  __name__ == "__main__":
                # Display controller state
                axes_str = ', '.join([f"{value:.2f}" for value in controls.axes])
                buttons_str = ', '.join([str(int(pressed)) for pressed in controls.buttons])
                hats_str = ', '.join([f"({hat[0]}, {hat[1]})" for hat in controls.hats])
                print(f"Axes: [{axes_str}], Buttons: [{buttons_str}], Hats: [{hats_str}]", end='\r')

            time.sleep(0.01)  # Add a small delay to avoid high CPU usage

    except Exception as error:
        print(f"Error: {str(error)}")
    finally:
        pygame.quit()

if __name__ == "__main__":
    thread = threading.Thread(target=controller_thread)
    thread.start()
    thread.join()
