from Config import Settings
from PIL import Image, ImageTk
import os


class WindowUtils:
    """
    Utilities for Window scaling
    """

    def __init__(self, MainWindow):
        # MainWindow class
        self.main = MainWindow

    def get_preview_size(self):
        """
        Determine maximum preview size maintaining its aspect ratio
        """
        # determine aspect ratio
        width, height = map(int, self.main.resolution.get().split('x'))
        aspect_ratio = width / height

        # Calculate width including audio meter
        audio_meter_width = Settings.AUDIO_METER_WIDTH + self.main.threshold_slider.winfo_width()
        max_width = self.main.window.winfo_width() - audio_meter_width
        max_height = self.main.window.winfo_height() - (
                    self.main.top_frame.winfo_height() + self.main.bottom_frame.winfo_height())
        if max_width / max_height > aspect_ratio:
            # Window is too wide, limit by height
            height = max_height
            width = round(height * aspect_ratio)
        else:
            # Window is too tall, limit by width
            width = max_width
            height = round(width / aspect_ratio)
        return width, height

    def get_start_window_geometry(self):
        """
        Return window size at start (when widgets aren't already initialized)
        """
        screen_width, screen_height = self.get_window_size()

        window_width = screen_width * Settings.WINDOW_REL_SIZE
        window_height = screen_height * Settings.WINDOW_REL_SIZE

        return (
            round(window_width),
            round(window_height),
            round((screen_width - window_width) / 2),
            round((screen_height - window_height) / 2)
        )

    def get_default_window_geometry(self):
        """
        Return default window size & position
        """

        # Update widget position
        self.main.window.update_idletasks()

        preview_width = self.main.preview_frame.winfo_width()
        preview_height = preview_width / Settings.PREVIEW_ASPECT_RATIO

        top_height = self.main.top_frame.winfo_height()
        bottom_height = self.main.bottom_frame.winfo_height()

        window_width = self.main.center_frame.winfo_width()
        window_height = top_height + preview_height + bottom_height

        screen_width, screen_height = self.get_window_size()
        return (
            round(window_width),
            round(window_height),
            round((screen_width - window_width) / 2),
            round((screen_height - window_height) / 2)
        )

    def set_window_icon(self):
        """
        Set Window Icon based on OS
        """
        if os.name == 'nt':
            # Windows
            self.main.window.iconbitmap(Settings.ICON_PATH_WIN)
        else:
            # Linux / UNIX / macOS
            icon = Image.open(Settings.ICON_PATH_UNIX)
            icon = ImageTk.PhotoImage(icon)
            self.main.window.iconphoto(True, icon)

    def get_window_size(self):
        """
        Get current window size
        """
        screen_width = self.main.window.winfo_screenwidth()
        screen_height = self.main.window.winfo_screenheight()
        return screen_width, screen_height
