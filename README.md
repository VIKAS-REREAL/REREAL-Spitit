# REREAL - Spitit

<p align="center">
  <img src="docs/icon.png" width="128" height="128" alt="REREAL - Spitit Logo">
</p>

<p align="center">
  <strong>Speak. Release. Done.</strong>
</p>

<p align="center">
  The fastest voice-to-text for Windows. Powered by Groq Whisper.<br>
  No login. No cloud. No telemetry. Just speak.
</p>

<p align="center">
  <a href="https://github.com/VIKAS-REREAL/REREAL-Spitit/releases/latest">
    <img src="https://img.shields.io/github/v/release/VIKAS-REREAL/REREAL-Spitit?style=flat-square&color=%23FFD505" alt="Release">
  </a>
  <a href="https://github.com/VIKAS-REREAL/REREAL-Spitit/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License">
  </a>
  <img src="https://img.shields.io/badge/platform-Windows%2010%2F11-0078D6?style=flat-square" alt="Platform">
</p>

---

## ✨ Features

- **⚡ Groq Whisper Speed** — Transcription in under a second
- **🌐 Hinglish Support** — Speak Hindi, type in Roman script
- **⌨️ Custom Hotkeys** — Hold-to-talk or toggle mode with any key combo
- **🎯 Smart Auto-Paste** — Types directly into your active text field
- **🔕 System Tray** — Lives quietly in your system tray
- **🔒 100% Private** — Your audio never touches our servers
- **🎨 Beautiful UI** — Dark glassmorphism design with animated status pill
- **📜 History** — Keep track of your recent transcriptions

## 📥 Download

| Type | Description | Link |
|------|-------------|------|
| **Installer** (recommended) | Full setup wizard with shortcuts | [Download](https://github.com/VIKAS-REREAL/REREAL-Spitit/releases/latest) |
| **Portable** | Single .exe, no install needed | [Download](https://github.com/VIKAS-REREAL/REREAL-Spitit/releases/latest) |

**System Requirements:** Windows 10/11 (64-bit), ~50MB disk, internet for transcription, a microphone.

## 🚀 Quick Start

1. **Get a Groq API key** — Free at [console.groq.com](https://console.groq.com)
2. **Install & launch** REREAL - Spitit
3. **Paste your API key** in Settings
4. **Hold `Alt + LShift`** and speak
5. **Release** — your speech appears where you're typing ✨

## 🎙️ Supported Languages

| Language | Code | Notes |
|----------|------|-------|
| Auto-detect | `auto` | Whisper auto-detects |
| English | `en` | — |
| Hinglish | `hinglish` | Hindi spoken → Roman script output |
| Hindi | `hi` | Devanagari output |
| Hindi + English Mix | `mixed_hi_en` | Preserves both scripts |
| Spanish, French, German, Italian, Portuguese, Russian, Japanese, Korean, Chinese | `es`, `fr`, `de`, `it`, `pt`, `ru`, `ja`, `ko`, `zh` | — |

## 🏗️ Build from Source

```powershell
# Clone
git clone https://github.com/VIKAS-REREAL/REREAL-Spitit.git
cd REREAL-Spitit

# Install dependencies
pip install -r requirements.txt

# Run in development
python src/main.py

# Build portable .exe
pip install pyinstaller
python scripts/build_icon.py
python scripts/generate_sound.py
python -m PyInstaller --noconfirm REREAL-Spitit.spec

# Build everything (portable + installer)
.\build-release.ps1 -Installer
```

## 📁 Project Structure

```
REREAL-Spitit/
├── src/
│   ├── main.py          # App entry point & orchestrator
│   ├── config.py        # Config management
│   ├── recorder.py      # Mic capture
│   ├── transcriber.py   # Groq Whisper client
│   ├── paster.py        # Output handling
│   ├── hotkey.py        # Global hotkey controller
│   ├── tray.py          # System tray
│   ├── updater.py       # Update checker
│   └── ui/
│       ├── theme.py     # Colors, fonts, constants
│       ├── pill.py      # Floating status pill
│       ├── settings.py  # Settings window
│       ├── splash.py    # Splash screen
│       └── components.py # Reusable widgets
├── scripts/
│   ├── build_icon.py    # Icon generator
│   └── generate_sound.py # Done sound generator
├── installer/           # Inno Setup files
├── docs/                # GitHub Pages website
└── ...
```

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

[MIT](LICENSE) — Free for personal use. Commercial use requires a separate license.

## 🔗 Links

- **Website:** [vikas-rereal.github.io/REREAL-Spitit](https://vikas-rereal.github.io/REREAL-Spitit/)
- **Groq:** [console.groq.com](https://console.groq.com)
- **Issues:** [Report a bug](https://github.com/VIKAS-REREAL/REREAL-Spitit/issues)

---

<p align="center">
  Built with ❤️ under <strong>REREAL</strong> — Where real meets unreal
</p>
