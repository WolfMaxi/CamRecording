from win32api import GetSystemMetrics
from datetime import datetime, timedelta
import tkinter as tk
import os

from Devices.Camera import Camera
from Devices.Microphone import Microphone
from GUI.WindowEvents import WindowEvents
from Config.ConfigHandler import ConfigHandler
import Config.Settings as Settings


class MainWindow:
    """
    Main Tkinter GUI
    """

    @staticmethod
    def meter_color(volume_normalized):
        # Change volume meter color based on level
        if volume_normalized > Settings.METER_THRESHOLD_RED:
            color = Settings.METER_COLOR_RED
        elif volume_normalized > Settings.METER_THRESHOLD_ORANGE:
            color = Settings.METER_COLOR_ORANGE
        else:
            color = Settings.METER_COLOR_GREEN
        return color

    def update_meter(self, volume):
        # Update input device volume in preview
        audio_clamp = Settings.AUDIO_CLAMP
        volume_normalized = min(max(volume, audio_clamp), 0)
        color = self.meter_color(volume_normalized)
        meter_height = 272 + int((volume_normalized - audio_clamp) / audio_clamp * 270)
        self.preview.coords(self.volume, 480, meter_height, 502, 272)
        self.preview.itemconfig(self.volume, fill=color)

    def start_recording(self):
        output = self.output.get()
        date_time = datetime.now() - timedelta(seconds=5)
        filename = date_time.strftime('%d-%m-%Y %H-%M-%S')
        video_out = os.path.join(output, filename + '.mkv')
        audio_out = os.path.join(output, filename + '.wav')
        self.cam.record(video_out)
        self.mic.record(audio_out)

    def stop_recording(self):
        self.cam.stop_recording()
        self.mic.stop_recording()

    def update_rec_status(self, volume):
        # Update recording status based on volume
        if self.rec_status:
            rec_status = None
            if volume >= self.threshold.get():
                rec_status = 2
                if self.last_trigger is None:
                    self.start_recording()
                self.last_trigger = datetime.now()
            elif self.last_trigger:
                duration = datetime.now() - self.last_trigger
                if duration.total_seconds() > 5:
                    rec_status = 1
                    self.stop_recording()
                    self.last_trigger = None
            if rec_status:
                self.rec_status = rec_status
                self.cam.rec_status = rec_status

    def update_preview(self):
        # Update camera preview
        frame = self.cam.retrieve_preview()
        if frame:
            self.preview.imgtk = frame
            self.preview.itemconfig(self.cam_stream, image=frame)

            volume = self.mic.volume
            self.update_rec_status(volume)

            # Update volume meter
            self.update_meter(volume)
        # Schedule next frame update
        self.preview.after(40, self.update_preview)

    def init_camera(self):
        # Initialize camera
        if self.available_cameras:
            cam_index = int(self.cam_index.get())
            resolution = self.resolution.get()
            if self.cam:
                # Don't initialize new cam if settings haven't changed
                if cam_index == self.cam.cam_index and resolution == self.cam.resolution:
                    return
                self.cam.close()
            self.cam = Camera(cam_index, resolution, self.hud_enabled.get())

    def init_microphone(self):
        if self.mic:
            self.mic.close()
        device_name = self.input_device_name.get()
        device_index = self.input_devices[device_name]
        self.device_index = device_index
        self.mic = Microphone(self.device_index)

    def __init__(self):
        width = Settings.WINDOW_WIDTH
        height = Settings.WINDOW_HEIGHT

        window_geometry = '%dx%d+%d+%d' % (
            width, height, round((GetSystemMetrics(0) - width) / 2), round((GetSystemMetrics(1) - height) / 2)
        )

        self.cam = None
        self.mic = None
        self.last_trigger = None
        self.rec_status = 0

        """
        REC status
        0 = Disabled
        1 = Enabled
        2 = Recording
        """

        # Init comp functions
        self.winevent = WindowEvents(self)
        self.conf_handler = ConfigHandler(self)

        # Setup main window
        self.window = tk.Tk()
        self.window.title(Settings.WINDOW_TITLE)
        self.window.resizable(False, False)
        self.window.geometry(window_geometry)
        self.window.iconbitmap(Settings.ICON_FILE)

        # Display loading text
        loading_text = tk.Label(self.window, text='Scanning for video devices...', bg='white')
        loading_text.place(relx=.5, rely=.5, anchor='center')
        self.window.update_idletasks()

        # --------------- Preview ---------------

        tk.Label(self.window, text='Preview').place(x=10, y=0)

        self.preview = tk.Canvas(self.window, width=500, height=270, bg='black')
        self.preview.create_text(242, 137, text='No cam found', fill='white')
        self.volume = self.preview.create_rectangle(480, 0, 500, 0, fill='green')
        self.thres_line = self.preview.create_line(480, 2, 500, 2, fill='red')
        self.cam_stream = self.preview.create_image(242, 137)
        self.preview.place(x=10, y=20)

        # ---------------- Slider ---------------

        tk.Label(self.window, text='db').place(x=532, y=0)

        self.threshold = tk.IntVar()
        self.thres_slider = tk.Scale(self.window, from_=0, to=Settings.AUDIO_CLAMP, variable=self.threshold,
                                     command=self.winevent.update_thres, length=270, sliderlength=10)
        self.thres_slider.place(x=510, y=20)

        # ---------------- Camera ---------------

        tk.Label(self.window, text='Camera').place(x=10, y=300)

        self.cam_index = tk.StringVar(value='-')
        self.available_cameras = Camera.get_available_cameras()
        if self.available_cameras:
            self.cam_index.set(self.available_cameras[0])
        tk.OptionMenu(self.window, self.cam_index, self.cam_index.get(), *self.available_cameras[1:],
                      command=lambda cam: self.init_camera()).place(x=55, y=298, width=50, height=25)

        # -------------- Resolution -------------

        tk.Label(self.window, text='Resolution').place(x=110, y=300)

        resolutions = Settings.RESOLUTIONS
        self.resolution = tk.StringVar(value=resolutions[1])
        tk.OptionMenu(self.window, self.resolution, resolutions[0], *resolutions[1:],
                      command=lambda res: self.init_camera()).place(x=170, y=298, width=90, height=25)

        # ------------- Input device ------------

        tk.Label(self.window, text='Input device').place(x=265, y=300)

        # retrieve all audio input devices
        self.input_devices = Microphone.get_input_devices()

        self.input_device_names = list(self.input_devices.keys())
        self.input_device_name = tk.StringVar(value=self.input_device_names[0])
        self.device_index = self.input_devices[self.input_device_name.get()]

        tk.OptionMenu(self.window, self.input_device_name, self.input_device_names[0], *self.input_device_names[1:],
                      command=lambda mic: self.init_microphone()).place(x=335, y=298, width=218, height=25)

        # ---------------- Output ---------------

        output_label = tk.Label(self.window, text='Output')
        output_label.bind('<Double-1>', lambda event: self.winevent.open_output())
        output_label.place(x=10, y=332)

        self.output = tk.StringVar(value=os.path.join(os.environ['USERPROFILE'], 'Documents'))
        tk.Entry(self.window, textvariable=self.output, state='readonly').place(x=57, y=334, width=278)
        tk.Button(self.window, text='Browse', command=self.winevent.set_output).place(x=337, y=332, width=60, height=20)

        # ------------------ HUD -----------------

        self.hud_enabled = tk.BooleanVar(value=True)
        tk.Checkbutton(self.window, text='HUD', variable=self.hud_enabled,
                       command=self.winevent.toggle_hud).place(x=410, y=332, width=50, height=20)

        self.start_button = tk.Button(self.window, text='Start', command=self.winevent.toggle_recording)
        self.start_button.place(x=470, y=332, width=80, height=20)

        # ----------------------------------------

        # Load and apply settings from config file
        try:
            self.conf_handler.load_config()
        except FileNotFoundError:
            pass

        self.winevent.update_thres(self.threshold.get())

        self.init_microphone()
        if self.available_cameras:
            self.init_camera()
            self.update_preview()

        loading_text.destroy()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cam:
            self.cam.close()
        self.mic.close()
        self.conf_handler.save_config()
