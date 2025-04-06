from PIL import Image, ImageTk
from datetime import datetime
from threading import Thread
import cv2

from Recorder.VideoRecorder import VideoRecorder
from Config import ConfigUtils
import Config.Settings as Settings


class Camera:
    """
    Resembles a Video camera
    """

    @staticmethod
    def get_backend():
        """
        Use different OpenCV backend depending on OS
        """
        if ConfigUtils.using_windows():
            return Settings.CAP_BACKEND_WIN
        else:
            return Settings.CAP_BACKEND_UNIX

    @staticmethod
    def get_available_cameras(max_cameras=5):
        """
        Determine all available cameras
        """
        available_cameras = []
        backend = Camera.get_backend()
        for i in range(max_cameras):
            cap = cv2.VideoCapture(i, backend)
            if cap.isOpened():
                available_cameras.append(i)
            cap.release()
        return available_cameras

    def retrieve_preview(self, size):
        """
        Retrieve camera preview for MainWindow
        """
        frame = self.current_frame
        if frame is None:
            return
        resized_frame = cv2.resize(frame, size)
        rec_status = self.rec_status
        if rec_status:
            cv2.circle(resized_frame, self.circle_pos, self.circle_radius, self.rec_colors[rec_status], -1)
        image = Image.fromarray(resized_frame)
        imgtk = ImageTk.PhotoImage(image=image)
        return imgtk

    def frame_capture(self):
        while self.capture:
            ret, cap = self.cap.read()
            if ret:
                if self.hud_enabled:
                    date_time_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                    cv2.putText(cap, date_time_str, self.text_pos, self.font,
                                self.font_size, (255, 255, 255), self.font_thickness)
                if self.recorder.is_recording:
                    self.recorder.add_frame(cap)
                self.recorder.buffer_frame(cap)
                frame = cv2.cvtColor(cap, cv2.COLOR_BGR2RGB)
                self.current_frame = frame

    def record(self, out_path):
        if self.recorder.is_recording:
            return
        self.recorder.record = True
        Thread(target=self.recorder.save_file, args=[out_path], daemon=True).start()

    def stop_recording(self):
        self.recorder.record = False

    def close(self):
        # Close camera
        self.capture = False
        self.cap_thread.join()
        self.cap.release()

    def __init__(self, cam_index, resolution, hud_enabled=False, fps=10, buffer_duration=5):
        self.cam_index = cam_index
        self.resolution = resolution
        self.hud_enabled = hud_enabled

        # Frame capture
        self.capture = True
        self.current_frame = None
        self.cap_thread = Thread(target=self.frame_capture, daemon=True)

        # Recording settings
        self.rec_status = 0
        self.rec_colors = {
            1: Settings.REC_COLOR_GREEN,
            2: Settings.REC_COLOR_RED
        }

        """
        REC status
        0 = Disabled
        1 = Enabled
        2 = Recording
        """

        width, height = resolution.split('x')
        width, height = int(width), int(height)

        self.recorder = VideoRecorder((width, height), fps, buffer_duration)

        # HUD Settings
        self.text_pos = (int(width * 0.01), int(height * 0.05))
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_size = width / 1280
        self.font_thickness = max(1, int(width / 480))
        self.circle_pos = (464, 11)
        self.circle_radius = 6

        # Create opencv videocapture
        backend = self.get_backend()
        self.cap = cv2.VideoCapture(self.cam_index, backend)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)

        self.cap_thread.start()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
