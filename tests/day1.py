"""
tests/day1.py
Unit tests for Day 1 Image Processing.
"""
import unittest
import numpy as np
import sys
import os

# Add 'src' to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from utils.image_processing import ImageProcessor

class TestDay1(unittest.TestCase):
    
    def setUp(self):
        """Runs before every test."""
        self.processor = ImageProcessor()
        # Create a fake random image (100x100 pixels, RGB)
        self.fake_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

    def test_processor_exists(self):
        """Does the class initialize?"""
        self.assertIsNotNone(self.processor)

    def test_processing_flow(self):
        """Does enhancement return a valid image?"""
        result = self.processor.enhance_for_ocr(self.fake_image)
        self.assertIsNotNone(result)
        # Result should still be RGB (3 channels) for UI display
        self.assertEqual(result.shape[2], 3)
        
    def test_empty_input(self):
        """Does it handle None input without crashing?"""
        result = self.processor.enhance_for_ocr(None)
        self.assertIsNone(result)

if __name__ == '__main__':
    print("Running Day 1 Tests...")
    unittest.main()