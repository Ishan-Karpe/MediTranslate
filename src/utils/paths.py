import sys
from pathlib import Path

def get_resource_path(relative_path):
    try:
        base_path = Path(sys._MEIPASS) # temp folder for extracted files
    except Exception:
        base_path = Path(__file__).parent.parent.parent
    return base_path / relative_path