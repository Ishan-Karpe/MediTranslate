"""
src/meditranslate/services/ai_assistant.py
Handles interaction with Google Gemini.
Features:
- Loads API Key from Home Directory (for installed tools).
- Automatic Retry Logic for Rate Limits.
- Bilingual Output (Target + English).
"""
import os
import time
import random
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv
from google import genai

class AIAssistant:
    def __init__(self):
        # Try Loading Key from Environment or Home Directory
        # Priority: Env Var > Local .env > Home Dir .env
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            # Check User Home Directory (~/.env)
            home_env = Path.home() / ".env"
            if home_env.exists():
                load_dotenv(home_env)
                api_key = os.getenv("GEMINI_API_KEY")

        self.api_key = api_key
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found! AI features will be disabled.")
            self.client = None
            return

        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.info("Gemini AI Client initialized.")
        except Exception as e:
            logger.error(f"Failed to connect to Gemini: {e}")
            self.client = None

    def explain_term(self, term, local_def, full_context, target_lang):
        """
        Generates explanation with retry logic.
        """
        if not self.client:
            return "AI Error: Client not active. Please add GEMINI_API_KEY to your ~/.env file."

        prompt = f"""
        Act as a warm, culturally sensitive medical guide for a patient who speaks {target_lang}.
        
        TASK: Explain the term "{term}" to the patient.
        
        CONTEXT:
        - Document Excerpt: "{full_context[:2000]}"
        - Technical Definition: "{local_def}"
        
        CULTURAL GUIDELINES:
        1. **Reassurance:** Medical terms can be scary. Use calming language.
        2. **Simplicity:** Use analogies relevant to daily life.
        3. **Action:** Focus on what they can DO (diet, rest).
        
        OUTPUT FORMAT (Strictly follow this):
        
        ### {target_lang} Explanation
        (Provide a culturally appropriate, respectful explanation in {target_lang}.)
        
        ---
        
        ### English Explanation
        * **What is it?** (Simple explanation)
        * **Why is it here?** (Context from doc)
        * **Advice:** (Actionable steps)
        """
    
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model="gemini-flash-latest",
                    contents=prompt,
                    config={'temperature': 0.75}
                )
                return response.text

            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "503" in error_str:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"AI Busy. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    
                    if attempt == max_retries - 1:
                        return self._fallback_generation(prompt)
                
                elif "404" in error_str:
                    return self._fallback_generation(prompt)
                
                else:
                    return f"Error connecting to AI: {str(e)}"
        
        return "AI Service busy. Please try again."

    def _fallback_generation(self, prompt):
        try:
            logger.info("Falling back to Flash Lite...")
            response = self.client.models.generate_content(
                model="gemini-flash-lite-latest",
                contents=prompt,
                config={'temperature': 0.75}
            )
            return response.text
        except Exception as e:
            return f"System Error: All AI models failed. {e}"