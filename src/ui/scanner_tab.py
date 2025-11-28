"""
src/ui/scanner_tab.py
Final Integration:
- Connects UI to Google Gemini 3 (via AIAssistant service).
- Handles threaded AI queries to prevent freezing.
- Displays Markdown-formatted AI responses.
"""
from pathlib import Path
import cv2
import numpy as np
from loguru import logger

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QGroupBox, QTextEdit, 
    QScrollArea, QFrame, QStackedWidget, QSizePolicy, QComboBox
)
from PySide6.QtCore import Qt, Signal, QThread, QObject

# Services
from services.ocr_service import OCRService
from services.analysis_service import AnalysisService
from services.ai_assistant import AIAssistant  # <--- NEW SERVICE
from utils.image_processing import ImageProcessor

# --- WORKER 1: OCR & TRANSLATION ---
class ProcessingWorker(QObject):
    # Returns: (TranslatedText, DocType, InsightsList, RawEnglishText)
    finished = Signal(str, str, list, str) 
    error = Signal(str)

    def __init__(self, ocr, analysis, image, target_lang):
        super().__init__()
        self.ocr = ocr
        self.analysis = analysis
        self.image = image
        self.target_lang = target_lang

    def run(self):
        try:
            # 1. OCR
            raw_text = self.ocr.extract_text(self.image, lang='eng')
            
            # 2. Detect Type
            doc_type = self.analysis.detect_document_type(raw_text)
            
            # 3. Translate
            translated_text = self.analysis.translate_content(raw_text, self.target_lang)
            
            # 4. Analyze (Get terms for the dropdown)
            insights = self.analysis.analyze_text(raw_text)
            
            # Pass everything back, including raw text for the AI context
            self.finished.emit(translated_text, doc_type, insights, raw_text)
        except Exception as e:
            self.error.emit(str(e))

# --- WORKER 2: AI QUERY (GEMINI) ---
class AIQueryWorker(QObject):
    finished = Signal(str)
    
    def __init__(self, ai_service, term, context, local_def, lang):
        super().__init__()
        self.ai = ai_service
        self.term = term
        self.context = context
        self.local_def = local_def
        self.lang = lang

    def run(self):
        # Calls the Google GenAI SDK
        response = self.ai.explain_term(self.term, self.local_def, self.context, self.lang)
        self.finished.emit(response)

# --- MAIN TAB CLASS ---
class ScannerTab(QWidget):
    def __init__(self):
        super().__init__()
        self.ocr_service = OCRService()
        self.analysis_service = AnalysisService()
        self.ai_assistant = AIAssistant() # <--- Initialize Gemini Client
        self.image_processor = ImageProcessor()
        
        # State Data
        self.raw_text_cache = ""
        self.found_insights_cache = []
        
        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)
        
        # === VIEW 1: UPLOAD ===
        self.view_upload = QWidget()
        upload_layout = QVBoxLayout(self.view_upload)
        upload_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_layout.setSpacing(20)
        
        lbl_welcome = QLabel("MediTranslate AI")
        lbl_welcome.setObjectName("TitleLabel")
        lbl_welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lang_select = QComboBox()
        self.lang_select.addItems(["Spanish", "Hindi"])
        self.lang_select.setFixedSize(300, 50)
        self.lang_select.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lang_select.setObjectName("LangSelect")
        
        btn_layout = QHBoxLayout()
        self.btn_upload = QPushButton("📂 Upload File")
        self.btn_upload.setFixedSize(200, 60)
        self.btn_upload.setObjectName("BigButton")
        self.btn_upload.clicked.connect(self._upload_image)
        
        self.btn_camera = QPushButton("📷 Use Camera")
        self.btn_camera.setFixedSize(200, 60)
        self.btn_camera.setObjectName("BigButton")
        self.btn_camera.clicked.connect(self._capture_camera)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_upload)
        btn_layout.addWidget(self.btn_camera)
        btn_layout.addStretch()
        
        upload_layout.addStretch()
        upload_layout.addWidget(lbl_welcome)
        upload_layout.addWidget(self.lang_select, alignment=Qt.AlignmentFlag.AlignCenter)
        upload_layout.addLayout(btn_layout)
        upload_layout.addStretch()
        
        # === VIEW 2: RESULTS ===
        self.view_results = QWidget()
        wrapper = QVBoxLayout(self.view_results)
        wrapper.setContentsMargins(20, 20, 20, 20)
        
        results_container = QWidget()
        results_layout = QHBoxLayout(results_container)
        results_layout.setSpacing(30)
        
        # --- LEFT: TRANSLATED DOC ---
        left_col = QVBoxLayout()
        self.lbl_res_title = QLabel("TRANSLATED DOCUMENT")
        self.lbl_res_title.setStyleSheet("font-weight: bold; color: #2E7D32;")
        
        self.text_editor = QTextEdit()
        self.text_editor.setPlaceholderText("Processing...")
        self.text_editor.setObjectName("Editor")
        self.text_editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        left_col.addWidget(self.lbl_res_title)
        left_col.addWidget(self.text_editor)
        
        # --- RIGHT: AI CARETAKER PANEL ---
        right_col = QVBoxLayout()
        lbl_ai_title = QLabel("🤖 AI MEDICAL GUIDE")
        lbl_ai_title.setStyleSheet("font-weight: bold; color: #1565C0;")
        
        # 1. Question Box
        question_box = QGroupBox("What confuses you?")
        question_box.setObjectName("AIBox")
        q_layout = QVBoxLayout(question_box)
        
        self.term_selector = QComboBox()
        self.term_selector.setPlaceholderText("Select a medical term...")
        self.term_selector.setObjectName("TermSelect")
        
        self.btn_explain = QPushButton("✨ Explain & Guide Me")
        self.btn_explain.setObjectName("ActionButton")
        self.btn_explain.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_explain.clicked.connect(self._ask_ai)
        
        q_layout.addWidget(self.term_selector)
        q_layout.addWidget(self.btn_explain)
        
        # 2. Answer Area (Displays Markdown)
        self.ai_response_area = QTextEdit()
        self.ai_response_area.setPlaceholderText("Select a term above to get a personalized explanation from Gemini AI...")
        self.ai_response_area.setReadOnly(True)
        self.ai_response_area.setObjectName("AIResponse")
        
        right_col.addWidget(lbl_ai_title)
        right_col.addWidget(question_box)
        right_col.addWidget(self.ai_response_area)
        
        results_layout.addLayout(left_col, stretch=60)
        results_layout.addLayout(right_col, stretch=40)
        
        wrapper.addWidget(results_container, stretch=1)
        
        # Bottom: Reset
        self.btn_reset = QPushButton("❌ Scan New Document")
        self.btn_reset.setObjectName("ResetButton")
        self.btn_reset.clicked.connect(self._reset_app)
        wrapper.addWidget(self.btn_reset, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.stack.addWidget(self.view_upload)
        self.stack.addWidget(self.view_results)

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #F5F7FA; font-family: 'Segoe UI', sans-serif; }
            QLabel#TitleLabel { font-size: 32px; font-weight: bold; color: #263238; }
            
            QComboBox { border: 1px solid #B0BEC5; border-radius: 6px; padding: 8px; background: white; font-size: 14px; }
            
            QPushButton#BigButton {
                background-color: white; border: 2px solid #CFD8DC; border-radius: 12px; font-weight: bold;
            }
            QPushButton#BigButton:hover { border-color: #2196F3; color: #1976D2; }
            
            QTextEdit#Editor {
                border: none; border-radius: 12px; background-color: white; padding: 20px;
                font-family: 'Noto Sans', 'Noto Sans Devanagari', sans-serif; font-size: 14px;
            }
            
            /* AI Panel Styles */
            QGroupBox#AIBox {
                font-weight: bold; border: 1px solid #CFD8DC; border-radius: 8px; 
                background-color: white; padding-top: 20px; margin-top: 10px;
            }
            
            QPushButton#ActionButton {
                background-color: #673AB7; color: white; border-radius: 6px; padding: 10px; font-weight: bold; margin-top: 5px; border: none;
            }
            QPushButton#ActionButton:hover { background-color: #7E57C2; }
            
            QTextEdit#AIResponse {
                border: none; background-color: #F3E5F5; border-radius: 12px;
                padding: 15px; color: #4A148C; font-family: 'Noto Sans', 'Noto Sans Devanagari', sans-serif;
                font-size: 14px; margin-top: 10px;
            }
            
            QPushButton#ResetButton {
                background-color: #FFEBEE; color: #D32F2F; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold;
            }
        """)

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
        except Exception: pass

    def _start_processing(self, image):
        target = self.lang_select.currentText()
        self.stack.setCurrentIndex(1)
        self.text_editor.setText("⏳ Analyzing document...")
        self.text_editor.setEnabled(False)
        self.term_selector.clear()
        self.ai_response_area.clear()
        
        self.thread = QThread()
        self.worker = ProcessingWorker(self.ocr_service, self.analysis_service, image, target)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_process_finished)
        self.worker.error.connect(self._on_process_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def _on_process_finished(self, text, doc_type, insights, raw_text):
        self.text_editor.setEnabled(True)
        self.text_editor.setText(text)
        self.raw_text_cache = raw_text
        self.found_insights_cache = insights
        
        # Populate Dropdown with found medical terms
        seen = set()
        for item in insights:
            if item['title'] not in seen:
                self.term_selector.addItem(item['title'])
                seen.add(item['title'])
                
        if self.term_selector.count() == 0:
            self.term_selector.addItem("No specific terms found")
            self.term_selector.setEnabled(False)
            self.btn_explain.setEnabled(False)
        else:
            self.term_selector.setEnabled(True)
            self.btn_explain.setEnabled(True)

    def _on_process_error(self, err):
        self.text_editor.setText(f"Error: {err}")
        self.text_editor.setEnabled(True)

    def _ask_ai(self):
        """Triggers the Gemini Thread."""
        term = self.term_selector.currentText()
        target_lang = self.lang_select.currentText()
        
        # Find the local definition to help Gemini context
        local_def = "Medical term found in document."
        for item in self.found_insights_cache:
            if item['title'] == term:
                local_def = item['desc']
                break
        
        self.ai_response_area.setMarkdown(f"**⏳ Asking AI Assistant about '{term}'...**")
        self.btn_explain.setEnabled(False)
        
        self.ai_thread = QThread()
        self.ai_worker = AIQueryWorker(self.ai_assistant, term, self.raw_text_cache, local_def, target_lang)
        self.ai_worker.moveToThread(self.ai_thread)
        self.ai_thread.started.connect(self.ai_worker.run)
        self.ai_worker.finished.connect(self._on_ai_finished)
        self.ai_worker.finished.connect(self.ai_thread.quit)
        self.ai_worker.finished.connect(self.ai_worker.deleteLater)
        self.ai_thread.finished.connect(self.ai_thread.deleteLater)
        self.ai_thread.start()

    def _on_ai_finished(self, response):
        # Renders Markdown properly (Bold, bullet points)
        self.ai_response_area.setMarkdown(response)
        self.btn_explain.setEnabled(True)

    def _reset_app(self):
        self.stack.setCurrentIndex(0)
        self.text_editor.clear()