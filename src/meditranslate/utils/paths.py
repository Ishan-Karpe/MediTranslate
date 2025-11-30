import sys
import os
from pathlib import Path

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        # Frozen Mode (PyInstaller temp folder)
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent.parent.parent.parent

    return base_path / relative_path