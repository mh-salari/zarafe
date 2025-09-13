"""PyInstaller hook for ffmpeg-binaries package."""

from PyInstaller.utils.hooks import collect_data_files, get_package_paths

# Collect all data files from the ffmpeg package
datas = collect_data_files("ffmpeg")

# Get package path to include the package structure
package_dir, package_path = get_package_paths("ffmpeg")

# Include the executable and internals directories
datas += [(package_path, "ffmpeg")]
