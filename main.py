#!/usr/bin/env python3
"""
Gemini Omni Watermark Remover
Mathematically removes Omni video watermarks using reverse alpha blending.
No AI/ML inference needed - pure math, lossless, fast.
"""
import os
import sys
import time
import argparse
import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from core.reverse_alpha import load_alpha_map, remove_watermark_from_frame
from core.detector import (
    detect_watermark_config,
    calculate_watermark_position,
    search_watermark_position,
)
from core.video_pipeline import VideoPipeline


def process_video(video_path, output_path=None, alpha_gain=1.0, search=False):
    pipe = VideoPipeline(video_path, output_path)
    w, h = pipe.width, pipe.height
    print(f"Input: {video_path}")
    print(f"Resolution: {w}x{h}, FPS: {pipe.fps:.2f}, Frames: {pipe.frame_count}")

    # Detect watermark config
    wm_config = detect_watermark_config(w, h)
    position = calculate_watermark_position(w, h, wm_config)
    logo_size = wm_config['logoSize']
    print(f"Default watermark: {logo_size}x{logo_size} at ({position['x']}, {position['y']})")

    # Load alpha map
    _, alpha_map = load_alpha_map(logo_size)

    # Auto-search for watermark position (refines default)
    if search:
        print("Searching for watermark position...")
        ret, first_frame = pipe.cap.read()
        if ret:
            pipe.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            detected = search_watermark_position(first_frame, logo_size, alpha_map)
            if detected:
                print(f"  Found at ({detected['x']}, {detected['y']})")
                position = detected
            else:
                print(f"  Not found, using default position")

    print(f"Using watermark: {logo_size}x{logo_size} at ({position['x']}, {position['y']})")

    start_time = time.time()
    frame_idx = 0

    try:
        while True:
            ret, frame = pipe.cap.read()
            if not ret:
                break
            frame_idx += 1
            cleaned = remove_watermark_from_frame(
                frame, alpha_map, position, alpha_gain
            )
            pipe.write_frame(cleaned)
            if frame_idx % 100 == 0:
                elapsed = time.time() - start_time
                fps = frame_idx / elapsed if elapsed > 0 else 0
                print(f"  Processed {frame_idx}/{pipe.frame_count} frames ({fps:.1f} fps)")
    except KeyboardInterrupt:
        print(f"\nInterrupted at frame {frame_idx}")
    except Exception as e:
        print(f"Error at frame {frame_idx}: {e}")
        raise
    finally:
        pipe.close()

    elapsed = time.time() - start_time
    print(f"\nProcessed {frame_idx} frames in {elapsed:.1f}s")

    if pipe.ffmpeg_path:
        print("Merging audio...")
        pipe.merge_audio()

    if os.path.exists(pipe.output_path):
        print(f"Output: {pipe.output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Remove Gemini Omni watermark from videos "
                    "(reverse alpha blending, no AI needed)"
    )
    parser.add_argument("input", help="Input video file path")
    parser.add_argument("-o", "--output", help="Output video file path")
    parser.add_argument(
        "--alpha-gain", type=float, default=1.0,
        help="Alpha gain multiplier (default: 1.0)"
    )
    parser.add_argument(
        "--search", action="store_true",
        help="Auto-detect watermark position by scanning the frame"
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: file not found: {args.input}")
        sys.exit(1)

    process_video(args.input, args.output, args.alpha_gain, args.search)


if __name__ == "__main__":
    main()
