# LeRobot + xArm 6 + RealSense: End-to-End Robot Learning Project

This project provides a complete, end-to-end solution for data collection, training, and deployment of robot learning policies for the UFACTORY xArm 6, using the Hugging Face `LeRobot` framework.

## Project Structure

- **`data_collection/`**: Scripts and modules for collecting demonstration data from the xArm 6 and a RealSense camera via keyboard teleoperation.
- **`data_processing/`**: (Coming soon) Utilities for inspecting, cleaning, and augmenting the collected datasets.
- **`training/`**: (Coming soon) Scripts and configurations for training policies like ACT or Diffusion Policy on the collected data.
- **`deployment/`**: (Coming soon) Scripts to run the trained policy on a Raspberry Pi for real-time inference and control.

## Hardware

- **Robot Arm**: UFACTORY xArm 6
- **Camera**: Intel RealSense D435 (wrist-mounted)
- **Host PC**: For data collection and training (e.g., Ubuntu with NVIDIA GPU).
- **Deployment Target**: Raspberry Pi 4/5 (for inference).

## Getting Started

1. Clone or download this repository.
2. Navigate into the `data_collection` directory.
3. Follow the instructions in `data_collection/README.md` to set up the environment and start collecting data.
