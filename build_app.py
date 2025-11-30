import PyInstaller.__main__
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).parent

def build():
    if Path("dist").exists(): shutil.rmtree("dist")
    if Path("build").exists(): shutil.rmtree("build")

    add_data = [
        (str(ROOT / 'src' / 'meditranslate' / 'data'), 'meditranslate/data'),
        (str(ROOT / 'src' / 'meditranslate' / 'resources'), 'meditranslate/resources'),
        (str(ROOT / '.env'), '.') 
    ]

    sep = ';' if os.name == 'nt' else ':'
    data_args = [f"{src}{sep}{dest}" for src, dest in add_data]

    print("Starting Build...")
    PyInstaller.__main__.run([
        'src/meditranslate/main.py',         
        '--name=MediTranslate',
        '--windowed',
        '--onedir',
        '--clean',
        '--noconfirm',
        '--paths=src', 
        
        *[f'--add-data={arg}' for arg in data_args],
        
        # Hidden imports
        '--hidden-import=pdf2image',
        '--hidden-import=reportlab',
        '--hidden-import=pyside6',
        '--hidden-import=cv2',
        '--hidden-import=numpy',
        '--hidden-import=meditranslate', 
    ])
    
    print("\nBuild Complete! Check the 'dist/MediTranslate' folder.")

if __name__ == "__main__":
    build()