"""
download_models.py
Downloads MarianMT models to a fixed absolute path.
"""
import os
from pathlib import Path
from transformers import MarianMTModel, MarianTokenizer
from loguru import logger

PROJECT_ROOT = Path(__file__).parent.absolute()
MODEL_DIR = PROJECT_ROOT / "resources" / "models"

MODELS = [
    "Helsinki-NLP/opus-mt-en-es",
    "Helsinki-NLP/opus-mt-es-en",
    "Helsinki-NLP/opus-mt-en-hi",
    "Helsinki-NLP/opus-mt-hi-en"
]

def download():
    logger.info(f"Starting fresh download to: {MODEL_DIR}")

    if not MODEL_DIR.exists():
        os.makedirs(MODEL_DIR)
        logger.info("Created resources/models directory.")

    for model_name in MODELS:
        logger.info(f"⬇️  Fetching {model_name}...")
        try:
            save_path = MODEL_DIR / model_name
            
            model = MarianMTModel.from_pretrained(model_name)
            tokenizer = MarianTokenizer.from_pretrained(model_name)
            
            model.save_pretrained(save_path)
            tokenizer.save_pretrained(save_path)
            
            logger.success(f"Saved: {model_name}")
        except Exception as e:
            logger.error(f"Failed {model_name}: {e}")

if __name__ == "__main__":
    download()