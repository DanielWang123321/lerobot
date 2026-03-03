import time
import click
from pathlib import Path
import numpy as np
from tqdm import tqdm

from lerobot.common.datasets.lerobot_dataset import LeRobotDatasetWriter
from xarm_robot import XArm6Robot
from realsense_camera import RealSenseCamera
from pika_teleop import PikaTeleop # <-- IMPORT CHANGE

ROBOT_IP = "192.168.1.208"
FRAME_RATE = 20
CAMERA_WIDTH = 424
CAMERA_HEIGHT = 240
CONTROL_HZ = 20

@click.command()
@click.option("--output-dir", "-o", type=click.Path(), required=True, help="Directory to save the recorded episodes.")
def main(output_dir):
    print("--- LeRobot xArm 6 Data Collection (Pika Sense) ---")
    
    try:
        robot = XArm6Robot(ip_address=ROBOT_IP, control_frequency_hz=CONTROL_HZ)
        camera = RealSenseCamera(width=CAMERA_WIDTH, height=CAMERA_HEIGHT, fps=FRAME_RATE)
        teleop = PikaTeleop() # <-- TELEOP CHANGE
        
        robot.connect()
        camera.start()
    except Exception as e:
        print(f"FATAL: Failed to initialize hardware: {e}")
        return

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    writer = LeRobotDatasetWriter(output_path)
    print(f"Data will be saved to: {output_path}")

    is_recording = False
    last_rec_toggle_state = False
    episode_data = []

    try:
        while True:
            start_time = time.perf_counter()

            action, rec_toggle_pressed, _, _, quit_program = teleop.get_action() # <-- ACTION CHANGE

            if quit_program: break

            # Edge detection for the recording button
            if rec_toggle_pressed and not last_rec_toggle_state:
                if not is_recording:
                    is_recording = True
                    episode_data = []
                    print("REC ON")
                else:
                    is_recording = False
                    if len(episode_data) > 10:
                        print(f"REC OFF. Saving episode with {len(episode_data)} steps...")
                        episode_to_save = {key: [d[key] for d in episode_data] for key in episode_data[0]}
                        for key in episode_to_save:
                            episode_to_save[key] = np.array(episode_to_save[key])
                        writer.add_episode(episode_to_save)
                        print("Episode saved!")
                    else:
                        print("Episode too short, not saving.")
            last_rec_toggle_state = rec_toggle_pressed
            
            robot.send_action(action)
            robot_obs = robot.get_observation()
            cam_success, color_img, depth_img = camera.get_frames()

            if not cam_success:
                print("Warning: Failed to get camera frame.")
                continue

            if is_recording:
                step_data = {
                    'observation.camera_color_image': color_img,
                    'observation.camera_depth_image': depth_img,
                    'observation.state': np.concatenate([robot_obs['q'], robot_obs['gripper_state']]),
                    'action': action,
                    'timestamp': time.time(),
                }
                episode_data.append(step_data)

            elapsed_time = time.perf_counter() - start_time
            sleep_time = (1.0 / CONTROL_HZ) - elapsed_time
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nInterrupted. Shutting down.")
    finally:
        print("Cleaning up...")
        if 'robot' in locals(): robot.disconnect()
        if 'camera' in locals(): camera.stop()
        if 'teleop' in locals(): teleop.close()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
