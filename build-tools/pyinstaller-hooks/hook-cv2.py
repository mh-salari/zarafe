"""PyInstaller hook for cv2 (OpenCV).

This ensures all OpenCV binaries and data files are properly collected.
"""

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

# Collect all cv2 submodules
hiddenimports = collect_submodules("cv2")

# Collect all dynamic libraries
binaries = collect_dynamic_libs("cv2")

# Collect data files
datas = collect_data_files("cv2", include_py_files=True)
