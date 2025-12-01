import sys
from pathlib import Path

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = Path(sys._MEIPASS) / "meditranslate"
    else:
        base_path = Path(__file__).parent.parent

    clean_rel_path = str(relative_path).replace("src/meditranslate/", "").replace("src/", "")
    
    return base_path / clean_rel_path