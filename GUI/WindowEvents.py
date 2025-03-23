import tkinter.filedialog
import subprocess
import os

import Config.Settings as Settings


class WindowEvents:
    """
    Events when user interacts with UI
    """

    def __init__(self, MainWindow):
        # MainWindow class
        self.main = MainWindow

    def update_thres(self, threshold):
        # Update threshold line in preview canvas
        audio_clamp = Settings.AUDIO_CLAMP
        width, height = self.main.preview_size
        # x / height = threshold / audio_clamp
        line_height = int(threshold) / audio_clamp * height
        print(width, height, threshold, audio_clamp)
        print(0, line_height, width, line_height)
        self.main.preview.coords(self.main.thres_line, 0, line_height, width, line_height)

    def open_output(self):
        # Open output folder in Windows explorer
        output = os.path.normpath(self.main.output.get())
        subprocess.Popen(f'explorer "{output}"')

    def set_output(self):
        # Browse files to set output directory
        output = tkinter.filedialog.askdirectory()
        if os.path.isdir(output):
            self.main.output.set(output)

    def toggle_hud(self):
        if self.main.hud_enabled.get():
            self.main.cam.hud_enabled = True
        else:
            self.main.cam.hud_enabled = False

    def toggle_recording(self):
        if self.main.rec_status:
            # Disable recording
            rec_status = 0
            self.main.start_button.config(text='Start')
            self.main.stop_recording()
        else:
            # Enable recording
            rec_status = 1
            self.main.start_button.config(text='Stop')
        self.main.rec_status = rec_status
        self.main.cam.rec_status = rec_status
