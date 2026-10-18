# Microsoft Store MSIX Packaging Guide for REREAL - Spitit

This guide details how to build, test, and distribute **REREAL - Spitit** as a Microsoft Store-ready **MSIX** package.

---

## 📦 Package Output Locations

When you build the application, output files are placed in dedicated `dist` directories:

| Package Type | File Path | Build Command | Description |
| :--- | :--- | :--- | :--- |
| **MSIX Package** | `dist_msix\REREAL-Spitit-2.0.2.msix` | `.\build-msix.ps1` | Official Microsoft Store / Sideloading MSIX package |
| **MSIX Layout** | `dist_msix\layout\` | `.\build-msix.ps1` | Raw unpacked MSIX directory containing `REREAL-Spitit.exe`, `AppxManifest.xml`, and `Assets\` |
| **Portable Executable** | `dist\REREAL-Spitit.exe` | `.\build-release.ps1` | Single standalone `.exe` (no installation required) |
| **Inno Setup Installer** | `dist_installer\REREAL-Spitit-Setup-2.0.2.exe` | `.\build-release.ps1 -Installer` | Traditional Windows installer wizard |

---

## 🚀 How to Build the MSIX Package

### Option 1: Standalone MSIX Build
Run the dedicated MSIX build script from PowerShell:

```powershell
.\build-msix.ps1
```

### Option 2: Full Unified Release Build
To build the Portable EXE, Inno Setup Installer, and MSIX Package all in a single run:

```powershell
.\build-release.ps1 -Installer -MSIX
```

---

## 🛠️ Prerequisites & Build Pipeline

1. **Python Dependencies**:
   Install required Python dependencies:
   ```cmd
   pip install -r requirements.txt
   pip install pyinstaller Pillow
   ```
2. **Windows SDK (`MakeAppx.exe` and `MakePri.exe`)**:
   - `MakeAppx.exe` and `MakePri.exe` are part of the free **Windows SDK**.
   - `build-msix.ps1` automatically detects them, generates `resources.pri` with modern unplated taskbar/start menu assets, and packs `dist_msix\REREAL-Spitit-2.0.2.msix`.
   - Install the Windows SDK via `winget`:
     ```powershell
     winget install Microsoft.WindowsSDK.10.0.18362
     ```

---

## 🧪 Local Testing & Sideloading

To test the MSIX package on your local computer before publishing to the Microsoft Store, pass the `-Sign` flag to `build-msix.ps1`:

```powershell
.\build-msix.ps1 -Sign
```

This will automatically:
1. Create/use a self-signed developer certificate matching the manifest identity.
2. Sign the `.msix` package with `signtool.exe`.
3. Export the certificate to `dist_msix\REREAL-Spitit-DevCert.cer`.

To install and double-click locally without certificate errors, trust the certificate once in PowerShell (Administrator):
```powershell
Import-Certificate -FilePath "dist_msix\REREAL-Spitit-DevCert.cer" -CertStoreLocation Cert:\LocalMachine\Root
```

---

## 🏪 Microsoft Store Publishing (Partner Center)

For store submission:
1. Log into [Microsoft Partner Center](https://partner.microsoft.com/dashboard).
2. Create or reserve your app name **REREAL - Spitit**.
3. Copy your Publisher ID (e.g., `CN=12345678-ABCD-...`) and Identity Name from Partner Center into `msix/AppxManifest.xml`:
   ```xml
   <Identity
     Name="YOUR-PARTNER-CENTER-APP-ID"
     Publisher="CN=YOUR-PUBLISHER-ID"
     Version="2.0.2.0"
     ProcessorArchitecture="x64" />
   ```
4. Run `.\build-msix.ps1` to produce the `.msix` package.
5. Upload `dist_msix\REREAL-Spitit-2.0.2.msix` directly to Partner Center. Microsoft Store automatically signs the package upon approval.
