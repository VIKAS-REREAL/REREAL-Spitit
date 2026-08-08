# REREAL - Spitit v2.0.1 — Settings Redesign & High-DPI Windows Branding

🚀 **REREAL - Spitit v2.0.1** introduces a major UI/UX redesign of the Settings window, full multi-resolution high-DPI Windows icon branding, live microphone level metering, and enhanced Windows installer upgrade rules.

---

## 🌟 What's New in v2.0.1

### 🎨 Modern 2-Pane Settings UI (720×640)
- **Sidebar Navigation**: Clean 5-tab vertical navigation (`General`, `Dictation`, `Microphone`, `Output`, `History`) with active yellow accent left-border indicators.
- **Full Screen & Maximization**: Completely resizable and maximizable layout to fit any screen resolution smoothly.
- **Persistent Save Footer**: Bottom bar with `SAVE SETTINGS` button and real-time unsaved changes indicator (`● Unsaved changes`).
- **Safe History Clear Popover**: Safe confirmation modal dialog before clearing transcription history log.

### 🎙️ Live Microphone Input Testing
- **Real-Time RMS Volume Meter**: Test your active microphone input directly inside **Microphone Settings** with live visual level bars and silence threshold adjustments.

### 🖥️ Windows System & Executable Branding
- **Win32 `WM_SETICON` & AppUserModelID**: Native Win32 process model integration ensuring crisp icon rendering on Windows Titlebars, Windows Taskbar, and Task Manager.
- **8-Frame Multi-Resolution ICO**: Embedded uncompressed 32-bit BMP icon frames (`16x16`, `24x24`, `32x32`, `48x48`, `64x64`, `96x96`, `128x128`, `256x256`) for high-DPI Windows Explorer rendering.

### 📦 Enhanced Inno Setup Windows Installer
- **Auto-Detect & Upgrade**: Automatically detects existing installations and closes active instances (`CloseApplications=force`) to update binaries cleanly without locked-file errors.
- **Folder Selection**: Full directory browser wizard with Start Menu and Desktop shortcuts.

---

## 📥 Downloads & Assets

| File Name | Description | Size | SHA256 Checksum |
|-----------|-------------|------|-----------------|
| `REREAL-Spitit-Setup-2.0.1.exe` | **Windows Installer** (Recommended) — Setup wizard with shortcuts | ~69 MB | Auto-verified |
| `REREAL-Spitit.exe` | **Portable Executable** — Single `.exe`, no installation required | ~68 MB | Auto-verified |

---

## 🛠️ Installation & Setup
1. Download **`REREAL-Spitit-Setup-2.0.1.exe`** (Installer) or **`REREAL-Spitit.exe`** (Portable).
2. Launch the application.
3. Obtain your free Groq API key at [console.groq.com](https://console.groq.com) and paste it into **Settings → General**.
4. Press and hold your dictation hotkey (`Alt + LShift`) and speak. Release to paste transcriptions instantly into any active application.

---

**Full Commit Changelog**: https://github.com/VIKAS-REREAL/REREAL-Spitit/compare/v2.0.0...v2.0.1
