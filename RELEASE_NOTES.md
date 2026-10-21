# REREAL - Spitit v2.0.3 — Certification Fixes & GitHub Actions Release CI/CD
 
🚀 **REREAL - Spitit v2.0.3** resolves Microsoft Store certification rejection issues (Policy 10.1.2.10 Functionality on Surface devices and Policy 11.16 Generative AI declaration guidance), introduces resilient windowed peak-RMS silence detection, clean modifier-free auto-pasting, and automated GitHub Actions release builds for Portable, Setup, and Store MSIX packages.

---

## 🌟 What's New in v2.0.3

### 🎤 Robust Dictation on Surface Laptops & All Microphones (Policy 10.1.2.10)
- **Resolved False-Positive Silence Rejections**: Surface Laptop 5 and modern ultrabooks utilize studio array microphones with lower digital gain margins. The previous hardcoded `silence_threshold = 0.01` with whole-buffer averaging caused valid speech to be dropped and displayed an error cross (`X`).
- **Windowed Peak RMS**: Speech detection now evaluates audio across 100ms windows, ensuring that pauses before or after speaking never dilute speech audio.
- **Graceful Error Recovery**: Muted microphones or silent inputs now gently hide the status pill rather than flashing an error state. Empty transcriptions no longer throw unhandled exceptions.
- **Audio Device Fallback**: Automatically falls back to the system default input device if a configured microphone index fails.

### 📋 Modifier-Clean Win32 Auto-Paste
- **Notepad Menu Collision Fix**: Replaced basic `keyboard.press_and_release("ctrl+v")` with a Win32 `keybd_event` sequence that releases any active modifier keys (`Alt`, `Shift`, `Win`) before simulating `Ctrl+V`. This prevents `Alt+V` from inadvertently opening Notepad's "View" menu instead of pasting text.
- **CJK Unicode Character Count**: Word/character counters in the floating pill and history accurately display character counts for Chinese, Japanese, and Korean.

### ⚙️ Automated GitHub Actions CI/CD Pipeline
- **One-Click Release Automation**: Added `.github/workflows/build.yml` which automatically builds and releases all 3 target artifacts on `windows-latest`:
  1. `REREAL-Spitit.exe` (Portable executable)
  2. `REREAL-Spitit-Setup-2.0.3.exe` (Inno Setup Installer)
  3. `REREAL-Spitit-2.0.3.msix` (Microsoft Store MSIX Package)
- **Artifacts Available Directly**: Every push and manual workflow trigger produces the ready-to-upload MSIX and installable executables under GitHub Actions run artifacts and GitHub Releases.

---

## 📥 Downloads & Assets (v2.0.3)

| File Name | Description | Size | Status |
|-----------|-------------|------|--------|
| `REREAL-Spitit-Setup-2.0.3.exe` | **Windows Installer** (Recommended) — Setup wizard with desktop & start shortcuts | ~70 MB | Verified |
| `REREAL-Spitit.exe` | **Portable Executable** — Single `.exe`, no installation required | ~69 MB | Verified |
| `REREAL-Spitit-2.0.3.msix` | **MSIX Package** — Microsoft Store & modern Windows 10/11 package | ~79 MB | Store Ready |

---

# REREAL - Spitit v2.0.2 — Launch Stability & Microsoft Store MSIX Packaging

🚀 **REREAL - Spitit v2.0.2** brings full Microsoft Store MSIX packaging support, crash-proof launch initialization under Windows 11 containers, modern borderless unplated taskbar/start menu icons, and unified release automation.

---

## 🌟 What's New in v2.0.2

### 🛡️ Crash-Proof Launch Under Windows 11 / MSIX Container
- **Resolved Policy 10.1.2.10 Launch Crash**: PyInstaller windowless builds (`console=False`) set `sys.stdout` and `sys.stderr` to `None`. Any unhandled stream access or print call in low-level hooks previously crashed the process silently inside MSIX containerized environments.
- **Log Stream Redirection**: Automatically redirects all output streams to `%LOCALAPPDATA%\REREAL_Spitit\spitit.log` with automatic 1 MB log rotation before any GUI code initializes.
- **Defensive Startup Safeguards**: System tray, global hotkeys, and floating status pill are wrapped in fault-tolerant handlers with full logging diagnostics.

### 🎨 Modern Borderless & Unplated Visual Assets
- **Square Backplate Elimination**: Windows 10/11 defaults to adding a solid colored square plate behind icons if unplated target assets are missing.
- **87 High-DPI Visual Assets**: Generated full target sizes (16px to 256px) of `_altform-unplated` and `_altform-lightunplated` PNGs, along with full DPI scale sets (`scale-100` through `scale-400`).
- **Clean System Integration**: Seamless transparent icon rendering across Windows Taskbar, Start Menu, Alt+Tab switcher, and Windows App Installer.

### 📦 Microsoft Store MSIX Packaging Pipeline
- **Automated Windows SDK Integration**: `build-msix.ps1` automatically searches for `MakePri.exe` to index visual assets into `resources.pri` and uses `MakeAppx.exe` to compile the official `.msix` package.
- **Unified Release Command**: Run `.\build-release.ps1 -Installer -MSIX` to build the Portable EXE, Inno Setup Installer, and MSIX package in one command.
- **Comprehensive Guide**: Added `docs/MSIX_PACKAGING.md` with step-by-step instructions for sideloading, local developer certificate signing, and Partner Center submission.

---

## 📥 Downloads & Assets (v2.0.2)

| File Name | Description | Size | Status |
|-----------|-------------|------|--------|
| `REREAL-Spitit-Setup-2.0.2.exe` | **Windows Installer** (Recommended) — Setup wizard with desktop & start shortcuts | ~70 MB | Verified |
| `REREAL-Spitit.exe` | **Portable Executable** — Single `.exe`, no installation required | ~69 MB | Verified |
| `REREAL-Spitit-2.0.2.msix` | **MSIX Package** — Microsoft Store & modern Windows 10/11 sideload package | ~79 MB | Verified |

---

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
