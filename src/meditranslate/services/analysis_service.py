"""
src/services/analysis_service.py
The Intelligence Layer.
Features: 
- Document Classification (detect_document_type)
- Primary Brain (Curated Glossary)
- Backup Brain (ICD-10) 
- Regex Pattern Matching
- Translation Wrapper
"""
import json
import re
from loguru import logger
from meditranslate.services.translation_service import TranslationService
from meditranslate.utils.paths import get_resource_path

class AnalysisService:
    def __init__(self):
        self.translator = None
        self.init_error = None
        try:
            self.translator = TranslationService()
        except Exception as e:
            self.init_error = str(e)
            logger.error(f"Translator failed to start: {e}")

        self.primary_glossary = {}
        self.backup_glossary = {} 
        
        self._load_primary_glossary()
        self._load_backup_glossary()

    def _load_primary_glossary(self):
        """Loads your hand-written, easy-to-understand glossary."""
        try:
            path = get_resource_path("data/medical_glossary.json")
            
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    self.primary_glossary = json.load(f)
                
                if "_meta" in self.primary_glossary:
                    del self.primary_glossary["_meta"]
                    
                logger.info(f"Primary Brain loaded: {len(self.primary_glossary)} terms.")
            else:
                self.primary_glossary = {"mg": {"title": "Milligrams", "desc": "Dosage unit", "type": "info"}}
        except Exception as e:
            logger.error(f"Primary glossary error: {e}")

    def _load_backup_glossary(self):
        """Loads the massive ICD-10 dataset."""
        try:
            path = get_resource_path("data/codes_glossary.json")
            
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    
                    # Handle List of Dictionaries
                    if isinstance(raw_data, list):
                        for item in raw_data:
                            if isinstance(item, dict):
                                code = item.get("code")
                                desc = item.get("description")
                                if code and desc:
                                    self.backup_glossary[code] = desc
                            elif isinstance(item, list) and len(item) >= 2:
                                self.backup_glossary[item[0]] = item[1]
                                
                    # Handle pure Dict
                    elif isinstance(raw_data, dict):
                        self.backup_glossary = raw_data
                        
                logger.info(f"Backup Brain loaded: {len(self.backup_glossary)} terms.")
            else:
                logger.warning(f"Backup glossary not found at {path}")
        except Exception as e:
            logger.error(f"Backup glossary error: {e}")

    def detect_document_type(self, text: str) -> str:
        """
        Classifies the document based on keywords.
        """
        text_lower = text.lower()
        
        # Simple Keyword Voting
        if any(x in text_lower for x in ["rx", "prescription", "pharmacy", "take", "daily", "tablet"]):
            return "Prescription / Medication List"
        
        if any(x in text_lower for x in ["lab", "metabolic", "count", "positive", "negative", "range", "result"]):
            return "Laboratory Report"
            
        if any(x in text_lower for x in ["discharge", "summary", "admitted", "hospital", "instructions"]):
            return "Discharge Summary"
            
        if any(x in text_lower for x in ["diagnosis", "history", "assessment", "plan"]):
            return "Clinical Note"
            
        return "General Medical Document"

    def analyze_text(self, text: str):
        """
        Scans text using Primary Brain -> Regex -> Backup Brain.
        """
        insights = []
        text_lower = text.lower()
        found_terms = set() 
        
        # PRIMARY BRAIN
        for term, data in self.primary_glossary.items():
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, text_lower):
                if term not in found_terms:
                    insights.append(data)
                    found_terms.add(term)

        # REGEX PATTERNS
        if re.search(r'\b\d{2,3}/\d{2,3}\b', text):
            insights.append({
                "title": "Blood Pressure", 
                "desc": "Systolic/Diastolic readings. Normal is ~120/80.", 
                "type": "warning"
            })
            
        if re.search(r'\b(99\.[5-9]|1\d{2}(\.\d)?)\s*F\b', text, re.IGNORECASE) or \
           re.search(r'\b(3[7-9](\.\d)?|4\d(\.\d)?)\s*C\b', text, re.IGNORECASE):
            insights.append({
                "title": "Fever Detected", 
                "desc": "High body temperature detected.", 
                "type": "warning"
            })
            
        if re.search(r'\btake\s+\d+(\.\d)?\s+(tablets|pills|capsules)', text_lower):
            insights.append({
                "title": "Dosage Instruction", 
                "desc": "Specific instruction on how many pills to take.", 
                "type": "info"
            })

        count = 0
        limit = 3 
        
        for code, desc in self.backup_glossary.items():
            if count >= limit: break
            
            if len(desc) > 4 and desc.lower() in text_lower:
                already_found = False
                for t in found_terms:
                    if t in desc.lower(): already_found = True
                
                if not already_found:
                    insights.append({
                        "title": f"{desc.title()} ({code})",
                        "desc": "Medical diagnosis detected via International Database.",
                        "type": "warning"
                    })
                    found_terms.add(desc.lower())
                    count += 1
            
        return insights

    def translate_content(self, text: str, target_lang: str) -> str:
        if self.translator is None:
            return f"[System Error]: Translator not active.\nReason: {self.init_error}"
        try:
            return self.translator.translate(text, target_lang)
        except Exception as e:
            return f"[Error]: {str(e)}"