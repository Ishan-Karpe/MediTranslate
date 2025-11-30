"""
tests/debug_hindi_fonts.py
For systems that have trouble rendering Devangari.
"""
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
db = QFontDatabase()
families = db.families()

print("--- HINDI FONTS FOUND ---")
for f in families:
    if "Devanagari" in f or "Hindi" in f or "Lohit" in f or "Gargi" in f:
        print(f)