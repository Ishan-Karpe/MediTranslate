"""
src/services/ai_assistant.py
Handles interaction with Google Gemini.
Uses dictionary-based configuration to avoid 'types' errors.
"""
import os
from loguru import logger
from dotenv import load_dotenv
from google import genai

# 1. Load environment variables
load_dotenv()

class AIAssistant:
    def __init__(self):
        # 2. Get Key & Initialize Client
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            logger.error("❌ GEMINI_API_KEY not found in .env file!")
            self.client = None
            return

        try:
            # Initialize Client
            self.client = genai.Client(api_key=self.api_key)
            logger.info("✨ Gemini AI Client initialized.")
        except Exception as e:
            logger.error(f"Failed to connect to Gemini: {e}")
            self.client = None

    def explain_term(self, term, local_def, full_context, target_lang):
        """
        Generates an empathetic, structured explanation using Gemini.
        """
        if not self.client:
            return "⚠️ AI Error: Client not active. Check API Key."

        # 3. Construct the Prompt
        prompt = f"""
        You are a kind, empathetic medical assistant helping a patient understand their medical document.
        
        TASK: Explain the term "{term}" to the patient.
        
        CONTEXT:
        - Patient Language: {target_lang} (OUTPUT MUST BE IN THIS LANGUAGE)
        - Document Excerpt: "{full_context[:1500]}..." 
        - Technical Definition: "{local_def}"
        
        GUIDELINES:
        1. **Tone:** Reassuring, calm, and clear. Avoid scary medical jargon.
        2. **Format:** Use Markdown (Bold headers, bullet points).
        3. **Structure:**
           - **What is it?** (Simple explanation)
           - **Why is it here?** (Context from the document)
           - **Next Steps:** (Actionable advice, e.g. "Take with food")
           - **Check-in:** Ask 1 simple question to check how they feel.
        4. **Safety:** Do NOT diagnose. Always refer to their actual doctor.
        
        Generate the response strictly in {target_lang}.
        """
        
        try:
            # 4. Generate Content (Dictionary Config)
            # FIX: We use a simple dict instead of 'types.GenerateContentConfig'
            response = self.client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt,
                config={
                    'temperature': 0.7, 
                }
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"AI Generation failed: {e}")
            # Fallback logic if 2.0 is not available for your key
            if "404" in str(e) or "not found" in str(e).lower():
                return self._fallback_generation(prompt)
            return f"Error connecting to AI: {str(e)}"

    def _fallback_generation(self, prompt):
        """Fallback to 1.5 Flash."""
        try:
            logger.warning("Gemini 2.0 failed, falling back to 1.5 Flash...")
            response = self.client.models.generate_content(
                model="gemini-flash-lite-latest",
                contents=prompt,
                config={'temperature': 0.7}
            )
            return response.text
        except Exception as e:
            return f"System Error: All AI models failed. {e}"