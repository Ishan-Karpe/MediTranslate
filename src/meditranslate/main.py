"""
src/main.py
Entry Point with Global Error Handling.
"""
import sys
import os
import traceback
from loguru import logger
from PySide6.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def global_exception_handler(exc_type, exc_value, exc_traceback):
    # Catches unhandled errors so that the app doesn't vanish
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))
    
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # Check if QApplication exists before showing message box
    if QApplication.instance():
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("MediTranslate has encountered a critical error.")
        msg.setInformativeText("The application needs to close.")
        msg.setDetailedText(error_msg)
        msg.setWindowTitle("Critical Error")
        msg.exec()
    
    sys.exit(1)

sys.excepthook = global_exception_handler

def main():
    logger.add("meditranslate.log", rotation="1 MB", level="DEBUG")
    logger.info("Starting MediTranslate System...")

    try:
        app = QApplication(sys.argv)
        app.setApplicationName("MediTranslate")

        window = MainWindow()
        window.show()

        logger.info("Application interface loaded successfully")
        sys.exit(app.exec())

    except Exception as e:
        logger.critical(f"Critical crash in main loop: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()