"""
src/ui/scanner_tab.py
Final Production Version.
- UI: Displays Target Language Only (Clean for patient).
- Data: Preserves English + Target for Bilingual PDF Export.
- AI: Connects to Gemini for empathetic guidance.
- Fonts: Handles Hindi rendering correctly.
"""
from pathlib import Path
import cv2
import numpy as np
from loguru import logger
from pdf2image import convert_from_path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QGroupBox, QTextEdit, 
    QScrollArea, QFrame, QStackedWidget, QSizePolicy, QComboBox
)
from PySide6.QtCore import Qt, Signal, QThread, QObject
from PySide6.QtGui import QFont

# Services
from services.ocr_service import OCRService
from services.analysis_service import AnalysisService
from services.ai_assistant import AIAssistant
from services.pdf_service import PDFService
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
            # 1. OCR (Read English Text)
            raw_text = self.ocr.extract_text(self.image, lang='eng')
            
            # 2. Detect Type
            doc_type = self.analysis.detect_document_type(raw_text)
            
            # 3. Translate Document
            translated_text = self.analysis.translate_content(raw_text, self.target_lang)
            
            # 4. Analyze (Get English Insights first)
            raw_insights = self.analysis.analyze_text(raw_text)
            
            # 5. PREPARE BILINGUAL DATA
            # We add 'trans_title' and 'trans_desc' to every item for the PDF & UI
            final_insights = []
            seen = set()
            
            for item in raw_insights:
                orig_title = item['title']
                if orig_title in seen: continue
                seen.add(orig_title)
                
                # Translate Title & Description using MarianMT
                item['trans_title'] = self.analysis.translate_content(orig_title, self.target_lang)
                item['trans_desc'] = self.analysis.translate_content(item['desc'], self.target_lang)
                
                final_insights.append(item)
            
            self.finished.emit(translated_text, doc_type, final_insights, raw_text)
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
        response = self.ai.explain_term(self.term, self.local_def, self.context, self.lang)
        self.finished.emit(response)

# --- UI COMPONENT: INSIGHT CARD ---
class InsightCard(QFrame):
    def __init__(self, title, desc, card_type="info"):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName(f"Card_{card_type}")
        self.setMinimumHeight(80)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title (Bold)
        lbl_title = QLabel(title)
        lbl_title.setWordWrap(True)
        # We assume the parent will set the correct font family (Hindi/English)
        lbl_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333; border: none;")
        layout.addWidget(lbl_title)
        
        # Description
        lbl_desc = QLabel(desc)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #555; font-size: 12px; border: none;")
        layout.addWidget(lbl_desc)

# --- MAIN SCREEN LOGIC ---
class ScannerTab(QWidget):
    def __init__(self):
        super().__init__()
        self.ocr_service = OCRService()
        self.analysis_service = AnalysisService()
        self.ai_assistant = AIAssistant()
        self.pdf_service = PDFService()
        self.image_processor = ImageProcessor()
        
        # State Data
        self.raw_text_cache = ""
        self.found_insights_cache = []
        self.last_result = {} 
        
        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)
        
        # === VIEW 1: UPLOAD SCREEN ===
        self.view_upload = QWidget()
        upload_layout = QVBoxLayout(self.view_upload)
        upload_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_layout.setSpacing(20)
        
        lbl_welcome = QLabel("MediTranslate AI")
        lbl_welcome.setObjectName("TitleLabel")
        lbl_welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_sub = QLabel("Select language and upload document.")
        lbl_sub.setStyleSheet("color: #666; font-size: 16px;")
        
        self.lang_select = QComboBox()
        self.lang_select.addItems(["Spanish", "Hindi"])
        self.lang_select.setFixedSize(300, 50)
        self.lang_select.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lang_select.setObjectName("LangSelect")
        
        btn_layout = QHBoxLayout()
        self.btn_upload = QPushButton("📂 Upload File")
        self.btn_upload.setFixedSize(200, 60)
        self.btn_upload.setObjectName("BigButton")
        self.btn_upload.clicked.connect(self._upload_file)
        
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
        upload_layout.addWidget(lbl_sub)
        upload_layout.addWidget(self.lang_select, alignment=Qt.AlignmentFlag.AlignCenter)
        upload_layout.addLayout(btn_layout)
        upload_layout.addStretch()
        
        # === VIEW 2: RESULTS SCREEN ===
        self.view_results = QWidget()
        wrapper = QVBoxLayout(self.view_results)
        wrapper.setContentsMargins(20, 20, 20, 20)
        
        results_container = QWidget()
        results_layout = QHBoxLayout(results_container)
        results_layout.setSpacing(30)
        
        # --- LEFT: TRANSLATED DOCUMENT ---
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
        
        # 1. Interactive Question Box
        question_box = QGroupBox("What confuses you?")
        question_box.setObjectName("AIBox")
        q_layout = QVBoxLayout(question_box)
        
        self.term_selector = QComboBox()
        self.term_selector.setPlaceholderText("Select a term...")
        self.term_selector.setObjectName("TermSelect")
        
        self.btn_explain = QPushButton("✨ Explain & Guide Me")
        self.btn_explain.setObjectName("ActionButton")
        self.btn_explain.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_explain.clicked.connect(self._ask_ai)
        
        q_layout.addWidget(self.term_selector)
        q_layout.addWidget(self.btn_explain)
        
        # 2. Answer Area
        self.ai_response_area = QTextEdit()
        self.ai_response_area.setPlaceholderText("Select a term above to get a personalized explanation...")
        self.ai_response_area.setReadOnly(True)
        self.ai_response_area.setObjectName("AIResponse")
        
        # 3. Static Cards List
        self.ai_scroll = QScrollArea()
        self.ai_scroll.setWidgetResizable(True)
        self.ai_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.ai_scroll.setStyleSheet("background: transparent;")
        
        self.ai_container = QWidget()
        self.ai_layout = QVBoxLayout(self.ai_container)
        self.ai_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.ai_layout.setSpacing(10)
        self.ai_scroll.setWidget(self.ai_container)
        
        right_col.addWidget(lbl_ai_title)
        right_col.addWidget(question_box)
        right_col.addWidget(self.ai_response_area)
        right_col.addWidget(self.ai_scroll) # Show cards below chat
        
        # Layout Weights
        results_layout.addLayout(left_col, stretch=55)
        results_layout.addLayout(right_col, stretch=45)
        wrapper.addWidget(results_container, stretch=1)
        
        # Bottom Buttons
        bottom_row = QHBoxLayout()
        self.btn_reset = QPushButton("❌ Scan New")
        self.btn_reset.setObjectName("ResetButton")
        self.btn_reset.clicked.connect(self.reset_state)
        
        self.btn_export = QPushButton("📥 Export Bilingual PDF")
        self.btn_export.setObjectName("ExportButton")
        self.btn_export.clicked.connect(self._export_pdf)
        self.btn_export.setEnabled(False)
        
        bottom_row.addWidget(self.btn_reset)
        bottom_row.addStretch()
        bottom_row.addWidget(self.btn_export)
        
        wrapper.addLayout(bottom_row)
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
            
            /* Text Editors need explicit font fallback for Hindi */
            QTextEdit#Editor, QTextEdit#AIResponse {
                border: none; border-radius: 12px; background-color: white; padding: 20px;
                font-family: 'Noto Sans Devanagari', 'Noto Sans', sans-serif; font-size: 14px;
            }
            
            QGroupBox#AIBox {
                font-weight: bold; border: 1px solid #CFD8DC; border-radius: 8px; background-color: white; padding-top: 20px;
            }
            QPushButton#ActionButton {
                background-color: #673AB7; color: white; border-radius: 6px; padding: 10px; font-weight: bold; border: none;
            }
            QPushButton#ActionButton:hover { background-color: #7E57C2; }
            
            QTextEdit#AIResponse {
                border: none; background-color: #F3E5F5; border-radius: 12px;
                padding: 15px; color: #4A148C; margin-top: 10px; min-height: 150px;
            }
            
            QPushButton#ResetButton {
                background-color: #FFEBEE; color: #D32F2F; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold;
            }
            QPushButton#ExportButton {
                background-color: #2E7D32; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold;
            }
            
            /* Insight Cards */
            QFrame#Card_info { background-color: white; border-left: 4px solid #2196F3; border-radius: 4px; }
            QFrame#Card_warning { background-color: white; border-left: 4px solid #FFC107; border-radius: 4px; }
            QFrame#Card_drug { background-color: white; border-left: 4px solid #4CAF50; border-radius: 4px; }
        """)

    def _upload_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Doc", str(Path.home()), "Documents (*.png *.jpg *.pdf)")
        if path:
            if path.lower().endswith('.pdf'):
                self._process_pdf(path)
            else:
                img = cv2.imread(path)
                if img is not None: self._start_processing(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    def _process_pdf(self, path):
        try:
            images = convert_from_path(path, first_page=1, last_page=1)
            if images: self._start_processing(np.array(images[0]))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"PDF Error: {e}")

    def _capture_camera(self):
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened(): cap = cv2.VideoCapture(1)
            for _ in range(10): cap.read()
            ret, frame = cap.read()
            cap.release()
            if ret: self._start_processing(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        except Exception: pass

    def _start_processing(self, image):
        target = self.lang_select.currentText()
        self.stack.setCurrentIndex(1)
        self.text_editor.setText(f"⏳ Processing...")
        self.term_selector.clear()
        self.ai_response_area.clear()
        self.btn_export.setEnabled(False)
        
        # Clear old cards
        while self.ai_layout.count():
            child = self.ai_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        
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
        self.text_editor.setText(text)
        
        # FONT FIX: Determine correct font based on Language
        current_lang = self.lang_select.currentText()
        if "Hindi" in current_lang:
            font = QFont("Noto Sans Devanagari", 14)
        else:
            font = QFont("Segoe UI", 14)
            
        self.text_editor.setFont(font)
        self.ai_response_area.setFont(font)

        self.raw_text_cache = raw_text
        self.found_insights_cache = insights
        self.btn_export.setEnabled(True)
        
        # Store for PDF (Contains both English & Trans keys)
        self.last_result = {
            "original_text": raw_text,
            "translated_text": text,
            "insights": insights,
            "doc_type": doc_type,
            "lang": current_lang
        }
        
        # Populate Sidebar (TARGET LANGUAGE ONLY)
        seen = set()
        for item in insights:
            # Use 'trans_title' for display
            display_title = item.get('trans_title', item['title'])
            display_desc = item.get('trans_desc', item['desc'])
            
            # 1. Dropdown
            if display_title not in seen:
                self.term_selector.addItem(display_title)
                seen.add(display_title)
            
            # 2. Static Cards (Show Trans only)
            card = InsightCard(display_title, display_desc, item['type'])
            # We must apply the font to the card labels manually
            for child in card.findChildren(QLabel):
                child.setFont(font)
                
            self.ai_layout.addWidget(card)
        
        if not insights:
            self.ai_layout.addWidget(QLabel("No specific terms found."))
        
        self.ai_layout.addStretch()
        
        enable_ai = self.term_selector.count() > 0
        self.term_selector.setEnabled(enable_ai)
        self.btn_explain.setEnabled(enable_ai)

    def _on_process_error(self, err):
        self.text_editor.setText(f"Error: {err}")

    def _ask_ai(self):
        term = self.term_selector.currentText()
        target = self.lang_select.currentText()
        local_def = "No local definition"
        
        # Match using translated title
        for item in self.found_insights_cache:
            if item.get('trans_title') == term:
                local_def = item['trans_desc']
                break
        
        self.ai_response_area.setMarkdown(f"**⏳ Asking AI about '{term}'...**")
        self.btn_explain.setEnabled(False)
        
        self.ai_thread = QThread()
        self.ai_worker = AIQueryWorker(self.ai_assistant, term, self.raw_text_cache, local_def, target)
        self.ai_worker.moveToThread(self.ai_thread)
        self.ai_thread.started.connect(self.ai_worker.run)
        self.ai_worker.finished.connect(self._on_ai_finished)
        self.ai_worker.finished.connect(self.ai_thread.quit)
        self.ai_worker.finished.connect(self.ai_worker.deleteLater)
        self.ai_thread.finished.connect(self.ai_thread.deleteLater)
        self.ai_thread.start()

    def _on_ai_finished(self, response):
        self.ai_response_area.setMarkdown(response)
        self.btn_explain.setEnabled(True)

    def _export_pdf(self):
        try:
            # Default filename
            default_name = f"MediTranslate_Report_{self.last_result.get('lang', 'Eng')}.pdf"
            path, _ = QFileDialog.getSaveFileName(self, "Save PDF", str(Path.home() / default_name), "PDF (*.pdf)")
            
            if path:
                # Check if file is writeable
                if Path(path).exists():
                    try:
                        # Try to open for exclusive write access to test lock
                        with open(path, 'a'): pass
                    except IOError:
                        QMessageBox.warning(self, "File Locked", 
                            f"Could not save to '{Path(path).name}'.\n\nIs it open in another program?\nPlease close it and try again.")
                        return

                self.pdf_service.generate_report(
                    path,
                    self.last_result.get('original_text', ''),
                    self.last_result.get('translated_text', ''),
                    self.last_result.get('insights', []),
                    self.last_result.get('type', 'Unknown'),
                    self.last_result.get('lang', 'English')
                )
                QMessageBox.information(self, "Success", f"Report saved successfully:\n{path}")
                
        except Exception as e:
            logger.error(f"Export Critical Fail: {e}")
            QMessageBox.critical(self, "Export Failed", f"An unexpected error occurred:\n{str(e)}")

    def reset_state(self):
        self.stack.setCurrentIndex(0)
        self.text_editor.clear()
        self.ai_response_area.clear()