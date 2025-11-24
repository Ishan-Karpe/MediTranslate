"""
src/main.py
The Application Entry Point.
"""
import sys
import os
from loguru import logger
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))

def main():
    logger.add('meditranslate.log', rotation='1 MB')
    logger.info("Starting MediTranslate...")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()


