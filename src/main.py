"""
src/main.py
Entry Point with Global Error Handling.
"""
import sys
import os
import traceback # <--- NEW
from loguru import logger
from PySide6.QtWidgets import QApplication, QMessageBox # <--- NEW

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from ui.main_window import MainWindow

# --- GLOBAL EXCEPTION HANDLER ---
def global_exception_handler(exc_type, exc_value, exc_traceback):
    """
    Catches any unhandled error so the app doesn't just vanish.
    """
    # Log it first
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))
    
    # Show Popup to User
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

# Register the hook
sys.excepthook = global_exception_handler

def main():
    logger.add("meditranslate.log", rotation="1 MB", level="DEBUG")
    logger.info("🚀 Starting MediTranslate System...")

    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        app.setApplicationName("MediTranslate")
        app.setOrganizationName("BridgeAI")

        window = MainWindow()
        window.show()

        logger.info("Application interface loaded successfully")
        sys.exit(app.exec())

    except Exception as e:
        logger.critical(f"🔥 Critical crash in main loop: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()