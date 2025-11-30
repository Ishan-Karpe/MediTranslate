"""
src/services/ai_assistant.py
Handles interaction with Google Gemini.
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
            logger.error("GEMINI_API_KEY not found in .env file!")
            self.client = None
            return

        try:
            # Initialize Client
            self.client = genai.Client(api_key=self.api_key)
            logger.info("Gemini AI Client initialized.")
        except Exception as e:
            logger.error(f"Failed to connect to Gemini: {e}")
            self.client = None

    def explain_term(self, term, local_def, full_context, target_lang):
        """
        Generates an empathetic, structured explanation using Gemini.
        """
        if not self.client:
            return "AI Error: Client not active. Check API Key."

        # 3. Construct the Prompt
        prompt = f"""
        Act as a warm, culturally sensitive medical guide for a patient who speaks {target_lang}.
        
        TASK: Explain the term "{term}" to the patient.
        
        CONTEXT:
        - Document Excerpt: "{full_context[:2000]}..." 
        - Technical Definition: "{local_def}"
        
        CULTURAL GUIDELINES:
        1. **Reassurance:** Medical terms can be scary. Use calming language.
        2. **Simplicity:** Use analogies relevant to daily life (e.g., "Like a filter getting clogged" for kidney issues).
        3. **Respect:** If the condition carries social stigma, address it with privacy and dignity.
        4. **Action:** Focus on what they can DO (diet, rest), not just the pathology.
        
        OUTPUT FORMAT (Strictly follow this):
        
        ### {target_lang} Explanation followed by English Explanation:

        ### {target_lang} Explanation
        (Translate the above, but adapt the tone to be culturally appropriate and respectful in {target_lang}.)


        ### English Explanation
        * **What is it?** (Simple explanation)
        * **Why is it here?** (Context from doc)
        * **Advice:** (Actionable steps)
        """
        
        try:
            response = self.client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt,
                config={
                    'temperature': 0.75, 
                }
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"AI Generation failed: {e}")
            if "404" in str(e) or "not found" in str(e).lower():
                return self._fallback_generation(prompt)
            return f"Error connecting to AI: {str(e)}"

    def _fallback_generation(self, prompt):
        try:
            logger.warning("Gemini Flash failed, falling back to Flash Lite...")
            response = self.client.models.generate_content(
                model="gemini-flash-lite-latest",
                contents=prompt,
                config={'temperature': 0.75}
            )
            return response.text
        except Exception as e:
            return f"System Error: All AI models failed. {e}"