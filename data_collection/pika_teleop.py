import numpy as np
import threading
import time
from pikasense import Pika

class PikaTeleop:
    """
    Provides teleoperation interface using the Pika Sense device.
    It runs in a separate thread to continuously poll the device.
    """
    def __init__(self):
        try:
            self.pika = Pika()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Pika Sense device. Is it connected? Error: {e}")
            
        self.action = np.zeros(7, dtype=np.float32)  # [dx, dy, dz, droll, dpitch, dyaw, gripper]
        self.is_running = True
        self.lock = threading.Lock()
        
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()

    def _poll_loop(self):
        """Continuously polls the Pika Sense device for its state."""
        while self.is_running:
            raw_pose = self.pika.get_pose()
            raw_gripper = self.pika.get_gripper()
            
            with self.lock:
                # Assuming get_pose() returns [x, y, z, roll, pitch, yaw]
                # And values are reasonably scaled. May need adjustment.
                self.action[:6] = raw_pose
                self.action[6] = raw_gripper # Assuming this is a value between 0 (open) and 1 (closed)
            time.sleep(0.01)

    def get_action(self) -> tuple[np.ndarray, bool, bool, bool, bool]:
        """
        Returns the latest robot action and button states.
        This version is simplified as Pika doesn't have the same buttons as a keyboard.
        We'll map one of its buttons to recording.
        """
        with self.lock:
            current_action = self.action.copy()
        
        # Map a Pika button to the recording toggle.
        # This is a placeholder - you'll need to find out which button index to use.
        # For now, let's assume a button press for > 0.5 triggers recording.
        toggle_recording = self.pika.get_button_state(0) > 0.5 
        
        # These are not supported by Pika Sense directly, returning False
        go_home = False
        toggle_gripper = False # Gripper is now part of the continuous action space
        quit_program = False 

        return current_action, toggle_recording, go_home, toggle_gripper, quit_program

    def close(self):
        """Stops the polling thread."""
        self.is_running = False
        self.thread.join()
        print("Pika Sense polling stopped.")
