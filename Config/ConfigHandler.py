from configparser import ConfigParser
import os

import Config.Settings as Settings


class ConfigHandler:
    """
    Handles everything config related, e.g. loading and saving config files
    """

    def save_config(self):
        """
        Save settings to config file
        """
        self.config['Cam'] = {
            'index': self.main.cam_index.get(),
            'resolution': self.main.resolution.get(),
            'hud': self.main.hud_enabled.get()
        }
        self.config['Mic'] = {
            'index': self.main.device_index,
            'name': self.main.input_device_name.get(),
            'threshold': self.main.threshold.get()
        }
        self.config['Output'] = {
            'path': self.main.output.get()
        }

        try:
            os.makedirs(self.config_folder)
        except FileExistsError:
            pass

        with open(self.config_file, 'w') as file:
            self.config.write(file)

    def load_config(self):
        """
        Load and verify settings from config file
        """

        if not os.path.isfile(self.config_file):
            raise FileNotFoundError('Config file not found')

        self.config.read(self.config_file)

        # Camera settings
        cam_index = self.config['Cam']['index']
        try:
            if self.main.available_cameras:
                if int(cam_index) in self.main.available_cameras:
                    # Set to last used cam index
                    self.main.cam_index.set(cam_index)
        except ValueError:
            pass

        # Resolution settings
        resolution = self.config['Cam']['resolution']
        if resolution in Settings.RESOLUTIONS:
            self.main.resolution.set(resolution)

        # HUD settings
        hud_enabled = self.config['Cam']['hud']
        if hud_enabled in ('True', 'False'):
            self.main.hud_enabled.set(hud_enabled)

        # Input device settings
        input_device_name = self.config['Mic']['name']
        try:
            input_device_index = int(self.config['Mic']['index'])
            if self.main.input_devices[input_device_name] == input_device_index:
                # Set index and name to last used input device if name and index match up
                self.main.device_index = input_device_index
                self.main.input_device_name.set(input_device_name)
        except (ValueError, KeyError):
            pass

        # Threshold settings
        audio_clamp = Settings.AUDIO_CLAMP
        threshold = self.config['Mic']['threshold']
        try:
            if audio_clamp <= int(threshold) <= 0:
                self.main.threshold.set(threshold)
        except ValueError:
            pass

        # Output settings
        output = self.config['Output']['path']
        if os.path.isdir(output):
            self.main.output.set(output)

    def __init__(self, MainWindow):
        self.main = MainWindow
        config_root = os.path.join(os.environ['LOCALAPPDATA'], 'WolfSoftware')
        self.config_folder = os.path.join(config_root, 'CamRecording')
        self.config_file = os.path.join(self.config_folder, 'config.ini')
        self.config = ConfigParser()
