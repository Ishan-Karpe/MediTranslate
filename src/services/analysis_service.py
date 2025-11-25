"""
src/services/analysis_service.py
Simulates the AI Intelligence layer.
Handles Translation (mock/real) and Medical Explanations.
"""
from loguru import logger

class AnalysisService:
    """
    Orchestrates text analysis: Translation + Contextual Explanation.
    """
    
    def __init__(self):
        # Our "Local Knowledge Base" (The AI Brain)
        self.medical_db = {
            "mg": {"title": "Milligrams (Dosage)", "desc": "Unit of measurement for medicine strength.", "type": "info"},
            "tablet": {"title": "Tablet Form", "desc": "Solid pill. Usually taken with water.", "type": "info"},
            "daily": {"title": "Frequency: Daily", "desc": "Take this once every 24 hours.", "type": "warning"},
            "amoxicillin": {"title": "Amoxicillin", "desc": "Antibiotic used to treat bacterial infections.", "type": "drug"},
            "hypertension": {"title": "Hypertension", "desc": "High blood pressure. Monitor heart rate.", "type": "warning"},
            "take": {"title": "Instruction", "desc": "Action required by patient.", "type": "info"}
        }

    def analyze_text(self, text: str):
        """
        Scans text for medical terms and returns explanations.
        """
        found_insights = []
        text_lower = text.lower()
        
        for keyword, data in self.medical_db.items():
            if keyword in text_lower:
                found_insights.append(data)
                
        return found_insights

    def mock_translate(self, text: str, target_lang: str) -> str:
        """
        Placeholder for MarianMT (Day 3). 
        For now, it returns the text with a tag so we know the UI works.
        """
        # In Day 3, we will hook up the real AI model here.
        return f"[Translated to {target_lang}]: {text}"