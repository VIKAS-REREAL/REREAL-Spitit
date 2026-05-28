# Changelog

All notable changes to REREAL - Spitit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
