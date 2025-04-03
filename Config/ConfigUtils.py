from pathlib import Path
from Config import Settings
import subprocess
import os

using_windows = os.name == 'nt'


def get_config_dir():
    """
    Retrieve Config Directory under Windows / UNIX
    """
    if using_windows:
        return os.path.join(os.environ['USERPROFILE'], Settings.CONFIG_PATH)  # Windows
    else:
        return os.path.join('~/.config', Settings.CONFIG_PATH) # UNIX


def get_documents_dir():
    """
    Retrieve standard output directory under Windows / UNIX
    """
    if using_windows:
        return os.path.join(os.environ['USERPROFILE'], 'Documents')
    else:
        # Try xdg-user-dir
        try:
            result = subprocess.run(["xdg-user-dir", "DOCUMENTS"], capture_output=True, text=True, check=True)
            documents_dir = result.stdout.strip()
            if documents_dir and Path(documents_dir).exists():
                return Path(documents_dir)
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass  # xdg-user-dir is missing or failed

        # Check XDG environment variables
        xdg_documents = os.getenv("XDG_DOCUMENTS_DIR")
        if xdg_documents and Path(xdg_documents).exists():
            return Path(xdg_documents)

        #Default fallback to ~/Documents (Linux/macOS standard)
        fallback_dir = Path.home() / "Documents"
        return fallback_dir if fallback_dir.exists() else Path.home()
