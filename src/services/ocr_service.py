"""
src/services/ocr_service.py
Handles the Optical Character Recognition (OCR) logic.
"""
import pytesseract
from loguru import logger
import cv2
import numpy as np

class OCRService:
    def __init__(self):
        logger.info("OCRService initialized")
        self._check_tesseract()

    def _check_tesseract(self):
        try:
            ver = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract Version: {ver}")
        except Exception as e:
            logger.critical(f"Tesseract not found: {e}")

    def extract_text(self, image: np.ndarray, lang: str = 'eng') -> str:
        if image is None: return ""
            
        try:
            logger.debug(f"Starting OCR with language: {lang}")
            
            # --- NEW CONFIGURATION ---
            # --psm 3: Fully automatic page segmentation (Good for full docs)
            # --psm 6: Assume a single uniform block of text (Good for paragraphs)
            # We will try PSM 3 first as it's the most robust for mixed forms.
            custom_config = r'--oem 3 --psm 3'
            
            text = pytesseract.image_to_string(
                image, 
                lang=lang, 
                config=custom_config # <--- Inject config here
            )
            
            # DEBUG: Print to terminal to see what Tesseract ACTUALLY found
            # This helps you see if it's a font issue or an OCR issue
            print("\n=== RAW OCR OUTPUT START ===")
            print(text)
            print("=== RAW OCR OUTPUT END ===\n")
            
            if not text.strip():
                return "[No text detected. Try Enhancing the image.]"
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"OCR Failed: {e}")
            return f"Error reading document: {e}"