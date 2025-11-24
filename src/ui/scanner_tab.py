"""
src/ui/scanner_tab.py
Handles document upload, display, and OCR extraction with background threading.
"""
from pathlib import Path
import cv2
import numpy as np
from loguru import logger
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QGroupBox, QScrollArea, QFrame,
    QSplitter, QTextEdit, QComboBox
)
# --- CRITICAL IMPORTS FOR THREADING ---
from PySide6.QtCore import Qt, Signal, QObject, QThread
from PySide6.QtGui import QPixmap, QImage

# Custom Imports
from utils.image_processing import ImageProcessor
from services.ocr_service import OCRService

# --- WORKER CLASS (Runs in Background) ---
class OCRWorker(QObject):
    """
    Runs OCR in a background thread to prevent UI freezing.
    """
    finished = Signal(str)  # Signal to send text back to UI
    error = Signal(str)     # Signal to send errors back

    def __init__(self, service, image, lang_code):
        super().__init__()
        self.service = service
        self.image = image
        self.lang_code = lang_code

    def run(self):
        """The heavy lifting happens here."""
        try:
            # This blocking call now runs in the background
            text = self.service.extract_text(self.image, lang=self.lang_code)
            self.finished.emit(text)
        except Exception as e:
            self.error.emit(str(e))

# --- MAIN TAB CLASS ---
class ScannerTab(QWidget):
    
    image_loaded = Signal(np.ndarray)
    
    def __init__(self):
        super().__init__()
        
        # Services
        self.image_processor = ImageProcessor()
        self.ocr_service = OCRService()
        
        # State
        self.current_image = None
        self.original_image = None
        self.ocr_thread = None # Keep reference to thread
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # --- TOP: Controls (Step 1) ---
        controls_group = QGroupBox("STEP 1: SOURCE")
        controls_group.setObjectName("HeaderGroup")
        controls_layout = QHBoxLayout(controls_group)
        
        self.upload_btn = QPushButton("📂 Upload File")
        self.upload_btn.setObjectName("PrimaryButton")
        self.upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.upload_btn.clicked.connect(self._upload_image)
        
        self.camera_btn = QPushButton("📷 Camera")
        self.camera_btn.setObjectName("SecondaryButton")
        self.camera_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.camera_btn.clicked.connect(self._capture_from_camera)
        
        controls_layout.addWidget(self.upload_btn)
        controls_layout.addWidget(self.camera_btn)
        main_layout.addWidget(controls_group)
        
        # --- MIDDLE: Split View (Image | Text) ---
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # LEFT: Image Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        self.image_label = QLabel("📄\n\nNo Document\nLoaded")
        self.image_label.setObjectName("EmptyState")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self.image_label)
        
        # RIGHT: Text Area
        self.text_area = QTextEdit()
        self.text_area.setPlaceholderText("Extracted text will appear here...")
        self.text_area.setReadOnly(False)
        self.text_area.setObjectName("ResultText")
        
        # Add to splitter
        self.splitter.addWidget(self.scroll_area)
        self.splitter.addWidget(self.text_area)
        self.splitter.setStretchFactor(0, 60)
        self.splitter.setStretchFactor(1, 40)
        
        main_layout.addWidget(self.splitter, stretch=1)
        
        # --- BOTTOM: Actions (Step 2 & 3) ---
        actions_layout = QHBoxLayout()
        
        # Group 2: Enhance
        enhance_group = QGroupBox("STEP 2: CLEAN")
        enhance_group.setObjectName("HeaderGroup")
        e_layout = QHBoxLayout(enhance_group)
        
        self.enhance_btn = QPushButton("✨ Auto-Enhance")
        self.enhance_btn.setObjectName("ActionButton")
        self.enhance_btn.clicked.connect(self._enhance_image)
        self.enhance_btn.setEnabled(False)
        e_layout.addWidget(self.enhance_btn)
        
        # Group 3: OCR
        ocr_group = QGroupBox("STEP 3: READ")
        ocr_group.setObjectName("HeaderGroup")
        o_layout = QHBoxLayout(ocr_group)
        
        # Language Selector
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English (eng)", "Spanish (spa)", "Hindi (hin)"])
        self.lang_combo.setMinimumWidth(150)
        self.lang_combo.setMinimumHeight(40)
        
        self.ocr_btn = QPushButton("🔍 Extract Text")
        self.ocr_btn.setObjectName("PrimaryButton")
        self.ocr_btn.clicked.connect(self._run_ocr)
        self.ocr_btn.setEnabled(False)
        
        o_layout.addWidget(self.lang_combo)
        o_layout.addWidget(self.ocr_btn)
        
        actions_layout.addWidget(enhance_group)
        actions_layout.addWidget(ocr_group)
        
        # Clear Button
        self.reset_btn = QPushButton("❌")
        self.reset_btn.setToolTip("Clear All")
        self.reset_btn.setFixedSize(50, 50)
        self.reset_btn.setObjectName("ResetButton")
        self.reset_btn.clicked.connect(self.reset_state)
        self.reset_btn.setEnabled(False)
        
        actions_layout.addWidget(self.reset_btn)
        
        main_layout.addLayout(actions_layout)

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #F5F7FA; font-family: 'Noto Sans', 'Segoe UI', sans-serif; }
            
            QGroupBox {
                font-weight: bold; border: 1px solid #E1E4E8; border-radius: 8px;
                margin-top: 10px; background-color: white; padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 10px; padding: 0 5px;
                color: #546E7A; font-size: 11px; font-weight: bold;
            }
            
            QPushButton { border-radius: 6px; font-weight: bold; font-size: 14px; padding: 10px; }
            QPushButton#PrimaryButton { background-color: #2E7D32; color: white; border: none; }
            QPushButton#PrimaryButton:hover { background-color: #388E3C; }
            QPushButton#SecondaryButton { background-color: #1976D2; color: white; border: none; }
            QPushButton#SecondaryButton:hover { background-color: #2196F3; }
            QPushButton#ActionButton { background-color: #673AB7; color: white; border: none; }
            QPushButton#ActionButton:hover { background-color: #7E57C2; }
            QPushButton#ResetButton { background-color: #D32F2F; color: white; border: none; }
            QPushButton#ResetButton:hover { background-color: #E53935; }
            QPushButton:disabled { background-color: #E0E0E0; color: #9E9E9E; }
            
            QTextEdit#ResultText {
                border: 1px solid #B0BEC5; border-radius: 8px;
                background-color: white; padding: 10px; 
                /* FIX: Added 'Noto Sans Devanagari' so Qt knows where to find Script 11 */
                /* Put Devanagari FIRST so Qt uses it for drawing */
                font-family: 'Noto Sans Devanagari', 'Noto Sans', sans-serif; 
                font-size: 14px; color: #263238;
            }
            
            QLabel#EmptyState {
                background-color: #EEF0F4; border: 2px dashed #B0BEC5;
                border-radius: 10px; color: #78909C; font-size: 16px; font-weight: bold;
            }
            
            QComboBox {
                border: 1px solid #B0BEC5; border-radius: 6px; padding: 5px;
                background: white; font-size: 13px;
            }

            /* Scrollbar Styling */
            QScrollBar:vertical {
                border: none; background: #E0E0E0; width: 14px; margin: 0px; border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background: #90A4AE; min-height: 30px; border-radius: 7px;
            }
        """)

    # --- LOGIC HANDLERS ---
    
    def _upload_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Doc", str(Path.home()), "Images (*.png *.jpg *.jpeg)")
        if file_path:
            img = cv2.imread(file_path)
            if img is not None:
                self._load_image_data(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    def _capture_from_camera(self):
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened(): cap = cv2.VideoCapture(1)
            if not cap.isOpened(): raise RuntimeError("No camera found")
            for _ in range(5): cap.read()
            ret, frame = cap.read()
            cap.release()
            if ret:
                self._load_image_data(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        except Exception as e:
            QMessageBox.warning(self, "Camera Error", str(e))

    def _load_image_data(self, image_rgb):
        self.original_image = image_rgb.copy()
        self.current_image = image_rgb.copy()
        
        self.image_label.setStyleSheet("border: none; background-color: transparent;")
        self.text_area.clear()
        
        self.enhance_btn.setEnabled(True)
        self.ocr_btn.setEnabled(True)
        self.reset_btn.setEnabled(True)
        
        self._display_current()

    def _display_current(self):
        if self.current_image is None: return
        h, w, ch = self.current_image.shape
        bytes_per_line = ch * w
        qt_img = QImage(self.current_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img)
        
        if w > self.image_label.width():
             pixmap = pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
             
        self.image_label.setPixmap(pixmap)

    def _enhance_image(self):
        if self.current_image is not None:
            self.current_image = self.image_processor.enhance_for_ocr(self.current_image)
            self._display_current()

    def _run_ocr(self):
        """Step 3: Trigger OCR in Background Thread"""
        if self.current_image is None: return
        
        self.text_area.setPlaceholderText("Reading document... please wait...")
        self.ocr_btn.setEnabled(False)
        self.ocr_btn.setText("⏳ Reading...")
        
        # 1. Get Config
        lang_map = {
            "English (eng)": "eng",
            "Spanish (spa)": "spa", 
            "Hindi (hin)": "hin+eng"
        }
        lang_code = lang_map.get(self.lang_combo.currentText(), "eng")
        
        # 2. Setup Thread & Worker
        self.ocr_thread = QThread()
        self.worker = OCRWorker(self.ocr_service, self.current_image, lang_code)
        self.worker.moveToThread(self.ocr_thread)
        
        # 3. Connect Signals
        self.ocr_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_ocr_finished)
        self.worker.error.connect(self._on_ocr_error)
        
        # Cleanup
        self.worker.finished.connect(self.ocr_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.ocr_thread.finished.connect(self.ocr_thread.deleteLater)
        
        # 4. Start
        self.ocr_thread.start()

    def _on_ocr_finished(self, text):
        """Called when background thread finishes successfully"""
        self.text_area.setText(text)
        self._reset_ocr_ui()

    def _on_ocr_error(self, error_msg):
        """Called if background thread crashes"""
        self.text_area.setText(f"❌ Error: {error_msg}\n\nCheck logs or language data.")
        self._reset_ocr_ui()

    def _reset_ocr_ui(self):
        """Helper to reset button state"""
        self.ocr_btn.setEnabled(True)
        self.ocr_btn.setText("🔍 Extract Text")

    def reset_state(self):
        self.current_image = None
        self.original_image = None
        self.image_label.clear()
        self.image_label.setText("📄\n\nNo Document\nLoaded")
        self.text_area.clear()
        
        self.image_label.setStyleSheet("""
            background-color: #EEF0F4; border: 2px dashed #B0BEC5;
            border-radius: 10px; color: #78909C; font-size: 16px; font-weight: bold;
        """)
        
        self.enhance_btn.setEnabled(False)
        self.ocr_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)