from threading import Thread
import sounddevice as sd
import numpy as np

from Recorder.AudioRecorder import AudioRecorder


class Microphone:
    """
    Resembles an audio input device
    """

    @staticmethod
    def get_input_devices():
        # Retrieve available audio input devices
        devices = sd.query_devices()
        input_devices = {}
        for device in devices:
            if device['max_input_channels'] > 0:
                input_devices[device['name']] = device['index']
        return input_devices

    @staticmethod
    def calculate_volume(in_data):
        # Calculate volume from audio data
        rms = np.sqrt(np.mean(in_data ** 2))
        if rms > 0:
            volume = 20 * np.log10(rms)
        else:
            volume = -np.inf
        return volume

    def callback(self, in_data, frames, time, status):
        self.volume = self.calculate_volume(in_data)
        if self.recorder.is_recording:
            self.recorder.add_audio_chunk(in_data)
        self.recorder.buffer_audio_chunk(in_data)

    def record(self, out_path):
        if self.recorder.is_recording:
            return
        self.recorder.record = True
        Thread(target=self.recorder.save_file, args=[out_path], daemon=True).start()

    def stop_recording(self):
        self.recorder.record = False

    def close(self):
        # Close audio stream
        self.stream.close()

    def __init__(self, device_index):
        self.volume = -np.inf
        self.stream = sd.InputStream(device=device_index, blocksize=2048, callback=self.callback)

        # Initialize Audio recorder
        samplerate = int(self.stream.samplerate)
        channels = int(self.stream.channels)
        self.recorder = AudioRecorder(samplerate, channels, 5)

        self.stream.start()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
