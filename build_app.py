"""
build_app.py
building the dist file for distrubution.
"""

import PyInstaller.__main__
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).parent

def build():
    if Path("dist").exists(): shutil.rmtree("dist")
    if Path("build").exists(): shutil.rmtree("build")

    add_data = [
        (str(ROOT / 'src' / 'data'), 'src/data'),
        (str(ROOT / 'src' / 'resources'), 'src/resources'),
        (str(ROOT / '.env'), '.') 
    ]

    sep = ';' if os.name == 'nt' else ':'
    data_args = [f"{src}{sep}{dest}" for src, dest in add_data]

    print("Starting Build...")
    PyInstaller.__main__.run([
        'src/main.py',                       
        '--name=MediTranslate',              
        '--windowed',                        
        '--onedir',                          
        '--clean',
        '--noconfirm',
        '--paths=src', 

        *[f'--add-data={arg}' for arg in data_args],
        
        '--hidden-import=pdf2image',
        '--hidden-import=reportlab',
        '--hidden-import=pyside6',
        '--hidden-import=PIL',
        '--hidden-import=cv2',
        '--hidden-import=numpy',
    ])
    
    print("\nBuild Complete! Check the 'dist/MediTranslate' folder.")

if __name__ == "__main__":
    build()