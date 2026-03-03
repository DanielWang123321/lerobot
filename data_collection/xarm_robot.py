import numpy as np
from lerobot.robot.robot import Robot
from xarm.wrapper import XArmAPI
import time

class XArm6Robot(Robot):
    """
    Updated interface for the UFACTORY xArm 6, now with PIKA Gripper support.
    """
    def __init__(self, ip_address: str, control_frequency_hz: int = 20):
        self.ip_address = ip_address
        self.control_frequency_hz = control_frequency_hz
        self.arm = None

    def connect(self):
        print(f"Connecting to xArm 6 at {self.ip_address}...")
        try:
            self.arm = XArmAPI(self.ip_address, is_radian=True)
            self.arm.motion_enable(enable=True)
            self.arm.set_mode(0)
            self.arm.set_state(0)
            # Gripper setup
            self.arm.set_gripper_mode(0)
            self.arm.set_gripper_enable(True)
            self.arm.set_gripper_speed(1000)
            time.sleep(1)
            if not (self.arm.connected and self.arm.state != 4):
                raise ConnectionError("Failed to connect or arm is in an error state.")
            print("Successfully connected to xArm 6 and PIKA Gripper.")
        except Exception as e:
            raise ConnectionError(f"Could not connect to xArm 6: {e}") from e

    def get_observation(self) -> dict[str, np.ndarray]:
        code, joint_states = self.arm.get_joint_states(is_radian=True)
        if code != 0:
            q = np.zeros(6, dtype=np.float32)
            dq = np.zeros(6, dtype=np.float32)
        else:
            q = np.array(joint_states[0], dtype=np.float32)
            dq = np.array(joint_states[1], dtype=np.float32)
            
        code, tcp_pose_array = self.arm.get_position(is_radian=True)
        tcp_pose = np.array(tcp_pose_array, dtype=np.float32) if code == 0 else np.zeros(6, dtype=np.float32)
        
        # Get gripper position
        code, gripper_pos = self.arm.get_gripper_position()
        # Normalize gripper position to [0, 1] (0=closed, 1=open), assuming range is ~[0, 850]
        gripper_state = np.array([np.clip(gripper_pos / 850.0, 0.0, 1.0)], dtype=np.float32) if code == 0 else np.zeros(1, dtype=np.float32)

        return {"q": q, "dq": dq, "tcp_pose": tcp_pose, "gripper_state": gripper_state}

    def send_action(self, action: np.ndarray):
        action = np.asarray(action, dtype=np.float32).flatten()
        if action.shape[0] != 7:
            raise ValueError(f"Action must be a 7D array [dx, dy, dz, droll, dpitch, dyaw, gripper], but got shape {action.shape}")

        pose_action = action[:6].copy()
        gripper_action = action[6]

        # Cartesian control
        pose_action[:3] *= 1000 # convert to mm
        self.arm.set_servo_cartesian(pose_action, is_radian=True, wait=False)

        # Gripper control (binary action: > 0.5 means close, <= 0.5 means open)
        current_gripper_pos = self.get_observation()['gripper_state'][0]
        if gripper_action > 0.5 and current_gripper_pos > 0.1:
            self.arm.set_gripper_position(0, wait=False) # Close
        elif gripper_action <= 0.5 and current_gripper_pos < 0.9:
            self.arm.set_gripper_position(850, wait=False) # Open

    def reset(self):
        print("Resetting robot to home position...")
        home_q = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0] 
        self.arm.set_servo_angle(angle=home_q, is_radian=True, speed=0.4, wait=True)
        self.arm.set_gripper_position(850, wait=True) # Open gripper
        print("Reset complete.")

    def disconnect(self):
        if self.arm and self.arm.connected:
            print("Disconnecting from xArm 6...")
            self.arm.disconnect()
            print("Disconnected.")
