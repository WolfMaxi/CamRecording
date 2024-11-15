from collections import deque
from time import sleep
import cv2


class VideoRecorder:
    def flush_buffer(self, out_file):
        # Flush circular buffer
        for frame in list(self.circ_buffer):
            out_file.write(frame)

    def save_file(self, out_path):
        self.is_recording = True
        query_interval = 1 / self.fps
        out_file = cv2.VideoWriter(out_path, self.writer, self.fps, self.resolution)
        self.flush_buffer(out_file)
        while self.record:
            if len(self.frame_buffer) > 0:
                frame = self.frame_buffer.popleft()
                out_file.write(frame)
            sleep(query_interval)
        out_file.release()
        self.is_recording = False

    def add_frame(self, frame):
        # Add frame to write to a file
        self.frame_buffer.append(frame)

    def buffer_frame(self, frame):
        # Add frame to circular buffer
        self.circ_buffer.append(frame)

    def __init__(self, resolution, fps, buffer_duration=5, frame_buffer_size=300):
        self.resolution = resolution
        self.fps = fps

        self.record = False
        self.is_recording = False

        buffer_size = int(fps * buffer_duration)
        self.circ_buffer = deque(maxlen=buffer_size)
        self.frame_buffer = deque(maxlen=frame_buffer_size)
        self.writer = cv2.VideoWriter_fourcc(*'XVID')
