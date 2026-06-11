"""
Gemini Omni Watermark Remover - Configuration
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.join(BASE_DIR, 'core')

# Alpha map files (Float32 raw data)
# alpha_48.bin = Gemini image watermark
# alpha_48_veo.bin = Veo video watermark (more transparent, larger margins)
ALPHA_MAP_48 = os.path.join(CORE_DIR, 'alpha_48_veo.bin')
ALPHA_MAP_96 = os.path.join(CORE_DIR, 'alpha_96.bin')

# Reverse alpha blending thresholds
ALPHA_NOISE_FLOOR = 3 / 255.0   # Remove low-level quantization noise
ALPHA_THRESHOLD = 0.002          # Ignore very small alpha values
MAX_ALPHA = 0.99                 # Avoid division by near-zero
LOGO_VALUE = 255                 # White watermark color

# Output settings
USE_H264 = True                  # Use H.264 encoding for better compatibility
