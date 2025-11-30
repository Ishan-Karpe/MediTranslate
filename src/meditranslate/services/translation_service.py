"""
src/services/translation_service.py
Handles loading AI models and performing translation.
"""
from loguru import logger
from transformers import MarianMTModel, MarianTokenizer
from utils.paths import get_resource_path

class TranslationService:
    
    def __init__(self):
        self.models = {} 
        self.tokenizers = {}
        
        self.model_dir = get_resource_path("src/meditranslate/resources/models")
        
        self.model_map = {
            "Spanish": "Helsinki-NLP/opus-mt-en-es",
            "Hindi": "Helsinki-NLP/opus-mt-en-hi",
        }
        
        logger.info(f"Translation Service initialized.")
        logger.info(f"Looking for models at: {self.model_dir}")

    def load_model(self, target_lang):
        """
        Loads the specific model for English -> Target Language.
        """
        model_name = self.model_map.get(target_lang)
        if not model_name:
            raise ValueError(f"Unsupported language: {target_lang}")
            
        if target_lang in self.models:
            return
            
        model_path = self.model_dir / model_name
        
        if not model_path.exists():
            logger.error(f"Path not found: {model_path}")
            raise FileNotFoundError(f"Model missing for {target_lang}")
            
        logger.info(f"Loading AI Model for {target_lang}...")
        
        try:
            # Load from local folder
            self.tokenizers[target_lang] = MarianTokenizer.from_pretrained(str(model_path))
            self.models[target_lang] = MarianMTModel.from_pretrained(str(model_path))
            logger.success(f"Loaded {target_lang} model")
        except Exception as e:
            logger.critical(f"Failed to load model: {e}")
            raise e

    def translate(self, text: str, target_lang: str) -> str:
        if not text or not text.strip():
            return ""
            
        self.load_model(target_lang)
        
        tokenizer = self.tokenizers[target_lang]
        model = self.models[target_lang]
        
        # Translate
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        translated = model.generate(**inputs) #kwargs
        result = tokenizer.batch_decode(translated, skip_special_tokens=True)
        
        return " ".join(result)