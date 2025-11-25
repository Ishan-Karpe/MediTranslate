"""
src/services/analysis_service.py
Orchestrates Translation and Contextual Analysis.
"""
from loguru import logger
from services.translation_service import TranslationService

class AnalysisService:
    def __init__(self):
        # 1. Try to load Translator, but expect failure
        self.translator = None
        self.init_error = None
        
        try:
            self.translator = TranslationService()
        except Exception as e:
            self.init_error = str(e)
            logger.error(f"CRITICAL: TranslationService failed to start. {e}")
        
        # Medical Keywords (same as before)
        self.medical_db = {
            "mg": {"title": "Milligrams", "desc": "Unit of measurement.", "type": "info"},
            "tablet": {"title": "Tablet", "desc": "Solid pill.", "type": "info"},
            "daily": {"title": "Daily", "desc": "Once every 24 hours.", "type": "warning"},
            "amoxicillin": {"title": "Amoxicillin", "desc": "Antibiotic.", "type": "drug"},
            "hypertension": {"title": "Hypertension", "desc": "High blood pressure.", "type": "warning"},
            "fever": {"title": "Fever", "desc": "High body temp.", "type": "warning"}
        }

    def analyze_text(self, text: str):
        found = []
        for k, v in self.medical_db.items():
            if k in text.lower(): found.append(v)
        return found

    def translate_content(self, text: str, target_lang: str) -> str:
        logger.info(f"Translating to {target_lang}...")
        
        # 2. SAFETY CHECK: If translator failed to load, return the error to the UI
        if self.translator is None:
            error_msg = f"[System Error]: Translator not active.\nReason: {self.init_error}"
            logger.warning(error_msg)
            return error_msg

        try:
            return self.translator.translate(text, target_lang)
        except Exception as e:
            logger.error(f"Translation runtime error: {e}")
            return f"[Error]: {str(e)}"