# Changelog

All notable changes to REREAL - Spitit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.1] - 2026-08-08

### Added
- **2-Pane Sidebar Settings Layout**: Redesigned Settings window into a 2-pane 720×640 sidebar layout with 5 regrouped tabs (`General`, `Dictation`, `Microphone`, `Output`, `History`).
- **Live Mic RMS Level Meter**: Real-time microphone input volume meter in Microphone settings to test mic input live.
- **Direct Win32 WM_SETICON & AppUserModelID**: Set Windows Application User Model ID and Win32 `WM_SETICON` message injection to ensure branded icon rendering on window titlebars, Windows Taskbar, and Task Manager.
- **Full Screen & Maximizable Settings Window**: Removed artificial window bounds to allow Settings window to expand responsively across any screen resolution.
- **Inno Setup Upgrade Controls**: Added auto-close running instance (`CloseApplications=force`), directory selection browser, and clean overwrite/reinstall rules in installer.
- **Safe History Clear Popover**: Added confirmation popover dialog before clearing transcription history.

### Fixed
- Overrode CustomTkinter default blue icon timer (`CTkToplevel`) to preserve user brand icons.
- Fixed global Windows hotkey freezing and timeout bug.
- Synced version constants across configuration files.


## [2.0.0] - 2026-05-29

### Added
- Complete rebuild from scratch
- Groq Whisper API integration (`whisper-large-v3-turbo`)
- Hold-to-talk and toggle-to-talk modes
- Custom hotkey picker with validation
- Hinglish mode with LLM post-processing (Roman script output)
- Hindi + English mixed mode
- 14 language support (auto-detect, en, hi, hinglish, es, fr, de, it, pt, ru, ja, ko, zh)
- Floating status pill with animated waveform
- Dark glassmorphism UI design
- System tray with dynamic menu
- Transcription history (max 50 entries)
- Auto-paste into active text field
- Windows toast notifications
- Done sound feedback
- Silence detection
- API key connection test
- GitHub Releases update checker
- First-run setup wizard
- Inno Setup installer with EULA
- GitHub Pages website
- GitHub Actions CI/CD pipeline

### Technical
- Python 3.11 + CustomTkinter
- In-memory WAV buffer (no temp files)
- Lazy module imports for fast startup
- Cross-thread UI updates via `root.after()`
- Windows startup registry management
- PyInstaller single-file portable build
