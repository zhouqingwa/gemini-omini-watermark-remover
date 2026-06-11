"""
Veo/Omini Watermark Remover - Video I/O Pipeline

Handles video frame extraction, writing, and audio merging using ffmpeg.
"""
import cv2
import os
import subprocess
import tempfile
import platform
import shutil


class VideoPipeline:
    def __init__(self, video_path, output_path=None):
        self.video_path = os.path.abspath(video_path)
        self.video_name = os.path.splitext(os.path.basename(video_path))[0]

        if output_path is None:
            output_dir = os.path.dirname(self.video_path)
            self.output_path = os.path.join(
                output_dir, f"{self.video_name}_clean.mp4"
            )
        else:
            self.output_path = os.path.abspath(output_path)

        # Open video
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise IOError(f"Failed to open video: {video_path}")

        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.frame_size = (self.width, self.height)

        # Find ffmpeg
        self.ffmpeg_path = self._find_ffmpeg()

        # Temp file for video without audio
        self.temp_file = tempfile.NamedTemporaryFile(
            suffix='.mp4', delete=False
        )
        self.temp_path = self.temp_file.name

        # Video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(
            self.temp_path, fourcc, self.fps, self.frame_size
        )

    def _find_ffmpeg(self):
        """Find ffmpeg executable in PATH or common locations."""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["where", "ffmpeg"], capture_output=True, text=True
                )
            else:
                result = subprocess.run(
                    ["which", "ffmpeg"], capture_output=True, text=True
                )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except Exception:
            pass
        return "ffmpeg"

    def write_frame(self, frame):
        """Write a single frame to the output video."""
        self.writer.write(frame)

    def close(self):
        """Release resources."""
        if hasattr(self, 'cap') and self.cap is not None:
            self.cap.release()
        if hasattr(self, 'writer') and self.writer is not None:
            self.writer.release()

    def merge_audio(self):
        """
        Merge original audio into the cleaned video using ffmpeg.
        Returns True if successful.
        """
        self.close()

        temp_audio = tempfile.NamedTemporaryFile(suffix='.aac', delete=False)
        temp_audio_path = temp_audio.name
        temp_audio.close()

        use_shell = os.name == "nt"

        try:
            extract_cmd = [
                self.ffmpeg_path, "-y",
                "-i", self.video_path,
                "-acodec", "copy",
                "-vn", "-loglevel", "error",
                temp_audio_path
            ]
            subprocess.run(
                extract_cmd, check=True,
                stdin=open(os.devnull), shell=use_shell
            )
        except Exception:
            try:
                os.unlink(temp_audio_path)
            except Exception:
                pass
            try:
                shutil.copy2(self.temp_path, self.output_path)
            except Exception:
                pass
            return False

        try:
            merge_cmd = [
                self.ffmpeg_path, "-y",
                "-i", self.temp_path,
                "-i", temp_audio_path,
                "-vcodec", "libx264",
                "-acodec", "copy",
                "-loglevel", "error",
                self.output_path
            ]
            subprocess.run(
                merge_cmd, check=True,
                stdin=open(os.devnull), shell=use_shell
            )
        except Exception:
            try:
                shutil.copy2(self.temp_path, self.output_path)
            except Exception:
                pass
            return False
        finally:
            try:
                os.unlink(temp_audio_path)
            except Exception:
                pass

        return True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        if os.path.exists(self.temp_path):
            try:
                os.unlink(self.temp_path)
            except Exception:
                pass
