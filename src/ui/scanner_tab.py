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
    QFileDialog, QMessageBox, QGroupBox, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage, QFont

from utils.image_processing import ImageProcessor

class ScannerTab(QWidget):
    
    # Signal: Emits the image data when ready
    image_loaded = Signal(np.ndarray)
    
    def __init__(self):
        super().__init__()
        self.image_processor = ImageProcessor()
        self.current_image = None
        self.original_image = None
        
        # 1. Setup Layout
        self._setup_ui()
        
        # 2. Apply Styling
        self._apply_styles() 
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # --- TOP: Controls ---
        controls_group = QGroupBox("STEP 1: SELECT SOURCE")
        controls_group.setObjectName("HeaderGroup")
        controls_layout = QHBoxLayout(controls_group)
        controls_layout.setSpacing(15)
        
        self.upload_btn = QPushButton("Upload File")
        self.upload_btn.setObjectName("PrimaryButton")
        self.upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.upload_btn.clicked.connect(self._upload_image)
        
        self.camera_btn = QPushButton("Use Camera")
        self.camera_btn.setObjectName("SecondaryButton")
        self.camera_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.camera_btn.clicked.connect(self._capture_from_camera)
        
        controls_layout.addWidget(self.upload_btn)
        controls_layout.addWidget(self.camera_btn)
        main_layout.addWidget(controls_group)
        
        # --- MIDDLE: Image Preview ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        self.image_label = QLabel("\n\nNo Document Loaded\n\nSelect a source above to begin")
        self.image_label.setObjectName("EmptyState")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_area.setWidget(self.image_label)
        main_layout.addWidget(self.scroll_area)
        
        self.info_label = QLabel("Ready to scan.")
        self.info_label.setObjectName("InfoLabel")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.info_label)
        
        # --- BOTTOM: Actions ---
        actions_group = QGroupBox("STEP 2: ENHANCE")
        actions_group.setObjectName("HeaderGroup")
        action_layout = QHBoxLayout(actions_group)
        
        self.enhance_btn = QPushButton("Auto-Enhance")
        self.enhance_btn.setObjectName("ActionButton")
        self.enhance_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.enhance_btn.clicked.connect(self._enhance_image)
        self.enhance_btn.setEnabled(False)
        
        self.reset_btn = QPushButton("Clear")
        self.reset_btn.setObjectName("ResetButton")
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.clicked.connect(self.reset_state) # <--- Calls the full clear now
        self.reset_btn.setEnabled(False)
        
        action_layout.addWidget(self.enhance_btn)
        action_layout.addWidget(self.reset_btn)
        main_layout.addWidget(actions_group)

    def _apply_styles(self):
        """Injects CSS-like styling into the UI components."""
        self.setStyleSheet("""
            QWidget { background-color: #F5F7FA; font-family: 'Segoe UI', sans-serif; }
            
            QGroupBox {
                font-weight: bold; border: 1px solid #E1E4E8; border-radius: 8px;
                margin-top: 10px; background-color: white; padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 15px; padding: 0 5px;
                color: #546E7A; font-size: 12px; font-weight: bold;
            }
            
            QPushButton#PrimaryButton {
                background-color: #2E7D32; color: white; border-radius: 8px;
                padding: 15px; font-size: 16px; font-weight: bold; border: none;
            }
            QPushButton#PrimaryButton:hover { background-color: #388E3C; }
            
            QPushButton#SecondaryButton {
                background-color: #1976D2; color: white; border-radius: 8px;
                padding: 15px; font-size: 16px; font-weight: bold; border: none;
            }
            QPushButton#SecondaryButton:hover { background-color: #2196F3; }
            
            QLabel#EmptyState {
                background-color: #EEF0F4; border: 3px dashed #B0BEC5;
                border-radius: 15px; color: #78909C; font-size: 18px; font-weight: bold;
            }
            
            QPushButton#ActionButton {
                background-color: #673AB7; color: white; padding: 12px;
                border-radius: 6px; font-weight: bold; font-size: 14px;
            }
            QPushButton#ActionButton:disabled { background-color: #D1C4E9; color: #9575CD; }

            QPushButton#ResetButton {
                background-color: #757575; color: white; padding: 12px;
                border-radius: 6px; font-weight: bold; font-size: 14px;
            }
            QPushButton#ResetButton:disabled { background-color: #E0E0E0; color: #9E9E9E; }

            QLabel#InfoLabel { color: #546E7A; font-size: 13px; font-weight: 600; margin-top: 5px; }

            QScrollBar:vertical {
                border: none;
                background: #E0E0E0; /* Light gray track */
                width: 14px;         /* Much wider */
                margin: 0px 0px 0px 0px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background: #90A4AE; /* Darker gray handle */
                min-height: 30px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical:hover {
                background: #78909C; /* Even darker on hover */
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px; /* Hides the tiny arrows */
            }

            QScrollBar:horizontal {
                border: none;
                background: #E0E0E0;
                height: 14px;
                margin: 0px 0px 0px 0px;
                border-radius: 7px;
            }
            QScrollBar::handle:horizontal {
                background: #90A4AE;
                min-width: 30px;
                border-radius: 7px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #78909C;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)

    def _upload_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Document", str(Path.home()), "Images (*.png *.jpg *.jpeg)")
        if file_path:
            img = cv2.imread(file_path)
            if img is not None:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                self._load_image_data(img_rgb, f"File: {Path(file_path).name}")

    def _capture_from_camera(self):
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened(): cap = cv2.VideoCapture(1)
            if not cap.isOpened(): raise RuntimeError("No camera found.")
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
        self.image_label.setStyleSheet("border: none; background-color: transparent;")
        self._display_current()
        self.image_loaded.emit(self.current_image)

    def _display_current(self):
        if self.current_image is None: return
        h, w, ch = self.current_image.shape
        bytes_per_line = ch * w
        qt_img = QImage(self.current_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img)
        if w > 1200: 
             pixmap = pixmap.scaledToWidth(1200, Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(pixmap)
        self.image_label.adjustSize()

    def _enhance_image(self):
        if self.current_image is not None:
            self.current_image = self.image_processor.enhance_for_ocr(self.current_image)
            self._display_current()
            self.info_label.setText(self.info_label.text() + " | Enhanced ✨")

    def _reset_image(self):
        """Resets the image to the original state."""
        if self.original_image is not None:
            self.current_image = self.original_image.copy()
            self._display_current()
            self.info_label.setText(self.info_label.text().split('|')[0].strip())
            
    def reset_state(self):
        """
        Completely clears the UI back to the startup state.
        """
        self.current_image = None
        self.original_image = None
        
        self.image_label.clear()
        self.image_label.setText("📄\n\nNo Document Loaded\n\nSelect a source above to begin")
        
        # Re-apply the 'Empty State' dashed border style
        self.image_label.setStyleSheet("""
            background-color: #EEF0F4; border: 3px dashed #B0BEC5;
            border-radius: 15px; color: #78909C; font-size: 18px; font-weight: bold;
        """)
        
        self.info_label.setText("Ready to scan.")
        self.enhance_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)
        logger.info("Scanner reset to empty state")