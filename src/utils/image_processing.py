"""
src/utils/image_processing.py
Image processing utils for medical image processing
"""

import cv2
import numpy as np
from loguru import logger

class ImageProcessor: # image enhancement utils for OCR
    def __init__(self):
        logger.debug("ImageProcessor initialized")

    def enhance_for_ocr(self, image: np.ndarray) -> np.ndarray: # return an enhanced image for OCR
        if image is None or image.size == 0:
            logger.warning("Empty image passed to processor")
            return image
        try:
            # grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            # smooth phone cameras
            denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)

            # make text more visible
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            clahed = clahe.apply(denoised)
            
            # rotated images
            deskewed = self._deskew(clahed)
            return cv2.cvtColor(deskewed, cv2.COLOR_GRAY2RGB)
        except Exception as e:
            logger.error(f"Error enhancing image for OCR: {e}")
            return image # original image  

    def _deskew(self, gray_image): # deskew image
        edges = cv2.Canny(gray_image, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
        
        if lines is None:
            return gray_image
        
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
        deskewed = cv2.warpAffine(gray_image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return deskewed

        