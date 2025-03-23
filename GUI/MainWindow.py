from datetime import datetime, timedelta
from PIL import Image, ImageTk
import tkinter.ttk as ttk
import tkinter as tk
import os

from Devices.Camera import Camera
from Devices.Microphone import Microphone
from GUI.WindowEvents import WindowEvents

from Config.ConfigHandler import ConfigHandler
from Config import ConfigUtils
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
        #self.preview.coords(self.volume, 480, meter_height, 502, 272)
        #self.preview.itemconfig(self.volume, fill=color)

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

    def get_window_size(self):
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        return screen_width, screen_height

    def get_default_window_size(self):
        """
        Return default window size & position
        """
        screen_width, screen_height = self.get_window_size()
        rel_width, rel_height = Settings.WINDOW_REL_SIZE
        window_width = round(screen_width * rel_width)
        window_height = round(screen_height * rel_height)
        return (
            (window_width, window_height),
            (
                round((screen_width - window_width) / 2),
                round((screen_height - window_height) / 2)
            )
        )

    def set_window_icon(self):
        if os.name == 'nt':
            # Windows
            self.window.iconbitmap(Settings.ICON_PATH_WIN)
        else:
            # Linux / UNIX / macOS
            icon = Image.open(Settings.ICON_PATH_UNIX)
            icon = ImageTk.PhotoImage(icon)
            self.window.iconphoto(True, icon)

    def on_resize(self):
        border_x = Settings.PREVIEW_BORDER_X
        border_y = Settings.PREVIEW_BORDER_Y
        aspect_ratio = Settings.PREVIEW_ASPECT_RATIO
        audio_meter_width = Settings.AUDIO_METER_WIDTH

        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()


        # Calculate width including audio meter
        max_width = window_width - (2 * border_x + audio_meter_width)
        max_height = window_height - 2 * border_y

        aspect_width, aspect_height = aspect_ratio
        aspect_ratio = aspect_width / aspect_height

        if max_width / max_height > aspect_ratio:
            # Window is too wide, limit by height
            height = max_height
            width = round(height * aspect_ratio)
        else:
            # Window is too tall, limit by width
            width = max_width
            height = round(width / aspect_ratio)

        if (width, height) != self.preview_size:
            # Only change when preview is resized
            self.preview_size = (width, height)
            frame_width = width + audio_meter_width

            self.center_frame.config(width=frame_width, height=height)
            self.center_frame.place(relx=.5, rely=.5, anchor='center')

            self.db_label.place(x=frame_width, y=0, anchor='ne')

            self.thres_slider.config(length=height - 30)
            self.thres_slider.place(x=frame_width, y=30, anchor='ne')


    def __init__(self):
        self.cam = None
        self.mic = None
        self.preview_size = None
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
        self.winevent = WindowEvents(self)
        self.conf_handler = ConfigHandler(self)

        # Setup main window
        self.window = tk.Tk()
        self.window.title(Settings.WINDOW_TITLE)
        self.set_window_icon()

        # Set default window position
        default_win_size, default_win_pos = self.get_default_window_size()
        self.window.minsize(*default_win_size)
        self.window.geometry('%dx%d+%d+%d' % (default_win_size + default_win_pos))

        # Display loading text
        loading_text = tk.Label(self.window, text='Scanning for video devices...', font=font_large, **widget_opts)
        loading_text.place(relx=.5, rely=.5, anchor='center')

        self.window.configure(bg=Settings.WINDOW_BG_COLOR)
        self.window.update_idletasks()

        self.center_frame = tk.Frame(self.window)
        top_frame = tk.Frame(self.center_frame, height=30, bg=bg_color)
        middle_frame = tk.Frame(self.center_frame, bg=bg_color)
        bottom_frame = tk.Frame(self.center_frame, height=60, bg=bg_color)

        top_frame.pack(side='top', fill='x')
        middle_frame.pack(side='top', fill='both', expand=True)
        bottom_frame.pack(side='bottom', fill='x')

        self.center_frame.pack(fill="both", expand=True)

        # --------------- Top frame ---------------

        self.preview_label = tk.Label(top_frame, text='Preview', font=font_large, **widget_opts)
        self.preview_label.pack(side='left')

        self.db_label = tk.Label(top_frame, text='Audio threshold', font=font_large, **widget_opts)
        self.db_label.pack(side='right')

        # ---------------- Mid frame ---------------

        self.preview = tk.Canvas(middle_frame, bg='black', highlightthickness=0)
        self.preview.pack(side='left')

        self.threshold = tk.IntVar()
        self.thres_slider = ttk.Scale(middle_frame,from_=0, to=Settings.AUDIO_CLAMP,variable=self.threshold,
                                     command=self.winevent.update_thres, orient='vertical')
        self.thres_slider.pack(side='right', fill='y')

        self.audio_meter = tk.Canvas(middle_frame, width=Settings.AUDIO_METER_WIDTH, bg='black', highlightthickness=0)
        self.audio_meter.pack(side='right', fill='y')

        # ============== Bottom frame ==============

        padding = 20

        # ------------- First column ------------

        first_col = tk.Frame(bottom_frame, height=30, bg=bg_color)
        first_col.pack(side='top', fill='x')

        device_label = tk.Label(first_col, text='Device', font=font_large, **widget_opts)
        device_label.pack(side='left', padx=(0, padding))

        # Camera selection menu

        camera_label = tk.Label(first_col, text='Camera', font=font_small, **widget_opts)
        camera_label.pack(side='left', padx=(0, padding))

        self.cam_index = tk.StringVar(value='-')
        self.available_cameras = Camera.get_available_cameras()
        if self.available_cameras:
            self.cam_index.set(self.available_cameras[0])
        cam_menu = ttk.OptionMenu(first_col, self.cam_index, self.cam_index.get(),*self.available_cameras[1:],
                                  command=lambda cam: self.init_camera())
        cam_menu.pack(side='left', padx=(0, padding))

        # Audio device selection

        mic_label = tk.Label(first_col, text='Audio', font=font_small, **widget_opts)
        mic_label.pack(side='left', padx=(0, padding))

        # retrieve all audio input devices
        self.input_devices = Microphone.get_input_devices()

        self.input_device_names = list(self.input_devices.keys())
        self.input_device_name = tk.StringVar(value=self.input_device_names[0])
        self.device_index = self.input_devices[self.input_device_name.get()]

        mic_menu = ttk.OptionMenu(first_col, self.input_device_name, self.input_device_names[0],
                                      *self.input_device_names[1:],command=lambda mic: self.init_microphone())
        mic_menu.pack(side='left')


        # ------------- Second column ------------

        sec_col = tk.Frame(bottom_frame, height=30, bg=bg_color)
        sec_col.pack(side='bottom', fill='x')

        output_label = tk.Label(sec_col, text='Output', font=font_large, **widget_opts)
        output_label.bind('<Double-1>', lambda event: self.winevent.open_output())
        output_label.pack(side='left', padx=(0, padding))

        # Resolution

        res_label = tk.Label(sec_col, text='Resolution', font=font_small, **widget_opts)
        res_label.pack(side='left', padx=(0, padding))

        resolutions = Settings.RESOLUTIONS
        self.resolution = tk.StringVar(value=resolutions[1])
        self.res_menu = ttk.OptionMenu(sec_col, self.resolution, resolutions[0], *resolutions[1:],
                                       command=lambda res: self.init_camera())
        self.res_menu.pack(side='left', padx=(0, padding))

        # HUD

        self.hud_enabled = tk.BooleanVar(value=True)
        self.hud_button = ttk.Checkbutton(sec_col, text='HUD', variable=self.hud_enabled,
                       command=self.winevent.toggle_hud)
        self.hud_button.pack(side='left', padx=(0, padding))

        documents_path = ConfigUtils.get_documents_dir()
        self.output = tk.StringVar(value=documents_path)
        output_text = ttk.Entry(sec_col, textvariable=self.output, state='readonly')
        output_text.pack(side='left', padx=(0, padding), fill='x', expand=True)

        browse_button = ttk.Button(sec_col, text='Browse', command=self.winevent.set_output)
        browse_button.pack(side='left', padx=(0, padding))

        self.start_button = ttk.Button(sec_col, text='Start', command=self.winevent.toggle_recording)
        self.start_button.pack(side='left')

        # Load and apply settings from config file
        try:
            self.conf_handler.load_config()
        except FileNotFoundError:
            pass

        """self.on_resize()

        width, height = self.preview_size
        preview_center = (width / 2, height / 2)

        self.preview.create_text(*preview_center, text='No cam found', fill='white', anchor='center')

        self.volume = self.preview.create_rectangle(0, 0, width, 0, fill='green')
        self.thres_line = self.preview.create_line(0, 0, width, 0, fill='red', width=2)

        self.cam_stream = self.preview.create_image(*preview_center)

        self.window.bind("<Configure>", lambda event: self.on_resize())

        self.winevent.update_thres(self.threshold.get())

        self.init_microphone()
        if self.available_cameras:
            self.init_camera()
            self.update_preview()"""

        loading_text.destroy()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cam:
            self.cam.close()
        self.mic.close()
        self.conf_handler.save_config()
