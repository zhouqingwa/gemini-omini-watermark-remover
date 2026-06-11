"""
Watermark size catalog for Gemini Omni generated content.

Omni video watermark (confirmed for 9:16 and 16:9):
  - 48x48 logo, marginRight=96, marginBottom=96
  - Same alpha map for all resolutions
  - Calibrated from actual Omni video frames

Gemini image watermarks have different margins (32/64/192px).
"""

import numpy as np

# ============================================================
# Omni video watermark config - consistent across all sizes
# Calibrated from actual Omni frames at 720x1280 and 1280x720
# ============================================================
VEO_WATERMARK = {'logoSize': 48, 'marginRight': 96, 'marginBottom': 96}

# Known Veo video resolutions (for exact matching)
VEO_RESOLUTIONS = [
    (720, 1280),   # 9:16  portrait
    (1280, 720),   # 16:9  landscape
    (1080, 1920),  # 9:16  portrait HD
    (1920, 1080),  # 16:9  landscape HD
]

# ============================================================
# Gemini image watermark configs (legacy, for reference)
# ============================================================
TIER_CONFIGS = {
    '0.5k': {'logoSize': 48, 'marginRight': 32, 'marginBottom': 32},
    '1k':   {'logoSize': 96, 'marginRight': 64, 'marginBottom': 64},
    '2k':   {'logoSize': 96, 'marginRight': 64, 'marginBottom': 64},
    '4k':   {'logoSize': 96, 'marginRight': 64, 'marginBottom': 64},
    '2k-new-margin': {'logoSize': 96, 'marginRight': 192, 'marginBottom': 192},
}

KNOWN_GEMINI_SIZES = [
    (512, 512), (256, 1024), (192, 1536), (424, 632), (632, 424),
    (448, 600), (1024, 256), (600, 448), (464, 576), (576, 464),
    (1536, 192), (384, 688), (688, 384), (792, 168),
    (1024, 1024), (512, 2048), (384, 3072), (848, 1264), (1264, 848),
    (896, 1200), (2048, 512), (1200, 896), (928, 1152), (1152, 928),
    (3072, 384), (768, 1376), (1376, 768), (1408, 768), (1584, 672),
    (2048, 2048), (1024, 4096), (768, 6144), (1696, 2528), (2528, 1696),
    (1792, 2400), (4096, 1024), (2400, 1792), (1856, 2304), (2304, 1856),
    (6144, 768), (1536, 2752), (2752, 1536), (3168, 1344),
    (2816, 1536),
    (4096, 4096), (2048, 8192), (1536, 12288), (3392, 5056), (5056, 3392),
    (3584, 4800), (8192, 2048), (4800, 3584), (3712, 4608), (4608, 3712),
    (12288, 1536), (3072, 5504), (5504, 3072), (6336, 2688),
]


def detect_watermark_config(width, height):
    """
    Detect watermark configuration for a given resolution.
    Returns {'logoSize', 'marginRight', 'marginBottom'}.
    """
    # 1. Try Veo exact match
    if (width, height) in VEO_RESOLUTIONS:
        return dict(VEO_WATERMARK)

    # 2. Try Gemini exact match (legacy images)
    for (kw, kh) in KNOWN_GEMINI_SIZES:
        if kw == width and kh == height:
            if max(width, height) <= 1024:
                return dict(TIER_CONFIGS['0.5k'])
            elif width == 2816 and height == 1536:
                return dict(TIER_CONFIGS['2k-new-margin'])
            else:
                return dict(TIER_CONFIGS['1k'])

    # 3. Unknown resolution: default to Veo config
    # Veo uses consistent 96px margins at all confirmed resolutions
    return dict(VEO_WATERMARK)


def calculate_watermark_position(width, height, config=None):
    """Calculate watermark position. Returns {x, y, width, height}."""
    if config is None:
        config = detect_watermark_config(width, height)
    logo_size = config['logoSize']
    return {
        'x': width - config['marginRight'] - logo_size,
        'y': height - config['marginBottom'] - logo_size,
        'width': logo_size,
        'height': logo_size,
    }


def search_watermark_position(frame, logo_size, alpha_map_2d, search_margin=200):
    """
    Auto-detect watermark position by scanning bottom-right area
    for best correlation with the known alpha map.
    Uses normalized cross-correlation.

    Args:
        frame: (H, W, 3) uint8 - first video frame
        logo_size: 48 or 96
        alpha_map_2d: (logo_size, logo_size) float32 alpha map
        search_margin: pixels to search from bottom-right corner

    Returns: {x, y, width, height} or None
    """
    h, w = frame.shape[:2]
    brightness = frame.astype(np.float32).max(axis=2) / 255.0

    # Normalize alpha map once
    am = alpha_map_2d.flatten()
    am_norm = (am - am.mean()) / (am.std() + 1e-8)

    # Search bottom-right area
    sx_start = max(0, w - search_margin - logo_size)
    sy_start = max(0, h - search_margin - logo_size)
    sx_end = w - logo_size
    sy_end = h - logo_size
    if sx_start > sx_end or sy_start > sy_end:
        return None

    best_score = -1.0
    best_pos = None
    stride = max(1, logo_size // 4)

    for sy in range(sy_start, sy_end + 1, stride):
        for sx in range(sx_start, sx_end + 1, stride):
            region = brightness[sy:sy + logo_size, sx:sx + logo_size]
            if region.shape != (logo_size, logo_size):
                continue
            r = region.flatten()
            r_norm = (r - r.mean()) / (r.std() + 1e-8)
            score = float(np.dot(am_norm, r_norm)) / logo_size
            if score > best_score:
                best_score = score
                best_pos = (sx, sy)

    if best_score > 0.05:
        return {
            'x': best_pos[0],
            'y': best_pos[1],
            'width': logo_size,
            'height': logo_size,
        }
    return None
