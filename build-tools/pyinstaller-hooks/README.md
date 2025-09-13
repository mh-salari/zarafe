# PyInstaller Build Tools

This directory contains custom PyInstaller hooks and build configuration for creating macOS application bundles.

## Build Commands

### Create macOS Application Bundle
```bash
uv run pyinstaller --onedir --windowed --name Zarafe --icon=resources/app_icon.icns --add-data "resources:resources" --additional-hooks-dir build-tools/pyinstaller-hooks --runtime-hook build-tools/pyinstaller-hooks/pyi_rth_ffmpeg.py main.py
```

**Note**: This requires the custom PyInstaller hook files:
- `hook-ffmpeg.py` - Collects ffmpeg package data files
- `pyi_rth_ffmpeg.py` - Runtime hook that creates the ffmpeg module with add_to_path functionality

### Test the Built Application
```bash
./dist/Zarafe.app/Contents/MacOS/Zarafe
```

## Files in this directory

- **hook-ffmpeg.py**: Custom PyInstaller hook that collects data files from the ffmpeg-binaries package
- **pyi_rth_ffmpeg.py**: Runtime hook that creates a mock ffmpeg module with the required `add_to_path()` method for glassesTools compatibility
- **README.md**: This documentation file

## How it works

The ffmpeg-binaries package used by glassesTools is missing its `__init__.py` file and the required API methods. Our custom hooks solve this by:

1. **hook-ffmpeg.py**: Ensures all ffmpeg package data files are included in the bundle
2. **pyi_rth_ffmpeg.py**: Creates a runtime shim that provides the missing `add_to_path()` method that glassesTools expects

This approach allows the application to work both in development (via the compatibility module in `zarafe/utils/ffmpeg_compat.py`) and in the bundled PyInstaller environment.