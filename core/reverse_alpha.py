"""
Reverse alpha blending - core mathematical watermark removal.

Principle:
  Gemini/Veo adds watermark via alpha compositing:
    watermarked = alpha * logo + (1 - alpha) * original

  Reverse solve:
    original = (watermarked - alpha * logo) / (1 - alpha)
"""

import numpy as np
import os
import sys

# Import config from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def load_alpha_map(size):
    """
    Load an embedded alpha map from binary Float32 data.
    Size: 48 or 96
    Returns: (logo_size, alpha_map_2d) where alpha_map_2d shape is (size, size)
    """
    if size == 48:
        path = config.ALPHA_MAP_48
    elif size == 96:
        path = config.ALPHA_MAP_96
    else:
        raise ValueError(f"Unsupported alpha map size: {size}")

    if not os.path.exists(path):
        raise FileNotFoundError(f"Alpha map not found: {path}")

    data = np.fromfile(path, dtype=np.float32)
    expected = size * size
    if len(data) != expected:
        raise ValueError(
            f"Alpha map {size}x{size}: expected {expected} floats, got {len(data)}"
        )
    return size, data.reshape(size, size)


def remove_watermark_from_region(
    region,
    alpha_map_2d,
    alpha_gain=1.0,
    noise_floor=None,
    alpha_threshold=None,
    max_alpha=None,
    logo_value=None,
):
    """
    Apply reverse alpha blending to a watermark region.

    Args:
        region: (H, W, 3) uint8 numpy array - the watermark area from the frame
        alpha_map_2d: (H, W) float32 - alpha values 0.0-1.0
        alpha_gain: multiplier for alpha strength

    Returns:
        (H, W, 3) uint8 array with watermark removed
    """
    if noise_floor is None:
        noise_floor = config.ALPHA_NOISE_FLOOR
    if alpha_threshold is None:
        alpha_threshold = config.ALPHA_THRESHOLD
    if max_alpha is None:
        max_alpha = config.MAX_ALPHA
    if logo_value is None:
        logo_value = config.LOGO_VALUE / 255.0

    # Work in float32 normalized to [0, 1]
    img = region.astype(np.float32) / 255.0

    # Get raw alpha
    raw_alpha = alpha_map_2d

    # Remove noise floor for signal detection
    signal_alpha = np.maximum(0, raw_alpha - noise_floor) * alpha_gain

    # Only process pixels where signal exceeds threshold
    mask = signal_alpha >= alpha_threshold

    if not np.any(mask):
        return region.copy()

    # Use clamped alpha for the inverse solve
    alpha = np.clip(raw_alpha * alpha_gain, 0, max_alpha)
    one_minus_alpha = 1.0 - alpha

    # Reverse alpha blending per channel
    result = img.copy()
    for c in range(3):
        channel = img[:, :, c]
        recovered = (channel - alpha * logo_value) / one_minus_alpha
        recovered = np.clip(recovered, 0, 1)
        # Apply only where mask is True
        result[:, :, c] = np.where(mask, recovered, channel)

    return (result * 255).astype(np.uint8)


def remove_watermark_from_frame(
    frame,
    alpha_map_2d,
    position,
    alpha_gain=1.0,
):
    """
    Remove watermark from a full video frame.

    Args:
        frame: (H, W, 3) uint8 numpy array - full video frame
        alpha_map_2d: (logo_size, logo_size) float32 - alpha map
        position: dict with {x, y, width, height}
        alpha_gain: multiplier for alpha strength

    Returns:
        (H, W, 3) uint8 array with watermark removed
    """
    x = position['x']
    y = position['y']
    w = position['width']
    h = position['height']

    # Ensure region is within frame bounds
    if x < 0 or y < 0 or x + w > frame.shape[1] or y + h > frame.shape[0]:
        x = max(0, x)
        y = max(0, y)
        w = min(w, frame.shape[1] - x)
        h = min(h, frame.shape[0] - y)
        if w <= 0 or h <= 0:
            return frame.copy()
        alpha_map_2d = alpha_map_2d[:h, :w]

    # Extract the watermark region
    region = frame[y:y + h, x:x + w].copy()

    # Remove watermark
    cleaned_region = remove_watermark_from_region(region, alpha_map_2d, alpha_gain)

    # Place back
    result = frame.copy()
    result[y:y + h, x:x + w] = cleaned_region
    return result
