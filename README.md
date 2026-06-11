<div align="center">

# Gemini/Omni Watermark Remover

**Mathematically remove visible watermarks from Gemini Omni AI-generated videos**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green.svg)](https://opencv.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

[English](#overview) | [中文](#概述)

</div>

---

## Overview

A specialized tool that removes the **visible watermark** from Gemini Omni AI-generated videos.

Unlike mainstream approaches that rely on lossy AI inpainting (LAMA, STTN), this tool uses **reverse alpha blending** — a deterministic mathematical formula — to achieve **lossless restoration**. The output quality is identical to the original video, with no blurring or artifacts.

**Supported resolutions (original Omni exports only):**
- ✅ 720×1280 (9:16 portrait)
- ✅ 1280×720 (16:9 landscape)

---

## Demo

**Before**

https://github.com/user-attachments/assets/41c2db2f-f422-4b72-ab01-934fa3ab58ef

**After**

https://github.com/user-attachments/assets/46805a2e-32dc-43f6-9ded-23408823c45a

---

## How It Works

Google overlays its watermark using alpha compositing:

```
watermarked = α × logo + (1 - α) × original
```

We reverse the formula:

```
original = (watermarked - α × logo) / (1 - α)
```

The `α` (opacity) and `logo` (watermark pattern) were calibrated from actual Omni video frames with pure black backgrounds.

| Parameter | Value |
|-----------|-------|
| Logo size | 48×48 |
| Right margin | 96px |
| Bottom margin | 96px |

---

## Quick Start

### Installation

```bash
pip install opencv-python numpy
```

### Usage

```bash
# Basic usage (output in same directory)
python main.py video.mp4

# Custom output path
python main.py video.mp4 -o output.mp4

# Auto-detect watermark position (recommended for first use)
python main.py video.mp4 --search

# Adjust removal strength
python main.py video.mp4 --alpha-gain 1.2
```

### Python API

```python
from core.reverse_alpha import load_alpha_map, remove_watermark_from_frame
from core.detector import detect_watermark_config, calculate_watermark_position
import cv2

cap = cv2.VideoCapture("video.mp4")
w, h = int(cap.get(3)), int(cap.get(4))

cfg = detect_watermark_config(w, h)
pos = calculate_watermark_position(w, h, cfg)
_, alpha = load_alpha_map(48)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    cleaned = remove_watermark_from_frame(frame, alpha, pos)
    # Process cleaned frame...
```

---

## Comparison

| | **This tool** | **AI Inpainting** (LAMA/STTN) | **Online Services** | **Video editors** |
|---|---|---|---|---|
| Method | Reverse alpha blending 🧮 | Deep learning inference 🧠 | Server-side processing ☁️ | Traditional algo |
| **Quality** | **Lossless** ✨ | Lossy, may blur | Lossy | Lossy |
| **Speed** | **~80-100fps** ⚡ | ~1-5fps (GPU needed) | Depends on network | ~10-30fps |
| **GPU** | Not required ✅ | Usually required ❌ | Not required | Optional |
| **Privacy** | Fully local 🔒 | Fully local 🔒 | Upload to server ⚠️ | Local |
| **Deps size** | ~50MB | ~5-10GB | Browser | ~200MB |
| **Cost** | Free 🆓 | Free | Quota limits | $30+ |

---

## Project Structure

```
gemini-omini-watermark-remover/
├── main.py                  # CLI entry point
├── config.py                # Configuration
├── requirements.txt         # Dependencies
├── core/
│   ├── reverse_alpha.py     # Core reverse alpha blending algorithm
│   ├── detector.py          # Watermark position detection
│   ├── video_pipeline.py    # Video I/O and audio merging
│   ├── alpha_48_veo.bin     # Calibrated alpha map
│   ├── alpha_48.bin         # Gemini image alpha map (fallback)
│   └── alpha_96.bin         # 96×96 alpha map (fallback)
```

---

## Caveats

- Removes the **visible watermark** only — invisible SynthID watermarks are not affected
- Only tested on original Omni exports (720×1280 and 1280×720); cropped or resized videos may not work correctly

---

## 概述

专门用于去除 Gemini Omni AI 生成视频中可见水印的工具。

与依赖 AI 修复（LAMA、STTN）的方案不同，本工具使用**逆向 Alpha 混合**数学公式，实现**无损还原**，无模糊、无伪影。视频全程本地处理，无需上传。

**支持分辨率（仅限 Omni 原始导出）：**
- ✅ 720×1280（9:16 竖屏）
- ✅ 1280×720（16:9 横屏）

```bash
pip install opencv-python numpy
python main.py your_video.mp4
```

---

## License

[MIT](LICENSE)
