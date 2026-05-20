# 📁 Project Structure

This document provides an overview of the directory structure for the **Spit It** repository.

```text
Spit It/
├── .github/                # GitHub-specific configuration
│   ├── ISSUE_TEMPLATE/     # Templates for reporting bugs or features
│   └── workflows/          # GitHub Actions (e.g., automated release builds)
├── assets/                 # Static assets (icons, images)
│   ├── icon.png            # Application logo (source)
│   └── icon.ico            # Windows executable icon (generated)
├── docs/                   # Project documentation (empty or placeholder)
├── installer/              # Files related to the application installer
├── scripts/                # Utility scripts for development
│   └── build_icon.py       # Script to generate .ico from .png
├── CHANGELOG.md            # History of changes and versions
├── CONTRIBUTING.md         # Guidelines for contributing to the project
├── LICENSE                 # Project license (MIT/GPL)
├── README.md               # Main project documentation and overview
├── REREAL-Spitit.spec      # PyInstaller build configuration
├── build-release.ps1       # PowerShell script for local builds
├── config.json             # Application configuration (user-specific)
├── config.py               # Configuration management logic
├── hotkey.py               # Global hotkey handling
├── main.py                 # Main entry point and orchestration
├── paster.py               # Clipboard and keyboard pasting logic
├── pyproject.toml          # Python project metadata and tool config
├── recorder.py             # Audio recording and processing
├── requirements.txt        # Python dependencies
├── transcriber.py          # Groq Whisper API client logic
├── tray.py                 # System tray icon and menu
├── ui.py                   # Floating status pill and settings window
└── version.txt             # Version history tracking
```

## 📂 Key Directories

- **`.github/`**: Contains automation workflows. The `release.yml` workflow automatically builds and uploads the `.exe` to GitHub Releases when a version tag (e.g., `v1.0.0`) is pushed.
- **`assets/`**: Stores the visual identity of the app.
- **`scripts/`**: Houses helper scripts that aren't part of the core app logic.

## 📄 Core Modules

- **`main.py`**: The heartbeat of the app. It initializes all components and runs the main loop.
- **`ui.py`**: Manages the "Floating Status Pill" and the Settings window.
- **`recorder.py`**: Handles microphone input and streams audio to temporary WAV files.
- **`transcriber.py`**: Sends audio to Groq's high-speed Whisper API for transcription.
- **`hotkey.py`**: Hooks into Windows global keyboard events to trigger recording.
- **`tray.py`**: Provides the system tray interface for quick access and background management.
