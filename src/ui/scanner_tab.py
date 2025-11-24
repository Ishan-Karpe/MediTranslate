"""
src/ui/scanner_tab.py
Handles document upload, camera capture, and preview.
"""
from pathlib import Path
import cv2
import numpy as np
from loguru import logger
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QGroupBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage

# Import the processor we just wrote
from utils.image_processing import ImageProcessor

class ScannerTab(QWidget):
    
    # Signal: Emits the image data when ready (we will use this tomorrow for OCR)
    image_loaded = Signal(np.ndarray)
    
    def __init__(self):
        super().__init__()
        self.image_processor = ImageProcessor()
        self.current_image = None
        self.original_image = None
        self._setup_ui()
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- TOP: Controls ---
        controls_group = QGroupBox("Input Source")
        controls_layout = QHBoxLayout(controls_group)
        
        self.upload_btn = QPushButton("Upload File")
        self.upload_btn.setMinimumHeight(40)
        self.upload_btn.clicked.connect(self._upload_image)
        
        self.camera_btn = QPushButton("Use Camera")
        self.camera_btn.setMinimumHeight(40)
        self.camera_btn.clicked.connect(self._capture_from_camera)
        
        controls_layout.addWidget(self.upload_btn)
        controls_layout.addWidget(self.camera_btn)
        main_layout.addWidget(controls_group)
        
        # --- MIDDLE: Image Preview ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.image_label = QLabel("No document loaded")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("font-size: 16px; color: #888; background: #eee;")
        
        self.scroll_area.setWidget(self.image_label)
        main_layout.addWidget(self.scroll_area)
        
        self.info_label = QLabel("Ready to scan.")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.info_label)
        
        # --- BOTTOM: Actions ---
        action_layout = QHBoxLayout()
        self.enhance_btn = QPushButton("Auto-Enhance")
        self.enhance_btn.clicked.connect(self._enhance_image)
        self.enhance_btn.setEnabled(False)
        
        self.reset_btn = QPushButton("Reset Original")
        self.reset_btn.clicked.connect(self._reset_image)
        self.reset_btn.setEnabled(False)
        
        action_layout.addWidget(self.enhance_btn)
        action_layout.addWidget(self.reset_btn)
        main_layout.addLayout(action_layout)

    def _upload_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Document", str(Path.home()), "Images (*.png *.jpg *.jpeg)")
        if file_path:
            img = cv2.imread(file_path)
            if img is not None:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                self._load_image_data(img_rgb, f"File: {Path(file_path).name}")

    def _capture_from_camera(self):
        try:
            cap = cv2.VideoCapture(0) # Try default camera
            if not cap.isOpened(): cap = cv2.VideoCapture(1) # Try secondary
            if not cap.isOpened(): raise RuntimeError("No camera found.")
            
            # Warmup
            for _ in range(5): cap.read()
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self._load_image_data(frame_rgb, "Source: Camera Capture")
        except Exception as e:
            QMessageBox.warning(self, "Camera Error", str(e))

    def _load_image_data(self, image_rgb, info_text):
        self.original_image = image_rgb.copy()
        self.current_image = image_rgb.copy()
        self.info_label.setText(info_text)
        self.enhance_btn.setEnabled(True)
        self.reset_btn.setEnabled(True)
        self._display_current()
        self.image_loaded.emit(self.current_image)

    def _display_current(self):
        h, w, ch = self.current_image.shape
        bytes_per_line = ch * w
        qt_img = QImage(self.current_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        pixmap = QPixmap.fromImage(qt_img)
        if w > 800: # Limit max width for display
             pixmap = pixmap.scaledToWidth(800, Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(pixmap)

    def _enhance_image(self):
        if self.current_image is not None:
            self.current_image = self.image_processor.enhance_for_ocr(self.current_image)
            self._display_current()
            self.info_label.setText(self.info_label.text() + " | Enhanced ✨")

    def _reset_image(self):
        if self.original_image is not None:
            self.current_image = self.original_image.copy()
            self._display_current()
            self.info_label.setText(self.info_label.text().split('|')[0].strip())
            
    def reset_state(self):
        self.current_image = None
        self.image_label.clear()
        self.image_label.setText("No document loaded")
        self.enhance_btn.setEnabled(False)