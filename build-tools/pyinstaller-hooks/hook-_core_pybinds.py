"""PyInstaller hook for _core_pybinds compiled extension.

This ensures the compiled .so file is properly collected.
"""

from PyInstaller.utils.hooks import collect_dynamic_libs

# Collect the compiled extension
binaries = collect_dynamic_libs("_core_pybinds")
