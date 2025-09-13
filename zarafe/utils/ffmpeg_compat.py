"""FFmpeg compatibility module for glassesTools."""

import os
import subprocess
from pathlib import Path
from typing import Any


def patch_ffmpeg_module() -> None:
    """Patch the ffmpeg module to provide the add_to_path method."""
    try:
        import ffmpeg

        # Check if add_to_path already exists
        if hasattr(ffmpeg, "add_to_path"):
            return

        # Get the ffmpeg executable path
        try:
            from ffmpeg.executable import get_executable_path

            ffmpeg_tuple = get_executable_path()
            ffmpeg_path = str(ffmpeg_tuple[0]) if ffmpeg_tuple[0] is not None else None
        except Exception:
            ffmpeg_path = None

        def add_to_path() -> None:
            """Add ffmpeg binaries directly to PATH."""
            if ffmpeg_path:
                ffmpeg_dir = str(Path(ffmpeg_path).parent)
                if ffmpeg_dir not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

        def init() -> None:
            """Initialize the module."""

        def run_as_ffmpeg(*args: Any) -> subprocess.CompletedProcess[bytes]:
            """Call ffmpeg directly."""
            if ffmpeg_path:
                return subprocess.run([ffmpeg_path, *args], check=False)
            raise RuntimeError("FFmpeg binary not found")

        # Add missing methods to the ffmpeg module
        ffmpeg.add_to_path = add_to_path
        ffmpeg.init = init
        ffmpeg.run_as_ffmpeg = run_as_ffmpeg
        ffmpeg.FFMPEG_PATH = ffmpeg_path

    except ImportError:
        # If ffmpeg module doesn't exist, we might be in PyInstaller
        pass


# Apply the patch when this module is imported
patch_ffmpeg_module()
