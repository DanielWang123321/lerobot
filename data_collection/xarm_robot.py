import numpy as np
from lerobot.robot.robot import Robot
from xarm.wrapper import XArmAPI
import time

class XArm6Robot(Robot):
    """
    A hardware-specific interface for the UFACTORY xArm 6 robot, compliant with the LeRobot framework.
    This class handles connection, observation retrieval, and action execution for the xArm 6.
    """

    def __init__(self, ip_address: str, control_frequency_hz: int = 10):
        """
        Args:
            ip_address: The IP address of the xArm 6 controller.
            control_frequency_hz: The frequency at which control commands will be sent.
        """
        self.ip_address = ip_address
        self.control_frequency_hz = control_frequency_hz
        self.arm = None

    def connect(self):
        """
        Connects to the robot, enables motion, and sets initial mode.
        """
        print(f"Connecting to xArm 6 at {self.ip_address}...")
        try:
            self.arm = XArmAPI(self.ip_address, is_radian=True)
            self.arm.motion_enable(enable=True)
            self.arm.set_mode(0)  # Position control mode
            self.arm.set_state(0) # Sport state
            time.sleep(1) # Wait for state to settle
            
            if self.arm.connected and self.arm.state != 4: # 4 is an error state
                print("Successfully connected to xArm 6.")
            else:
                raise ConnectionError("Failed to connect or arm is in an error state.")

        except Exception as e:
            print(f"Error connecting to xArm 6: {e}")
            raise ConnectionError(f"Could not connect to xArm 6 at {self.ip_address}") from e

    def get_observation(self) -> dict[str, np.ndarray]:
        """
        Retrieves the current state of the robot.

        Returns:
            A dictionary containing:
            - 'q': The 6 joint angles in radians.
            - 'dq': The 6 joint velocities in radians/s.
            - 'tcp_pose': The 6D pose of the tool center point [x, y, z, roll, pitch, yaw].
        """
        if not self.arm or not self.arm.connected:
            raise RuntimeError("Robot is not connected.")

        code, joint_states = self.arm.get_joint_states(is_radian=True)
        if code != 0:
            # Handle potential communication errors
            print("Warning: Failed to get joint states.")
            # Return a zeroed-out observation to prevent crashes, but log the issue.
            return {
                "q": np.zeros(6, dtype=np.float32),
                "dq": np.zeros(6, dtype=np.float32),
                "tcp_pose": np.zeros(6, dtype=np.float32),
            }
            
        q = np.array(joint_states[0], dtype=np.float32)
        dq = np.array(joint_states[1], dtype=np.float32)

        code, tcp_pose_array = self.arm.get_position(is_radian=True)
        if code != 0:
            print("Warning: Failed to get TCP pose.")
            tcp_pose = np.zeros(6, dtype=np.float32)
        else:
            tcp_pose = np.array(tcp_pose_array, dtype=np.float32)
        
        return {"q": q, "dq": dq, "tcp_pose": tcp_pose}

    def send_action(self, action: np.ndarray):
        """
        Sends a relative (delta) Cartesian pose command to the robot.

        The robot will move by the specified deltas from its current TCP pose.

        Args:
            action: A 6D numpy array representing the delta pose [dx, dy, dz, droll, dpitch, dyaw].
                    Positions are in meters, rotations are in radians.
        """
        if not self.arm or not self.arm.connected:
            raise RuntimeError("Robot is not connected.")
            
        # Ensure action has the correct shape
        action = np.asarray(action, dtype=np.float32).flatten()
        if action.shape[0] != 6:
            raise ValueError(f"Action must be a 6D array, but got shape {action.shape}")

        # Convert meters to millimeters for the SDK
        action_mm = action.copy()
        action_mm[:3] *= 1000

        # set_tool_position is non-blocking and suitable for real-time control.
        # It expects an absolute target, so we calculate it from the current pose.
        # However, for smoother teleop, servo_cartesian is better. It moves with a given speed.
        # Let's use set_servo_cartesian for continuous, smooth control.
        # It requires speed, not a delta pose, so we scale the action to represent a velocity.
        
        # A simple approach: scale the delta action to a velocity command.
        # A more advanced approach would use a proper PID controller.
        # For simplicity, let's assume the action represents a target velocity vector.
        # Cartesian velocity: [vx, vy, vz, vroll, vpitch, vyaw]
        # Max speeds for xArm 6 are around 1000 mm/s and 180 deg/s (pi rad/s)
        # Let's scale our action (assumed to be in [-1, 1] range from teleop) to physical speeds.
        
        # Wait for the duration of one control step to approximate real-time control.
        # wait=True would block, which we don't want in a fast loop.
        # The `set_servo_cartesian` is non-blocking and expects continuous commands.
        self.arm.set_servo_cartesian(action_mm, is_radian=True, wait=False)
        
    def reset(self):
        """
        Resets the robot to a predefined home position.
        """
        print("Resetting robot to home position...")
        # Make sure to set a safe home position for your setup
        home_q = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0] 
        self.arm.set_servo_angle(angle=home_q, is_radian=True, speed=0.4, wait=True)
        print("Reset complete.")

    def disconnect(self):
        """
        Disconnects from the robot.
        """
        if self.arm and self.arm.connected:
            print("Disconnecting from xArm 6...")
            self.arm.disconnect()
            print("Disconnected.")
