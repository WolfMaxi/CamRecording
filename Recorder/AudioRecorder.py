from collections import deque
from time import sleep
import soundfile as sf
import cv2


class AudioRecorder:
    def flush_buffer(self, out_file):
        # Flush circular buffer
        buffer = self.circ_buffer.copy()
        for chunk in buffer:
            out_file.write(chunk)

    def save_file(self, out_path):
        self.is_recording = True
        query_interval = 1 / self.samplerate
        with sf.SoundFile(out_path, mode='w', samplerate=self.samplerate,
                          channels=self.channels, subtype='PCM_16') as out_file:
            self.flush_buffer(out_file)
            while self.record:
                if len(self.audio_buffer) == 0:
                    sleep(query_interval)
                    continue
                in_data = self.audio_buffer.popleft()
                out_file.write(in_data)
        self.is_recording = False

    def add_audio_chunk(self, in_data):
        self.audio_buffer.append(in_data)

    def buffer_audio_chunk(self, in_data):
        self.circ_buffer.append(in_data)

    def __init__(self, samplerate, channels, buffer_duration=5, audio_buffer_size=1323000):
        self.samplerate = samplerate
        self.channels = channels

        self.record = False
        self.is_recording = False

        self.buffer_size = 50000
        self.circ_buffer = deque(maxlen=self.buffer_size)
        self.audio_buffer = deque(maxlen=audio_buffer_size)
        self.writer = cv2.VideoWriter_fourcc(*'XVID')
