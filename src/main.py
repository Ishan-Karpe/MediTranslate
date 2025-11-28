"""
src/main.py
The Entry Point for MediTranslate.
"""
import sys
import os
from loguru import logger
from PySide6.QtWidgets import QApplication

# 1. Setup Path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from ui.main_window import MainWindow

def main():
    logger.add("meditranslate.log", rotation="1 MB", level="DEBUG")
    logger.info("🚀 Starting MediTranslate System...")

    try:
        app = QApplication(sys.argv)
        
        app.setStyle("Fusion")
        
        app.setApplicationName("MediTranslate")

        window = MainWindow()
        window.show()

        logger.info("Application interface loaded successfully")
        
        sys.exit(app.exec())

    except Exception as e:
        logger.critical(f"🔥 Critical crash: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()