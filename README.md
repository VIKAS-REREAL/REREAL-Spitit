# REREAL · Spitit

**Voice to text** — Windows speech-to-text app powered by Groq Whisper.

Hold `Alt + Left Shift` to dictate, and the transcribed text is pasted into whatever app you're typing in.

## Features

- 🎙️ **Hold-to-talk** or **Toggle-to-talk** activation modes
- 🌐 Multi-language support (English, Hindi, Hinglish, and 10+ more)
- ⚡ Fast transcription via Groq Whisper API
- 🖥️ System tray integration — runs silently in the background
- 🎨 Premium dark-mode UI with animated status pill

## Download

Grab the latest `.exe` from the [Releases](../../releases) page.

## Build from Source

```powershell
# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build portable exe
.\build-release.ps1
```

The built exe will be at `dist/REREAL-Spitit.exe`.

## GitHub Actions

Every push to `main`/`master` automatically builds the `.exe` via GitHub Actions.  
To create a release with the exe attached, push a version tag:

```bash
git tag v1.1.0
git push origin v1.1.0
```

## License

MIT © REREAL
