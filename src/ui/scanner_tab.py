"""
src/ui/scanner_tab.py
The Complete "Intelligent Assistant" UI.
Features:
- PDF Input & Export (Bilingual)
- AI Caretaker (Culturally Aware)
- High Contrast Mode (Grayscale Toggle)
- Professional UI Layout (Grey Sidebar, Centered Headers)
- Robust Threading & Error Handling
"""
from pathlib import Path
import cv2
import numpy as np
from loguru import logger
from pdf2image import convert_from_path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QGroupBox, QTextEdit, 
    QScrollArea, QFrame, QStackedWidget, QSizePolicy, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QThread, QObject
from PySide6.QtGui import QFont

# Services
from services.ocr_service import OCRService
from services.analysis_service import AnalysisService
from services.ai_assistant import AIAssistant
from services.pdf_service import PDFService
from utils.image_processing import ImageProcessor

# --- WORKER 1: IMAGE PROCESSING, OCR & TRANSLATION ---
class ProcessingWorker(QObject):
    # Returns: (TranslatedText, DocType, InsightsList, RawEnglishText)
    finished = Signal(str, str, list, str) 
    error = Signal(str)

    def __init__(self, ocr, analysis, processor, image, target_lang, force_binary):
        super().__init__()
        self.ocr = ocr
        self.analysis = analysis
        self.processor = processor
        self.image = image
        self.target_lang = target_lang
        self.force_binary = force_binary

    def run(self):
        try:
            # 1. ENHANCE IMAGE (CPU Heavy - Run in thread)
            # Apply High Contrast if checkbox was checked
            processed_img = self.processor.enhance_for_ocr(self.image, self.force_binary)
            
            # 2. OCR (Read English Text)
            raw_text = self.ocr.extract_text(processed_img, lang='eng')
            
            # 3. Detect Type
            doc_type = self.analysis.detect_document_type(raw_text)
            
            # 4. Translate Document
            translated_text = self.analysis.translate_content(raw_text, self.target_lang)
            
            # 5. Analyze (Get English Insights)
            insights = self.analysis.analyze_text(raw_text)
            
            # 6. TRANSLATE INSIGHTS (Bilingual Data for PDF)
            final_insights = []
            seen = set()
            for item in insights:
                orig_title = item.get('title', '')
                if orig_title in seen: continue
                seen.add(orig_title)
                
                # Translate Title & Description
                item['trans_title'] = self.analysis.translate_content(orig_title, self.target_lang)
                item['trans_desc'] = self.analysis.translate_content(item.get('desc', ''), self.target_lang)
                
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
        # Calls Gemini with the Culturally Aware prompt
        response = self.ai.explain_term(self.term, self.local_def, self.context, self.lang)
        self.finished.emit(response)

# --- UI COMPONENT: INSIGHT CARD ---
class InsightCard(QFrame):
    def __init__(self, title, desc, card_type="info"):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName(f"Card_{card_type}")
        
        # Let layout handle height dynamically, but set minimum
        self.setMinimumHeight(80)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title (Bold)
        lbl_title = QLabel(title)
        lbl_title.setWordWrap(True)
        # Font will be set by parent based on language
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
        upload_layout.setSpacing(15) # Tighter spacing for the header group
        
        # 1. Main Header
        lbl_welcome = QLabel("MediTranslate AI")
        lbl_welcome.setObjectName("TitleLabel")
        lbl_welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 2. Instruction Text (Right below header)
        lbl_sub = QLabel("Select target language:")
        lbl_sub.setObjectName("SubHeader") # New ID for styling
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 3. Language Dropdown (Right below text)
        self.lang_select = QComboBox()
        self.lang_select.addItems(["Spanish", "Hindi"])
        self.lang_select.setFixedSize(300, 50)
        self.lang_select.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lang_select.setObjectName("LangSelect")
        
        # 4. High Contrast Checkbox
        self.chk_contrast = QCheckBox("High Contrast (For Blue/Pink Paper)")
        self.chk_contrast.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 5. Buttons (Enlarged)
        btn_layout = QHBoxLayout()
        self.btn_upload = QPushButton("📂 Upload File")
        self.btn_upload.setFixedSize(250, 80) # Bigger
        self.btn_upload.setObjectName("BigButton")
        self.btn_upload.clicked.connect(self._upload_file)
        
        self.btn_camera = QPushButton("📷 Use Camera")
        self.btn_camera.setFixedSize(250, 80) # Bigger
        self.btn_camera.setObjectName("BigButton")
        self.btn_camera.clicked.connect(self._capture_camera)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_upload)
        btn_layout.addWidget(self.btn_camera)
        btn_layout.addStretch()
        
        # Add to Layout (Vertical Stack)
        upload_layout.addStretch()
        upload_layout.addWidget(lbl_welcome)
        upload_layout.addWidget(lbl_sub) # Directly below header
        upload_layout.addWidget(self.lang_select, alignment=Qt.AlignmentFlag.AlignCenter) # Directly below text
        
        # Spacer before toggle
        upload_layout.addSpacing(20)
        upload_layout.addWidget(self.chk_contrast, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Spacer before buttons
        upload_layout.addSpacing(20)
        upload_layout.addLayout(btn_layout)
        upload_layout.addStretch()
        
        # === VIEW 2: RESULTS SCREEN ===
        self.view_results = QWidget()
        results_layout = QHBoxLayout(self.view_results)
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.setSpacing(0)
        
        # --- LEFT PANEL: TRANSLATED DOCUMENT ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(30, 30, 30, 30)
        left_layout.setSpacing(15)
        
        # Centered Heading
        lbl_res_title = QLabel("TRANSLATED DOCUMENT")
        lbl_res_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_res_title.setStyleSheet("font-weight: 900; font-size: 16px; color: #2E7D32; letter-spacing: 1px;")
        
        lbl_res_sub = QLabel("View the AI-translated text below.")
        lbl_res_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_res_sub.setStyleSheet("color: #757575; font-size: 13px; margin-bottom: 10px;")
        
        self.text_editor = QTextEdit()
        self.text_editor.setPlaceholderText("Processing...")
        self.text_editor.setObjectName("Editor")
        self.text_editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Bottom Actions
        bottom_actions = QHBoxLayout()
        self.btn_reset = QPushButton("← Scan New")
        self.btn_reset.setObjectName("ResetButton")
        self.btn_reset.clicked.connect(self.reset_state)
        
        self.btn_export = QPushButton("📥 Export PDF")
        self.btn_export.setObjectName("ExportButton")
        self.btn_export.clicked.connect(self._export_pdf)
        self.btn_export.setEnabled(False)
        
        bottom_actions.addWidget(self.btn_reset)
        bottom_actions.addStretch()
        bottom_actions.addWidget(self.btn_export)
        
        left_layout.addWidget(lbl_res_title)
        left_layout.addWidget(lbl_res_sub)
        left_layout.addWidget(self.text_editor)
        left_layout.addLayout(bottom_actions)
        
        # --- RIGHT PANEL: SIDEBAR (Grey Background) ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(420)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(20, 30, 20, 30)
        sidebar_layout.setSpacing(20)
        
        lbl_ai_title = QLabel("🤖 AI MEDICAL GUIDE")
        lbl_ai_title.setStyleSheet("font-weight: 900; color: #1565C0; font-size: 14px;")
        
        # 1. Interactive Question Box
        question_box = QGroupBox("What confuses you?")
        question_box.setObjectName("AIBox")
        q_layout = QVBoxLayout(question_box)
        q_layout.setSpacing(10)
        
        self.term_selector = QComboBox()
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
        self.ai_response_area.setMinimumHeight(150)
        
        # 3. Static Cards List
        self.ai_scroll = QScrollArea()
        self.ai_scroll.setWidgetResizable(True)
        self.ai_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.ai_scroll.setStyleSheet("background: transparent;")
        
        self.ai_container = QWidget()
        self.ai_layout = QVBoxLayout(self.ai_container)
        self.ai_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.ai_layout.setSpacing(10)
        self.ai_layout.setContentsMargins(0,0,0,0)
        self.ai_scroll.setWidget(self.ai_container)
        
        sidebar_layout.addWidget(lbl_ai_title)
        sidebar_layout.addWidget(question_box)
        sidebar_layout.addWidget(self.ai_response_area)
        sidebar_layout.addWidget(self.ai_scroll)
        
        # Combine Panels
        results_layout.addWidget(left_panel, stretch=1)
        results_layout.addWidget(self.sidebar, stretch=0)
        
        self.stack.addWidget(self.view_upload)
        self.stack.addWidget(self.view_results)

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #FFFFFF; font-family: 'Segoe UI', sans-serif; }
            
            /* Sidebar Container */
            QWidget#Sidebar {
                background-color: #F8F9FA;
                border-left: 1px solid #E0E0E0;
            }
            
            QLabel#TitleLabel { font-size: 36px; font-weight: bold; color: #263238; }
            QLabel#SubHeader { color: #666; font-size: 16px; margin-bottom: 5px; }
            
            QComboBox { border: 1px solid #B0BEC5; border-radius: 6px; padding: 8px; background: white; font-size: 14px; }
            QCheckBox { font-size: 14px; color: #555; font-weight: bold; spacing: 8px; }
            
            /* Big Buttons */
            QPushButton#BigButton {
                background-color: white; border: 2px solid #E0E0E0;
                border-radius: 12px; font-size: 18px; font-weight: bold; color: #455A64;
            }
            QPushButton#BigButton:hover {
                background-color: #E3F2FD; border-color: #2196F3; color: #1976D2;
            }
            
            QTextEdit#Editor {
                border: 1px solid #E0E0E0; border-radius: 8px; background-color: white; padding: 25px;
                font-family: 'Noto Sans Devanagari', 'Noto Sans', sans-serif; font-size: 15px; line-height: 1.6;
            }
            
            /* AI Box */
            QGroupBox#AIBox {
                font-weight: bold; border: 1px solid #CFD8DC; border-radius: 8px; 
                background-color: white; padding-top: 25px; margin-top: 5px;
            }
            
            QPushButton#ActionButton {
                background-color: #673AB7; color: white; border-radius: 6px; padding: 12px; font-weight: bold; border: none;
            }
            QPushButton#ActionButton:hover { background-color: #7E57C2; }
            
            QTextEdit#AIResponse {
                border: none; background-color: #F3E5F5; border-radius: 12px; padding: 15px;
                color: #4A148C; font-family: 'Noto Sans Devanagari', 'Noto Sans', sans-serif; font-size: 14px;
            }
            
            QPushButton#ResetButton {
                background-color: #FFEBEE; color: #D32F2F; border: none; padding: 12px 24px; border-radius: 6px; font-weight: bold;
            }
            QPushButton#ExportButton {
                background-color: #2E7D32; color: white; border: none; padding: 12px 24px; border-radius: 6px; font-weight: bold;
            }
            
            /* Cards on Grey Background need White BG */
            QFrame#Card_info { background-color: white; border: 1px solid #E1F5FE; border-left: 4px solid #29B6F6; border-radius: 6px; }
            QFrame#Card_warning { background-color: white; border: 1px solid #FFF8E1; border-left: 4px solid #FFA726; border-radius: 6px; }
            QFrame#Card_drug { background-color: white; border: 1px solid #E8F5E9; border-left: 4px solid #66BB6A; border-radius: 6px; }
            
            QScrollBar:vertical { border: none; background: #E0E0E0; width: 10px; margin: 0px; border-radius: 5px; }
            QScrollBar::handle:vertical { background: #90A4AE; min-height: 30px; border-radius: 5px; }
        """)

    def _upload_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Doc", str(Path.home()), "Documents (*.png *.jpg *.pdf)")
        if path:
            if path.lower().endswith('.pdf'): self._process_pdf(path)
            else:
                img = cv2.imread(path)
                if img is not None: self._start_processing(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    def _process_pdf(self, path):
        try:
            images = convert_from_path(path, first_page=1, last_page=1)
            if images: self._start_processing(np.array(images[0]))
        except Exception as e: QMessageBox.warning(self, "Error", f"PDF Error: {e}")

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
        use_contrast = self.chk_contrast.isChecked()
        self.stack.setCurrentIndex(1)
        self.text_editor.setText(f"⏳ Processing...")
        self.term_selector.clear()
        self.ai_response_area.clear()
        self.btn_export.setEnabled(False)
        
        while self.ai_layout.count():
            child = self.ai_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        
        self.thread = QThread()
        self.worker = ProcessingWorker(self.ocr_service, self.analysis_service, self.image_processor, image, target, use_contrast)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_process_finished)
        self.worker.error.connect(self._on_process_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def _on_process_finished(self, text, doc_type, insights, raw_text):
        if not raw_text or not raw_text.strip():
            QMessageBox.warning(self, "No Text", "Could not read text. Try High Contrast mode.")
            self.text_editor.setPlaceholderText("Scan failed. Try again.")
            self.btn_reset.setEnabled(True)
            return

        self.text_editor.setText(text)
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
        self.last_result = {"text": text, "type": doc_type, "insights": insights, "lang": current_lang, "original_text": raw_text, "translated_text": text}
        
        seen = set()
        for item in insights:
            display_title = item.get('trans_title', item.get('title', 'Unknown'))
            if display_title not in seen:
                self.term_selector.addItem(display_title)
                seen.add(display_title)
            
            card = InsightCard(display_title, item.get('trans_desc', ''), item.get('type', 'info'))
            for child in card.findChildren(QLabel): child.setFont(font)
            self.ai_layout.addWidget(card)
        
        if not insights: self.ai_layout.addWidget(QLabel("No specific terms found."))
        self.ai_layout.addStretch()
        
        enable_ai = self.term_selector.count() > 0
        self.term_selector.setEnabled(enable_ai)
        self.btn_explain.setEnabled(enable_ai)

    def _on_process_error(self, err):
        self.text_editor.setText(f"Error: {err}")
        self.btn_reset.setEnabled(True)

    def _ask_ai(self):
        term = self.term_selector.currentText()
        target = self.lang_select.currentText()
        local_def = "No local definition"
        for item in self.found_insights_cache:
            if item.get('trans_title') == term:
                local_def = item.get('trans_desc', '')
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
            lang_key = self.last_result.get('lang', 'Report').replace(" ", "")
            default_name = f"MediTranslate_{lang_key}.pdf"
            path, _ = QFileDialog.getSaveFileName(self, "Save PDF", str(Path.home() / default_name), "PDF (*.pdf)")
            
            if path:
                str_path = str(path)
                if Path(str_path).exists():
                    try:
                        with open(str_path, 'wb'): pass
                    except IOError:
                        QMessageBox.warning(self, "File Error", "Could not overwrite file. Is it open?")
                        return

                self.pdf_service.generate_report(
                    str_path,
                    self.last_result.get('original_text', ''),
                    self.last_result.get('translated_text', ''),
                    self.last_result.get('insights', []),
                    self.last_result.get('type', 'Unknown'),
                    self.last_result.get('lang', 'English')
                )
                QMessageBox.information(self, "Success", f"Saved to:\n{str_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def reset_state(self):
        self.stack.setCurrentIndex(0)
        self.text_editor.clear()
        self.ai_response_area.clear()
        self.chk_contrast.setChecked(False)