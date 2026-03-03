import time
import click
from pathlib import Path
import numpy as np
from tqdm import tqdm

# LeRobot's dataset handling utility
from lerobot.common.datasets.lerobot_dataset import LeRobotDatasetWriter

# Our custom hardware interfaces
from xarm_robot import XArm6Robot
from realsense_camera import RealSenseCamera
from keyboard_teleop import KeyboardTeleop

# --- Configuration ---
# IMPORTANT: Change this to your robot's IP address
ROBOT_IP = "192.168.1.208"  

# Camera and control loop settings
FRAME_RATE = 10  # Hz
CAMERA_WIDTH = 424 # Using a smaller resolution for faster processing
CAMERA_HEIGHT = 240
CONTROL_HZ = 10

@click.command()
@click.option("--output-dir", "-o", type=click.Path(), required=True, help="Directory to save the recorded episodes.")
def main(output_dir):
    """
    Main script for recording teleoperated robot episodes.
    """
    print("--- LeRobot xArm 6 Data Collection ---")
    
    # Initialize hardware and teleoperation
    try:
        robot = XArm6Robot(ip_address=ROBOT_IP, control_frequency_hz=CONTROL_HZ)
        camera = RealSenseCamera(width=CAMERA_WIDTH, height=CAMERA_HEIGHT, fps=FRAME_RATE)
        teleop = KeyboardTeleop()
        
        # Connect to hardware
        robot.connect()
        camera.start()
        
    except Exception as e:
        print(f"FATAL: Failed to initialize hardware: {e}")
        return

    # Initialize the dataset writer
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    writer = LeRobotDatasetWriter(output_path)
    print(f"Data will be saved to: {output_path}")

    # Main control loop
    is_recording = False
    episode_data = []

    try:
        while True:
            start_time = time.perf_counter()

            # Get action from teleop interface
            action, toggle_rec, go_home, toggle_grip, quit_program = teleop.get_action()

            if quit_program:
                print("Quit signal received. Shutting down.")
                break

            if go_home:
                robot.reset()
                continue
            
            # --- Recording Logic ---
            if toggle_rec:
                if not is_recording:
                    # Start a new recording
                    is_recording = True
                    episode_data = []
                    print("Starting new episode recording...")
                else:
                    # Stop recording and save the episode
                    is_recording = False
                    if len(episode_data) > 10: # Only save if it's a meaningful length
                        print(f"Stopping recording. Saving episode with {len(episode_data)} steps...")
                        # This is a simplified saving logic. LeRobotDatasetWriter expects
                        # the full episode data at once.
                        # We need to format the collected data correctly.
                        
                        # Restructure the data from a list of dicts to a dict of lists/arrays
                        episode_to_save = {key: [] for key in episode_data[0].keys()}
                        for step in episode_data:
                            for key, value in step.items():
                                episode_to_save[key].append(value)

                        # Convert lists to numpy arrays
                        for key, value in episode_to_save.items():
                           episode_to_save[key] = np.array(value)

                        writer.add_episode(episode_to_save)
                        print("Episode saved!")
                    else:
                        print("Episode too short, not saving.")
            
            # --- Robot Control and Data Capture ---
            # Send action to the robot
            robot.send_action(action)
            
            # Get observations from robot and camera
            robot_obs = robot.get_observation()
            cam_success, color_img, depth_img = camera.get_frames()

            if not cam_success:
                print("Warning: Failed to get camera frame.")
                continue

            if is_recording:
                # Add a "timestamp" to prevent LeRobot complaining about missing keys
                timestamp = time.time()
                
                # LeRobot expects specific keys for images
                # Rename 'q' to 'state_observation_q' for clarity if needed, but 'q' is fine
                step_data = {
                    'observation.camera_color_image': color_img,
                    'observation.camera_depth_image': depth_img,
                    'observation.state': robot_obs['q'], # Using joint positions as primary state
                    'action': action,
                    'timestamp': timestamp,
                }
                episode_data.append(step_data)

            # Maintain the control loop frequency
            elapsed_time = time.perf_counter() - start_time
            sleep_time = (1.0 / CONTROL_HZ) - elapsed_time
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nCaught KeyboardInterrupt. Shutting down gracefully.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        # Cleanup
        print("Cleaning up resources...")
        if 'writer' in locals() and is_recording and len(episode_data) > 10:
             print("There was an unsaved episode. Do you want to save it? (y/n)")
             # In a real script, you'd handle this. For now, we discard.
        
        if 'robot' in locals():
            robot.disconnect()
        if 'camera' in locals():
            camera.stop()
        if 'teleop' in locals():
            teleop.close()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
