import pyrealsense2 as rs
import numpy as np
import cv2

class RealSenseCamera:
    """
    A wrapper for the Intel RealSense D435 camera to simplify frame capture.
    """

    def __init__(self, width: int = 640, height: int = 480, fps: int = 30):
        """
        Args:
            width: The width of the desired image resolution.
            height: The height of the desired image resolution.
            fps: The desired frames per second.
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.pipeline = rs.pipeline()
        self.config = rs.config()

        # Check if a RealSense device is connected
        ctx = rs.context()
        if len(ctx.devices) == 0:
            raise RuntimeError("No RealSense device connected. Please plug in the camera.")
            
        # Get device product line for setting specific options
        pipeline_wrapper = rs.pipeline_wrapper(self.pipeline)
        pipeline_profile = self.config.resolve(pipeline_wrapper)
        device = pipeline_profile.get_device()

        self.config.enable_stream(rs.stream.depth, self.width, self.height, rs.format.z16, self.fps)
        self.config.enable_stream(rs.stream.color, self.width, self.height, rs.format.bgr8, self.fps)
        
        # For wrist-mounted cameras, disabling the laser emitter can reduce interference
        # and battery consumption. Enable it if you need active depth sensing.
        # depth_sensor = device.first_depth_sensor()
        # if depth_sensor.supports(rs.option.emitter_enabled):
        #     depth_sensor.set_option(rs.option.emitter_enabled, 0) # 0 to disable, 1 to enable

    def start(self):
        """
        Starts the camera pipeline and prepares for frame capture.
        """
        print("Starting RealSense camera stream...")
        try:
            self.profile = self.pipeline.start(self.config)
            # Create an align object
            # rs.align allows us to align depth frames to color frames
            # This is important for tasks that require pixel-perfect correspondence
            align_to = rs.stream.color
            self.align = rs.align(align_to)
            print("RealSense camera started successfully.")
        except Exception as e:
            print(f"Failed to start RealSense camera: {e}")
            raise

    def get_frames(self) -> tuple[bool, np.ndarray | None, np.ndarray | None]:
        """
        Waits for and retrieves the next set of aligned frames from the camera.

        Returns:
            A tuple containing:
            - success (bool): True if frames were retrieved successfully.
            - color_image (np.ndarray | None): The BGR color image.
            - depth_image (np.ndarray | None): The depth image in millimeters.
        """
        try:
            frames = self.pipeline.wait_for_frames(timeout_ms=2000) # 2-second timeout
        except RuntimeError as e:
            print(f"Error waiting for frames: {e}. Is the camera still connected?")
            return False, None, None
            
        if not frames:
            return False, None, None

        aligned_frames = self.align.process(frames)
        
        depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()

        if not depth_frame or not color_frame:
            return False, None, None

        # Convert images to numpy arrays
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        return True, color_image, depth_image

    def stop(self):
        """
        Stops the camera pipeline.
        """
        print("Stopping RealSense camera stream...")
        try:
            self.pipeline.stop()
            print("Camera stopped.")
        except Exception as e:
            print(f"Error stopping camera: {e}")

if __name__ == '__main__':
    # Example usage:
    try:
        camera = RealSenseCamera()
        camera.start()
        
        print("Displaying camera feed. Press 'q' to quit.")
        while True:
            success, color_img, depth_img = camera.get_frames()
            if not success:
                print("Failed to get frames. Exiting.")
                break

            # Apply a colormap to the depth image for visualization
            depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_img, alpha=0.03), cv2.COLORMAP_JET)

            # Stack color and depth images horizontally for display
            images = np.hstack((color_img, depth_colormap))

            cv2.namedWindow('RealSense Feed', cv2.WINDOW_AUTOSIZE)
            cv2.imshow('RealSense Feed', images)

            key = cv2.waitKey(1)
            # Press 'q' to exit
            if key & 0xFF == ord('q') or key == 27:
                cv2.destroyAllWindows()
                break
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'camera' in locals():
            camera.stop()
