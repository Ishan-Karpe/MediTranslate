"""
src/utils/image_processing.py
Image processing utilities for medical document OCR.
"""
import cv2
import numpy as np
from loguru import logger

class ImageProcessor:
    def __init__(self):
        logger.debug("ImageProcessor initialized")
    
    def enhance_for_ocr(self, image: np.ndarray, force_binary: bool = False) -> np.ndarray:
        if image is None or image.size == 0:
            return image

        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
            
            if force_binary:
                _, processed = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            else:
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                processed = clahe.apply(denoised)
            
            final = self._deskew(processed)
            
            return cv2.cvtColor(final, cv2.COLOR_GRAY2RGB)
            
        except Exception as e:
            logger.error(f"Enhancement pipeline failed: {e}")
            return image

    def _deskew(self, gray_image):
        edges = cv2.Canny(gray_image, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
        
        if lines is None: return gray_image
        
        angles = []
        for line in lines:
            rho, theta = line[0]
            angle = np.degrees(theta) - 90
            angles.append(angle)
        
        if not angles: return gray_image
        median_angle = np.median(angles)
        
        if abs(median_angle) > 15 or abs(median_angle) < 0.5:
            return gray_image
            
        (h, w) = gray_image.shape
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, median_angle, 1.0)

        return cv2.warpAffine(gray_image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))