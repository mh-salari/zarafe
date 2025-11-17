"""PyInstaller hook for projectaria_tools package.

This hook ensures that the compiled C++ extensions (_core_pybinds, etc.)
are properly collected during the build process.

We exclude ffmpeg libraries (libavcodec, libavformat, libavutil, etc.) because
they conflict with cv2's ffmpeg libraries. Both packages will use cv2's version.
"""

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

# Collect all dynamic libraries (compiled extensions) from projectaria_tools
all_binaries = collect_dynamic_libs("projectaria_tools")

# Filter out ffmpeg libraries to avoid conflicts with cv2's ffmpeg
# Keep only the projectaria_tools-specific binaries (like _core_pybinds.so)
ffmpeg_libs = ["libavcodec", "libavformat", "libavutil", "libswscale", "libswresample", "libavfilter", "libavdevice"]
binaries = [(dest, src) for dest, src in all_binaries if not any(lib in src for lib in ffmpeg_libs)]

# Collect any data files that might be needed
datas = collect_data_files("projectaria_tools")

# Collect all submodules
hiddenimports = collect_submodules("projectaria_tools")

# Explicitly add _core_pybinds which is the compiled extension
hiddenimports += [
    "_core_pybinds",
]
