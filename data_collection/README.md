# Data Collection for LeRobot + xArm 6

This directory contains the scripts necessary to collect demonstration data from an xArm 6 robot with a wrist-mounted RealSense camera, controlled via keyboard teleoperation.

## 1. Setup

### Prerequisites
- You have a UFACTORY xArm 6 connected to your network.
- You have an Intel RealSense D435 camera connected to your host PC via USB 3.
- Your host PC is running a Linux-based OS (e.g., Ubuntu 20.04/22.04).

### Installation
1.  **Create a Conda Environment (Recommended)**:
    ```bash
    conda create -n lerobot python=3.10
    conda activate lerobot
    ```

2.  **Install Python Dependencies**:
    Navigate to this directory in your terminal and run:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `pyrealsense2` can sometimes be tricky. If the pip install fails, you may need to install it from source or via other methods described in the official RealSense documentation.*

3.  **Install UFACTORY xArm SDK**:
    The `xarm-python-sdk` should be installed by the `requirements.txt` file. If you encounter issues, follow the official installation guide on the [xArm Developer Center](https://www.ufactory.cc/developer/en/xarm-sdk-introduction).

## 2. Configuration

Before running the script, you need to configure the robot's IP address.

-   **Find your robot's IP**: You can find this in the xArm Studio software or from your network router.
-   **Edit `record_episode.py`**: Open the `record_episode.py` script and change the `ROBOT_IP` variable at the top of the file to match your robot's IP address.

## 3. Running the Data Collection Script

Once the environment is set up and configured, you can start collecting data.

1.  **Run the script**:
    ```bash
    python record_episode.py --output-dir ./my_xarm_dataset
    ```
    - The `--output-dir` argument specifies where the collected episodes will be saved. Each episode will be a subdirectory within this main directory.

2.  **Teleoperation Control Window**:
    A small Pygame window will appear. This window must be **in focus** to capture your keyboard commands. The controls are:
    - **Linear Movement**:
        - `W`/`S`: Move Forward/Backward (+/- X direction)
        - `A`/`D`: Move Left/Right (+/- Y direction)
        - `Q`/`E`: Move Up/Down (+/- Z direction)
    - **Rotational Movement**:
        - `I`/`K`: Pitch Up/Down
        - `J`/`L`: Yaw Left/Right
        - `U`/`O`: Roll Left/Right
    - **Episode & Robot Control**:
        - `R`: **Start/Stop Recording** a new episode.
        - `H`: Send the robot to a predefined Home position.
        - `G`: (Placeholder) Toggle the gripper.
        - `ESC`: **Quit** the application safely.

## 4. Data Format

The script saves data in the `LeRobotDataset` format, which is ready for training with the `LeRobot` framework. Each episode is saved in its own folder (e.g., `episode_0`, `episode_1`, etc.) containing:
- `trajectory.parquet`: A file storing all state and action data for each timestep.
- `camera_color.mp4`: A video of the color images from the camera.
- `camera_depth.mp4`: (Optional) A video of the depth images.
- `meta.json`: Metadata about the episode.
