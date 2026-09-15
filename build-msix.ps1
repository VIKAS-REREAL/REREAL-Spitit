param(
    [switch]$Sign,
    [string]$Publisher = "",
    [switch]$SkipPyInstaller
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  REREAL - Spitit MSIX Packaging Script" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

$manifestPath = "msix\AppxManifest.xml"
if (Test-Path $manifestPath) {
    [xml]$manifestXml = Get-Content $manifestPath
    $manifestVersion = $manifestXml.Package.Identity.Version
    if ($manifestVersion -match '^(\d+\.\d+\.\d+)\.0$') {
        $version = $Matches[1]
    } else {
        $version = $manifestVersion
    }
    if (-not $Publisher) {
        $Publisher = $manifestXml.Package.Identity.Publisher
    }
} else {
    $version = "2.0.2"
    if (-not $Publisher) { $Publisher = "CN=REREAL" }
}

$exePath = "dist\REREAL-Spitit.exe"
$msixOutputDir = "dist_msix"
$layoutDir = "$msixOutputDir\layout"
$packageFile = "$msixOutputDir\REREAL-Spitit-$version.msix"

# [Step 1] Verify or build PyInstaller executable
if (-not (Test-Path $exePath) -and -not $SkipPyInstaller) {
    Write-Host "[1/4] Portable executable missing. Running PyInstaller..." -ForegroundColor Cyan
    python -m PyInstaller --noconfirm REREAL-Spitit.spec
}

if (-not (Test-Path $exePath)) {
    throw "Build failed: Missing $exePath. Run PyInstaller first or remove -SkipPyInstaller."
}
Write-Host "[1/4] Found executable: $exePath" -ForegroundColor Green

# [Step 2] Generate Visual Assets
Write-Host "[2/4] Generating visual assets for MSIX..." -ForegroundColor Cyan
python scripts/generate_msix_assets.py

# [Step 3] Prepare Layout Directory
Write-Host "[3/4] Assembling MSIX layout directory..." -ForegroundColor Cyan
if (Test-Path $layoutDir) {
    Remove-Item -Recurse -Force $layoutDir
}
New-Item -ItemType Directory -Path "$layoutDir\Assets" -Force | Out-Null

Copy-Item $exePath -Destination "$layoutDir\REREAL-Spitit.exe" -Force
Copy-Item "msix\AppxManifest.xml" -Destination "$layoutDir\AppxManifest.xml" -Force
Copy-Item "msix\Assets\*" -Destination "$layoutDir\Assets\" -Recurse -Force

Write-Host "  Layout ready at: $layoutDir" -ForegroundColor Green

# [Step 4] Locate MakeAppx.exe and Package
Write-Host "[4/4] Searching for Windows SDK MakeAppx.exe..." -ForegroundColor Cyan

$makeappx = $null
$makeappxCmd = Get-Command "makeappx.exe" -ErrorAction SilentlyContinue
if ($makeappxCmd) {
    $makeappx = $makeappxCmd.Path
} else {
    $searchPaths = @(
        "C:\Program Files (x86)\Windows Kits\10\bin\*\x64\makeappx.exe",
        "C:\Program Files\Windows Kits\10\bin\*\x64\makeappx.exe",
        "C:\Program Files (x86)\Microsoft Visual Studio\*\*\MSBuild\Current\Bin\makeappx.exe",
        "${env:ProgramFiles(x86)}\Windows Kits\10\App Certification Kit\makeappx.exe"
    )
    foreach ($p in $searchPaths) {
        $found = Get-ChildItem -Path $p -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) {
            $makeappx = $found.FullName
            break
        }
    }
}

if (-not $makeappx) {
    Write-Host ""
    Write-Host "[!] MakeAppx.exe not found on PATH or in Windows Kits." -ForegroundColor Red
    Write-Host "    Install the Windows SDK via winget:" -ForegroundColor Yellow
    Write-Host "    winget install Microsoft.WindowsSDK.10.0.18362" -ForegroundColor White
    throw "Windows SDK (MakeAppx.exe) is required to build a valid Microsoft Store MSIX package."
}

Write-Host "  Using MakeAppx: $makeappx" -ForegroundColor Green

    # Locate MakePri in the same SDK bin folder
    $makepri = Join-Path (Split-Path $makeappx) "makepri.exe"
    if (Test-Path $makepri) {
        Write-Host "  Indexing visual assets via MakePri ($makepri)..." -ForegroundColor Cyan
        $priconfig = "$layoutDir\priconfig.xml"
        & $makepri createconfig /cf "$priconfig" /dq "lang-en-US" /pv 10.0.0 /o | Out-Null
        & $makepri new /pr "$layoutDir" /cf "$priconfig" /mn "$layoutDir\AppxManifest.xml" /of "$layoutDir\resources.pri" /o | Out-Null
        if (Test-Path $priconfig) { Remove-Item -Force $priconfig }
        Write-Host "  [OK] resources.pri generated with unplated asset index." -ForegroundColor Green
    }

    if (Test-Path $packageFile) {
        Remove-Item -Force $packageFile
    }

    Write-Host "  Packing MSIX..." -ForegroundColor Cyan
    & $makeappx pack /d "$layoutDir" /p "$packageFile" /o

if (-not (Test-Path $packageFile)) {
    throw "MSIX packing failed: Output file not created."
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  MSIX Package Created Successfully!" -ForegroundColor Green
Write-Host "  Location: $packageFile" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Optional Self-Signing for Local Testing
if ($Sign) {
    Write-Host ""
    Write-Host "[Optional] Signing MSIX package for local testing..." -ForegroundColor Cyan

    $signtool = $null
    $signtoolCmd = Get-Command "signtool.exe" -ErrorAction SilentlyContinue
    if ($signtoolCmd) {
        $signtool = $signtoolCmd.Path
    } else {
        $searchSignPaths = @(
            "C:\Program Files (x86)\Windows Kits\10\bin\*\x64\signtool.exe",
            "C:\Program Files\Windows Kits\10\bin\*\x64\signtool.exe"
        )
        foreach ($sp in $searchSignPaths) {
            $foundSign = Get-ChildItem -Path $sp -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($foundSign) {
                $signtool = $foundSign.FullName
                break
            }
        }
    }

    if ($signtool) {
        $certSubject = $Publisher
        $cert = Get-ChildItem Cert:\CurrentUser\My | Where-Object { $_.Subject -eq $certSubject } | Select-Object -First 1
        if (-not $cert) {
            Write-Host "  Creating self-signed developer certificate ($certSubject)..." -ForegroundColor Cyan
            $cert = New-SelfSignedCertificate -Type Custom -Subject $certSubject -KeyUsage DigitalSignature -FriendlyName "REREAL Spitit Dev Certificate" -CertStoreLocation "Cert:\CurrentUser\My" -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3")
        }
        & $signtool sign /fd SHA256 /sha1 $cert.Thumbprint "$packageFile"
        $certPath = "$msixOutputDir\REREAL-Spitit-DevCert.cer"
        Export-Certificate -Cert $cert -FilePath $certPath -Force | Out-Null
        Write-Host "  [OK] Package signed with test certificate ($certSubject)." -ForegroundColor Green
        Write-Host "  [Note] To install/double-click locally on this PC, trust the certificate once in PowerShell (Admin):" -ForegroundColor Cyan
        Write-Host "         Import-Certificate -FilePath `"$certPath`" -CertStoreLocation Cert:\LocalMachine\Root" -ForegroundColor White
    } else {
        Write-Host "  [!] Signtool.exe not found. Package left unsigned (ready for Microsoft Partner Center Store upload)." -ForegroundColor Yellow
    }
}
