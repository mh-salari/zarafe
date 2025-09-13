# Runtime hook for ffmpeg-binaries package

import os
import sys


def create_ffmpeg_module() -> None:
    """Create the ffmpeg module with add_to_path functionality."""

    # Create a mock ffmpeg module that provides the add_to_path function
    class FFmpegModule:
        def __init__(self) -> None:
            self.FFMPEG_PATH = None
            self._init_ffmpeg_path()

        def _init_ffmpeg_path(self) -> None:
            """Initialize the FFmpeg path."""
            # In PyInstaller, look for ffmpeg binary in the bundle
            if getattr(sys, "frozen", False):
                # Running in a bundle
                bundle_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
                possible_paths = [
                    os.path.join(bundle_dir, "ffmpeg", "binaries", "ffmpeg"),
                    os.path.join(bundle_dir, "ffmpeg", "ffmpeg"),
                    os.path.join(bundle_dir, "Frameworks", "ffmpeg", "binaries", "ffmpeg"),
                ]

                for path in possible_paths:
                    if os.path.isfile(path):
                        self.FFMPEG_PATH = path
                        break

        def add_to_path(self) -> None:
            """Add ffmpeg binaries to PATH."""
            if self.FFMPEG_PATH:
                ffmpeg_dir = os.path.dirname(self.FFMPEG_PATH)
                if ffmpeg_dir not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

        def init(self) -> None:
            """Initialize the module."""

        def run_as_ffmpeg(self, args):
            """Run ffmpeg with arguments."""
            import subprocess

            if self.FFMPEG_PATH:
                return subprocess.run([self.FFMPEG_PATH, *args], check=False)
            raise RuntimeError("FFmpeg binary not found")

    # Create the module instance
    ffmpeg_module = FFmpegModule()

    # Add it to sys.modules
    sys.modules["ffmpeg"] = ffmpeg_module


# Only run this if we're in a frozen environment and ffmpeg isn't already available
if getattr(sys, "frozen", False) and "ffmpeg" not in sys.modules:
    create_ffmpeg_module()
