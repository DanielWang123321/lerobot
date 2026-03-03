import pygame
import numpy as np

class KeyboardTeleop:
    """
    Provides a simple keyboard-based teleoperation interface using Pygame.
    Maps key presses to 6D end-effector velocity commands for the robot.
    """
    def __init__(self, screen_size=(200, 200)):
        """
        Initializes the Pygame window for capturing keyboard events.
        Args:
            screen_size: A tuple (width, height) for the display window.
        """
        pygame.init()
        pygame.display.set_caption("Keyboard Teleop")
        self.screen = pygame.display.set_mode(screen_size)
        self.font = pygame.font.SysFont("monospace", 12)
        
        # Action state, representing [vx, vy, vz, vroll, vpitch, vyaw]
        self.action = np.zeros(6, dtype=np.float32)
        
        # Control sensitivity (tweak these values to your preference)
        self.linear_speed_factor = 0.3  # m/s
        self.angular_speed_factor = 0.8 # rad/s
        
        self.is_running = True
        self.is_recording = False
        self.gripper_action = 0 # 0=no-op, 1=close, -1=open
        
        self.controls_text = [
            "--- Keyboard Teleop ---",
            "Linear (Position):",
            " W/S: Forward/Back (+/-X)",
            " A/D: Left/Right   (+/-Y)",
            " Q/E: Up/Down       (+/-Z)",
            "",
            "Angular (Rotation):",
            " I/K: Pitch Up/Down",
            " J/L: Yaw Left/Right",
            " U/O: Roll Left/Right",
            "",
            "Controls:",
            " R: Start/Stop Recording",
            " G: Toggle Gripper",
            " H: Go to Home Pose",
            " ESC: Quit",
            "-----------------------",
        ]
        
    def _update_display(self):
        """Renders the control instructions and current status on the Pygame screen."""
        self.screen.fill((255, 255, 255)) # White background
        
        for i, line in enumerate(self.controls_text):
            text_surface = self.font.render(line, True, (0, 0, 0)) # Black text
            self.screen.blit(text_surface, (10, 10 + i * 15))
            
        rec_status = "RECORDING" if self.is_recording else "NOT RECORDING"
        rec_color = (255, 0, 0) if self.is_recording else (0, 128, 0)
        status_surface = self.font.render(rec_status, True, rec_color)
        self.screen.blit(status_surface, (10, self.screen.get_height() - 25))
        
        pygame.display.flip()

    def get_action(self) -> tuple[np.ndarray, bool, bool, bool, bool]:
        """
        Processes keyboard events and returns the corresponding robot action.

        Returns:
            A tuple containing:
            - action (np.ndarray): The 6D velocity command [vx, vy, vz, v_roll, v_pitch, v_yaw].
            - toggle_recording (bool): True if the recording state should be toggled.
            - go_home (bool): True if the robot should go to its home position.
            - toggle_gripper (bool): True if the gripper state should be toggled.
            - quit (bool): True if the program should exit.
        """
        toggle_recording = False
        go_home = False
        toggle_gripper = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.is_running = False
                if event.key == pygame.K_r:
                    toggle_recording = True
                    self.is_recording = not self.is_recording
                if event.key == pygame.K_h:
                    go_home = True
                if event.key == pygame.K_g:
                    toggle_gripper = True

        keys = pygame.key.get_pressed()
        self.action.fill(0)

        # Linear movements
        if keys[pygame.K_w]: self.action[0] = 1.0  # Forward (+X)
        if keys[pygame.K_s]: self.action[0] = -1.0 # Back (-X)
        if keys[pygame.K_a]: self.action[1] = 1.0  # Left (+Y)
        if keys[pygame.K_d]: self.action[1] = -1.0 # Right (-Y)
        if keys[pygame.K_q]: self.action[2] = 1.0  # Up (+Z)
        if keys[pygame.K_e]: self.action[2] = -1.0 # Down (-Z)
        
        # Angular movements
        if keys[pygame.K_j]: self.action[4] = 1.0  # Yaw Left (+Pitch, assuming camera orientation)
        if keys[pygame.K_l]: self.action[4] = -1.0 # Yaw Right (-Pitch)
        if keys[pygame.K_i]: self.action[3] = 1.0  # Pitch Up (+Roll)
        if keys[pygame.K_k]: self.action[3] = -1.0 # Pitch Down (-Roll)
        if keys[pygame.K_u]: self.action[5] = 1.0  # Roll Left (+Yaw)
        if keys[pygame.K_o]: self.action[5] = -1.0 # Roll Right (-Yaw)

        # Scale action by speed factors
        scaled_action = self.action.copy()
        scaled_action[:3] *= self.linear_speed_factor
        scaled_action[3:] *= self.angular_speed_factor
        
        self._update_display()

        return scaled_action, toggle_recording, go_home, toggle_gripper, not self.is_running

    def close(self):
        """Closes the Pygame window."""
        pygame.quit()

if __name__ == '__main__':
    # Example usage
    teleop = KeyboardTeleop()
    print("Pygame window opened for teleoperation. Press ESC to quit.")
    
    quit_program = False
    while not quit_program:
        action, rec, home, grip, quit_program = teleop.get_action()
        
        # Check if any action is being commanded
        if np.any(action):
            print(f"Action: {np.round(action, 2)}")
        if rec:
            print("Toggle Recording!")
        if home:
            print("Go Home!")
        if grip:
            print("Toggle Gripper!")

        # Small delay to prevent busy-looping and maxing out CPU
        pygame.time.wait(10)
        
    teleop.close()
    print("Teleoperation example finished.")
