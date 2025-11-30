"""
tests/debug_models.py
For models that may error out due to corrupted/missing downloaded files.
Checks both Hindi and Spanish translation pipelines.
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

try:
    print("1. Importing TranslationService...")
    from services.translation_service import TranslationService
    print("   Import successful.")
    
    print("\n2. Initializing Service (Loading paths)...")
    service = TranslationService()
    print(f"   Service Initialized. Model dir: {service.model_dir}")
    

    print("\n--- 3A. Checking HINDI Model ---")
    hindi_path = service.model_dir / "Helsinki-NLP/opus-mt-en-hi"
    
    if hindi_path.exists():
         print(f"   Hindi Model found at: {hindi_path}")
    else:
         print(f"   Hindi Model MISSING at: {hindi_path}")
         print("   SOLUTION: Run 'uv run download_models.py' again.")
         sys.exit(1)

    print("   Loading Hindi Model (Heavy Step)...")
    service.load_model("Hindi")
    print("   Hindi Model Loaded into RAM.")
    
    print("   Test Translation (English -> Hindi)...")
    result_hi = service.translate("Hello Doctor", "Hindi")
    print(f"   Result: {result_hi}")

    print("\n--- 3B. Checking SPANISH Model ---")
    spanish_path = service.model_dir / "Helsinki-NLP/opus-mt-en-es"
    
    if spanish_path.exists():
         print(f"   Spanish Model found at: {spanish_path}")
    else:
         print(f"   Spanish Model MISSING at: {spanish_path}")
         print("   SOLUTION: Run 'uv run download_models.py' again.")
         sys.exit(1)

    print("   Loading Spanish Model (Heavy Step)...")
    service.load_model("Spanish")
    print("   Spanish Model Loaded into RAM.")
    
    print("   Test Translation (English -> Spanish)...")
    result_es = service.translate("Hello Doctor", "Spanish")
    print(f"   Result: {result_es}")

    print("\nSUCCESS: All models are healthy!")
    
except Exception as e:
    print("\nFATAL ERROR DURING DEBUG:")
    print(e)
    print("\nNote: If the error mentions 'sentencepiece', run: uv add sentencepiece")
    print("Note: If the error mentions 'sacremoses', run: uv add sacremoses")