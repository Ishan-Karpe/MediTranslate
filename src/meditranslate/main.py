"""
src/meditranslate/main.py
Entry Point.
Features:
- Auto-Download of AI Models on first run.
- Global Error Handling (Crash Popup).
- Uses absolute package imports for PyPI distribution.
"""
import sys
import traceback
from loguru import logger
from PySide6.QtWidgets import QApplication, QMessageBox
from meditranslate.services.translation_service import TranslationService

def check_and_download_models():
    """
    Checks if models exist. If not, runs download.
    """
    service = TranslationService()
    if not service.model_dir.exists() or not any(service.model_dir.iterdir()):
        print("Models missing. Starting download...")
        
        try:
            from transformers import MarianMTModel, MarianTokenizer
            
            models = ["Helsinki-NLP/opus-mt-en-es", "Helsinki-NLP/opus-mt-en-hi"]
            
            for model in models:
                print(f"Downloading {model}...")
                save_path = service.model_dir / model
                MarianMTModel.from_pretrained(model).save_pretrained(save_path)
                MarianTokenizer.from_pretrained(model).save_pretrained(save_path)
            
            print("Models downloaded successfully.")
                
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False
            
    return True

# --- GLOBAL EXCEPTION HANDLER ---
def global_exception_handler(exc_type, exc_value, exc_traceback):
    """
    Catches any unhandled error so the app doesn't just vanish.
    """
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
    logger.info("Starting MediTranslate System...")

    try:
        app = QApplication(sys.argv)
        
        app.setStyle("Fusion")
        app.setApplicationName("MediTranslate")
        
        # 1. Check Models BEFORE showing UI
        if not check_and_download_models():
            QMessageBox.critical(None, "Error", "Failed to download AI models.\nCheck internet connection.")
            sys.exit(1)

        # 2. Launch UI
        from meditranslate.ui.main_window import MainWindow 
        window = MainWindow()
        window.show()

        logger.info("Application interface loaded successfully")
        sys.exit(app.exec())

    except Exception as e:
        logger.critical(f"Critical crash in main loop: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()