from datetime import datetime, timedelta
import tkinter.ttk as ttk
import tkinter as tk
import os

from Devices.Camera import Camera
from Devices.Microphone import Microphone

from GUI.WindowEvents import WindowEvents
from GUI.WindowUtils import WindowUtils

from Config.ConfigHandler import ConfigHandler
from Config import ConfigUtils
import Config.Settings as Settings


class MainWindow:
    """
    Main Tkinter GUI
    """

    @staticmethod
    def meter_color(volume_normalized):
        """
        Change audio meter color based on volume
        """
        if volume_normalized > Settings.METER_THRESHOLD_RED:
            color = Settings.METER_COLOR_RED
        elif volume_normalized > Settings.METER_THRESHOLD_ORANGE:
            color = Settings.METER_COLOR_ORANGE
        else:
            color = Settings.METER_COLOR_GREEN
        return color

    def update_meter(self, volume):
        """
        Update input device volume in audio meter
        """
        audio_clamp = Settings.AUDIO_CLAMP
        # volume capped at audio clamp
        volume_normalized = min(max(volume, audio_clamp), 0)
        color = self.meter_color(volume_normalized)
        height = self.audio_meter.winfo_height()
        meter_height = height - (volume_normalized - audio_clamp) / (-audio_clamp) * height
        self.audio_meter.coords(self.volume, 0, meter_height, Settings.AUDIO_METER_WIDTH, height)
        self.audio_meter.itemconfig(self.volume, fill=color)

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
        """
        Update recording status based on volume
        """
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
        """
        Update video feed for preview
        """
        frame = self.cam.retrieve_preview(self.preview_size)
        if frame:
            self.preview.imgtk = frame
            self.preview.itemconfig(self.cam_stream, image=frame)

            # Place image in center of canvas
            width, height = self.preview_size
            self.preview.coords(self.cam_stream, width / 2, height / 2)

            volume = self.mic.volume
            self.update_rec_status(volume)

            # Update volume meter
            self.update_meter(volume)
        # Schedule next frame update
        self.preview.after(40, self.update_preview)

    def init_camera(self):
        if self.available_cameras:
            cam_index = int(self.cam_index.get())
            resolution = self.resolution.get()
            if self.cam:
                # Don't initialize new cam if settings haven't changed
                if cam_index == self.cam.cam_index and resolution == self.cam.resolution:
                    return
                self.cam.close()
            self.cam = Camera(cam_index, resolution, self.overlay_enabled.get())

    def init_microphone(self):
        if self.mic:
            self.mic.close()
        device_name = self.input_device_name.get()
        device_index = self.input_devices[device_name]
        self.device_index = device_index
        self.mic = Microphone(self.device_index)

    def __init__(self):
        self.cam = None
        self.mic = None
        self.last_trigger = None
        self.rec_status = 0

        widget_opts = {
            'fg': Settings.WINDOW_FG_COLOR,
            'bg': Settings.WINDOW_BG_COLOR,
            'highlightthickness': 0
        }

        bg_color = Settings.WINDOW_BG_COLOR
        font_large = Settings.WINDOW_FONT_LARGE
        font_small = Settings.WINDOW_FONT_SMALL

        """
        REC status
        0 = Disabled
        1 = Enabled
        2 = Recording
        """

        # Init comp functions
        self.winEvent = WindowEvents(self)
        self.winUtil = WindowUtils(self)
        self.confHandler = ConfigHandler(self)

        # Setup main window
        self.window = tk.Tk()
        self.window.title(Settings.WINDOW_TITLE)
        self.winUtil.set_window_icon()

        # ========== START OF TK WIDGETS ==========

        # Display loading text
        loading_text = tk.Label(self.window, text='Scanning for video devices...', font=font_large, **widget_opts)
        loading_text.place(relx=.5, rely=.5, anchor='center')

        # Update window to show loading screen
        self.window.configure(bg=Settings.WINDOW_BG_COLOR)
        self.window.update_idletasks()

        self.center_frame = tk.Frame(self.window)
        self.center_frame.pack(fill='both', expand=True)

        self.center_frame.grid_rowconfigure(1, weight=1)
        self.center_frame.grid_columnconfigure(0, weight=1)

        self.top_frame = tk.Frame(self.center_frame, height=30, bg=bg_color)
        self.middle_frame = tk.Frame(self.center_frame, bg='black')
        self.bottom_frame = tk.Frame(self.center_frame, height=60, bg=bg_color)

        self.top_frame.grid(row=0, column=0, sticky='we')
        self.middle_frame.grid(row=1, column=0, sticky='nsew')
        self.bottom_frame.grid(row=2, column=0, sticky='we')

        # --------------- Top frame ---------------

        self.preview_label = tk.Label(self.top_frame, text='Preview', font=font_large, **widget_opts)
        self.preview_label.pack(side='left')

        self.threshold_label = tk.Label(self.top_frame, text='Threshold', font=font_large, **widget_opts)
        self.threshold_label.pack(side='right')

        # ---------------- Mid frame ---------------

        # Preview frame on the left
        self.preview_frame = tk.Frame(self.middle_frame, bg='black')
        self.preview_frame.pack(side='left', fill='both', expand=True)

        self.preview = tk.Canvas(self.preview_frame, bg='black', highlightthickness=0)
        self.preview.place(relx=.5, rely=.5, anchor='center')

        # Volume meter with fixed width on the right
        volume_meter_frame = tk.Frame(self.middle_frame, width=Settings.AUDIO_METER_WIDTH + 30)
        volume_meter_frame.pack(side='right', fill='y')

        self.audio_meter = tk.Canvas(volume_meter_frame, width=Settings.AUDIO_METER_WIDTH, highlightthickness=0)
        self.audio_meter.pack(side='left', fill='both', expand=True)

        self.threshold = tk.IntVar()
        self.threshold_slider = ttk.Scale(volume_meter_frame, from_=0, to=Settings.AUDIO_CLAMP, variable=self.threshold,
                                          command=lambda event: self.winEvent.update_thres(), orient='vertical')
        self.threshold_slider.pack(side='right', fill='y')

        # Audio Meter elements
        self.volume = self.audio_meter.create_rectangle(0, 0, 0, 0, outline='')
        self.threshold_line = self.audio_meter.create_line(0, 0, Settings.AUDIO_METER_WIDTH, 0, fill='red', width=2)

        # ============== Bottom frame ==============

        padding = 10

        # ------------- First column ------------

        device_label = tk.Label(self.bottom_frame, text='Device', font=font_large, **widget_opts)
        device_label.grid(row=0, column=0, sticky='w', padx=(0, padding))

        # Camera selection menu

        camera_label = tk.Label(self.bottom_frame, text='Camera', font=font_small, **widget_opts)
        camera_label.grid(row=0, column=1, sticky='w', padx=(0, padding))

        self.cam_index = tk.StringVar(value='-')
        self.available_cameras = Camera.get_available_cameras()
        if self.available_cameras:
            self.cam_index.set(self.available_cameras[0])
        cam_menu = ttk.OptionMenu(self.bottom_frame, self.cam_index, self.cam_index.get(), *self.available_cameras,
                                  command=lambda cam: self.init_camera())
        cam_menu.grid(row=0, column=2, sticky='we', padx=(0, padding))

        # Audio device selection

        mic_label = tk.Label(self.bottom_frame, text='Audio', font=font_small, **widget_opts)
        mic_label.grid(row=0, column=3, sticky='w', padx=(0, padding))

        # retrieve all audio input devices
        self.input_devices = Microphone.get_input_devices()

        self.input_device_names = list(self.input_devices.keys())
        self.input_device_name = tk.StringVar(value=self.input_device_names[0])
        self.device_index = self.input_devices[self.input_device_name.get()]

        mic_menu = ttk.OptionMenu(self.bottom_frame, self.input_device_name, self.input_device_names[0],
                                  *self.input_device_names[1:], command=lambda mic: self.init_microphone())
        mic_menu.grid(row=0, column=4, sticky='we', padx=(0, padding))

        self.start_button = ttk.Button(self.bottom_frame, text='Start', command=self.winEvent.toggle_recording)
        self.start_button.grid(row=0, column=5, sticky='w', padx=(0, padding))

        # ------------- Second column ------------

        output_label = tk.Label(self.bottom_frame, text='Output', font=font_large, **widget_opts)
        output_label.bind('<Double-1>', lambda event: self.winEvent.open_output())
        output_label.grid(row=1, column=0, sticky='w', padx=(0, padding))

        # Resolution

        res_label = tk.Label(self.bottom_frame, text='Resolution', font=font_small, **widget_opts)
        res_label.grid(row=1, column=1, sticky='w', padx=(0, padding))

        resolutions = Settings.RESOLUTIONS
        self.resolution = tk.StringVar(value=resolutions[0])
        self.res_menu = ttk.OptionMenu(self.bottom_frame, self.resolution, resolutions[0], *resolutions,
                                       command=lambda res: self.init_camera())
        self.res_menu.grid(row=1, column=2, sticky='w', padx=(0, padding))

        output_label = tk.Label(self.bottom_frame, text='Output', font=font_small, **widget_opts)
        output_label.grid(row=1, column=3, sticky='w', padx=(0, padding))

        documents_path = ConfigUtils.get_documents_dir()
        self.output = tk.StringVar(value=documents_path)
        output_text = ttk.Entry(self.bottom_frame, textvariable=self.output, state='readonly')
        output_text.grid(row=1, column=4, sticky='we', padx=(0, padding))

        browse_button = ttk.Button(self.bottom_frame, text='Browse', command=self.winEvent.set_output)
        browse_button.grid(row=1, column=5, sticky='w', padx=(0, padding))

        # HUD

        ttk.Button(self.bottom_frame, text='Screenshot').grid(row=0, column=6)

        self.overlay_enabled = tk.BooleanVar(value=True)
        self.overlay_button = ttk.Checkbutton(self.bottom_frame, text='Overlay', variable=self.overlay_enabled,
                                              command=self.winEvent.toggle_overlay)
        self.overlay_button.grid(row=1, column=6, sticky='we')

        # ========== END OF tk Widgets ==========

        #
        width, height = self.winUtil.get_preview_size()
        self.preview_size = (width, height)
        preview_center = (width / 2, height / 2)

        self.cam_stream = self.preview.create_image(*preview_center)
        self.window.bind("<Configure>", lambda event: self.winEvent.on_resize())

        # Load and apply settings from config file
        try:
            self.confHandler.load_config()
        except FileNotFoundError:
            pass
        # Update threshold line once after applying config
        self.winEvent.update_thres()

        self.init_microphone()
        if self.available_cameras:
            self.init_camera()
            self.update_preview()

        # Adjust window size
        default_win_geometry = self.winUtil.get_default_window_geometry()
        self.window.minsize(*default_win_geometry[:2])
        self.window.geometry('%dx%d+%d+%d' % default_win_geometry)

        loading_text.destroy()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cam:
            self.cam.close()
        self.mic.close()
        self.confHandler.save_config()
