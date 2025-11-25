"""
src/ui/scanner_tab.py
The "Intelligent Assistant" UI Layout.
FIXED: Added robust container widgets to prevent layout collapse.
"""
from pathlib import Path
import cv2
import numpy as np
from loguru import logger

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QGroupBox, QTextEdit, 
    QScrollArea, QFrame, QStackedWidget, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QThread, QObject

# Services
from services.ocr_service import OCRService
from services.analysis_service import AnalysisService
from utils.image_processing import ImageProcessor

# --- WORKER THREAD ---
class ProcessingWorker(QObject):
    finished = Signal(str, list)
    error = Signal(str)

    def __init__(self, ocr_service, analysis_service, image):
        super().__init__()
        self.ocr = ocr_service
        self.analysis = analysis_service
        self.image = image

    def run(self):
        try:
            # 1. OCR
            raw_text = self.ocr.extract_text(self.image)
            # 2. Translate (Mock)
            translated_text = self.analysis.mock_translate(raw_text, "Spanish")
            # 3. Insights
            insights = self.analysis.analyze_text(raw_text)
            
            self.finished.emit(translated_text, insights)
        except Exception as e:
            self.error.emit(str(e))

# --- AI CARD WIDGET ---
class InsightCard(QFrame):
    def __init__(self, title, desc, card_type="info"):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName(f"Card_{card_type}")
        
        # Make sure cards have a minimum height so they don't squash
        self.setMinimumHeight(80)
        
        layout = QVBoxLayout(self)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333; border: none;")
        layout.addWidget(lbl_title)
        
        lbl_desc = QLabel(desc)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #555; font-size: 12px; border: none;")
        layout.addWidget(lbl_desc)

# --- MAIN TAB CLASS ---
class ScannerTab(QWidget):
    def __init__(self):
        super().__init__()
        self.ocr_service = OCRService()
        self.analysis_service = AnalysisService()
        self.image_processor = ImageProcessor()
        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)
        
        # ==========================
        # VIEW 1: UPLOAD SCREEN
        # ==========================
        self.view_upload = QWidget()
        upload_layout = QVBoxLayout(self.view_upload)
        upload_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_layout.setSpacing(20)
        
        lbl_welcome = QLabel("MediTranslate AI")
        lbl_welcome.setObjectName("TitleLabel")
        lbl_welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_sub = QLabel("Upload a medical document to get\ntranslation and simplified explanations.")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setStyleSheet("color: #666; font-size: 16px;")
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)
        
        self.btn_upload = QPushButton("📂 Upload File")
        self.btn_upload.setFixedSize(200, 60)
        self.btn_upload.setObjectName("BigButton")
        self.btn_upload.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_upload.clicked.connect(self._upload_image)
        
        self.btn_camera = QPushButton("📷 Use Camera")
        self.btn_camera.setFixedSize(200, 60)
        self.btn_camera.setObjectName("BigButton")
        self.btn_camera.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_camera.clicked.connect(self._capture_camera)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_upload)
        btn_layout.addWidget(self.btn_camera)
        btn_layout.addStretch()
        
        upload_layout.addStretch()
        upload_layout.addWidget(lbl_welcome)
        upload_layout.addWidget(lbl_sub)
        upload_layout.addLayout(btn_layout)
        upload_layout.addStretch()
        
        # ==========================
        # VIEW 2: RESULTS SCREEN
        # ==========================
        self.view_results = QWidget()
        # The main wrapper layout
        wrapper = QVBoxLayout(self.view_results)
        wrapper.setContentsMargins(20, 20, 20, 20)
        wrapper.setSpacing(20)

        # --- FIX: Container for the Columns ---
        # We wrap the columns in a widget to force them to render
        results_container = QWidget()
        results_layout = QHBoxLayout(results_container) # Apply layout to this widget
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.setSpacing(20)
        
        # LEFT COLUMN (Text)
        left_col = QVBoxLayout()
        lbl_res_title = QLabel("TRANSLATED DOCUMENT")
        lbl_res_title.setStyleSheet("font-weight: bold; color: #2E7D32; letter-spacing: 1px;")
        
        self.text_editor = QTextEdit()
        self.text_editor.setPlaceholderText("Processing...")
        self.text_editor.setObjectName("Editor")
        # FORCE SIZE: Make sure editor expands
        self.text_editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        left_col.addWidget(lbl_res_title)
        left_col.addWidget(self.text_editor)
        
        # RIGHT COLUMN (AI Cards)
        right_col = QVBoxLayout()
        lbl_ai_title = QLabel("AI MEDICAL INSIGHTS")
        lbl_ai_title.setStyleSheet("font-weight: bold; color: #1565C0; letter-spacing: 1px;")
        
        self.ai_scroll = QScrollArea()
        self.ai_scroll.setWidgetResizable(True)
        self.ai_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.ai_scroll.setStyleSheet("background: transparent;")
        # FORCE SIZE
        self.ai_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.ai_container = QWidget()
        self.ai_layout = QVBoxLayout(self.ai_container)
        self.ai_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.ai_layout.setSpacing(15)
        
        self.ai_scroll.setWidget(self.ai_container)
        
        right_col.addWidget(lbl_ai_title)
        right_col.addWidget(self.ai_scroll)
        
        # Add columns to container
        results_layout.addLayout(left_col, stretch=60)
        results_layout.addLayout(right_col, stretch=40)
        
        # Add Container to Wrapper (This forces it to show up)
        wrapper.addWidget(results_container, stretch=1)
        
        # Reset Button (Bottom)
        self.btn_reset = QPushButton("❌ Scan New Document")
        self.btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset.setObjectName("ResetButton")
        self.btn_reset.clicked.connect(self._reset_app)
        
        wrapper.addWidget(self.btn_reset, alignment=Qt.AlignmentFlag.AlignRight)
        
        # Add views to stack
        self.stack.addWidget(self.view_upload)
        self.stack.addWidget(self.view_results)

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #F5F7FA; font-family: 'Segoe UI', sans-serif; }
            
            QLabel#TitleLabel { font-size: 32px; font-weight: bold; color: #263238; }
            
            QPushButton#BigButton {
                background-color: white; border: 2px solid #CFD8DC;
                border-radius: 12px; font-size: 16px; font-weight: bold; color: #455A64;
            }
            QPushButton#BigButton:hover {
                background-color: #E3F2FD; border-color: #2196F3; color: #1976D2;
            }
            
            QTextEdit#Editor {
                border: none; border-radius: 12px; background-color: white;
                padding: 20px; font-size: 16px; line-height: 1.5; color: #37474F;
                font-family: 'Noto Sans', 'Noto Sans Devanagari', sans-serif;
            }
            
            QPushButton#ResetButton {
                background-color: #FFEBEE; color: #D32F2F; border: none;
                padding: 12px 24px; border-radius: 6px; font-weight: bold;
            }
            QPushButton#ResetButton:hover { background-color: #FFCDD2; }
            
            QFrame#Card_info {
                background-color: white; border-left: 4px solid #2196F3;
                border-radius: 4px; padding: 10px;
            }
            QFrame#Card_warning {
                background-color: #FFF8E1; border-left: 4px solid #FFC107;
                border-radius: 4px; padding: 10px;
            }
            QFrame#Card_drug {
                background-color: #E8F5E9; border-left: 4px solid #4CAF50;
                border-radius: 4px; padding: 10px;
            }
        """)

    # --- LOGIC ---
    def _upload_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Doc", str(Path.home()), "Images (*.png *.jpg)")
        if path:
            img = cv2.imread(path)
            if img is not None:
                self._start_processing(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    def _capture_camera(self):
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened(): cap = cv2.VideoCapture(1)
            for _ in range(10): cap.read()
            ret, frame = cap.read()
            cap.release()
            if ret:
                self._start_processing(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _start_processing(self, image):
        self.stack.setCurrentIndex(1)
        self.text_editor.setText("⏳ Scanning and Analyzing document...")
        self.text_editor.setEnabled(False)
        
        # Clear old AI cards
        while self.ai_layout.count():
            child = self.ai_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        self.thread = QThread()
        self.worker = ProcessingWorker(self.ocr_service, self.analysis_service, image)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_process_finished)
        self.worker.error.connect(self._on_process_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def _on_process_finished(self, text, insights):
        self.text_editor.setEnabled(True)
        self.text_editor.setText(text)
        
        if not insights:
            lbl = QLabel("No specific medical terms detected.")
            lbl.setStyleSheet("color: #999; font-style: italic; border: none;")
            self.ai_layout.addWidget(lbl)
        
        for data in insights:
            card = InsightCard(data['title'], data['desc'], data['type'])
            self.ai_layout.addWidget(card)
        self.ai_layout.addStretch()

    def _on_process_error(self, err):
        self.text_editor.setText(f"❌ Error: {err}")
        self.text_editor.setEnabled(True)

    def _reset_app(self):
        self.stack.setCurrentIndex(0)
        self.text_editor.clear()