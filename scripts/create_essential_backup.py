"""
Create a clean, essential backup zip of the repository.
Includes all source code, assets, scripts, configs, packaging definitions,
and documentation/context markdown files.
Excludes build artifacts, caches, and large compiled binaries.
"""

import os
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_ZIP = ROOT_DIR / "Spitit_essential_backup.zip"

EXCLUDED_DIR_NAMES = {
    ".git",
    "build",
    "dist",
    "dist_installer",
    "dist_msix",
    "__pycache__",
    "downloads",
}

EXCLUDED_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".exe",
    ".zip",
    ".tmp",
}

# Root level specific files to include
ROOT_FILES = {
    "SPITIT_V3_SPEC.md",
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "RELEASE_NOTES.md",
    "LICENSE",
    "pyproject.toml",
    "requirements.txt",
    "version.txt",
    "REREAL-Spitit.spec",
    "build-msix.ps1",
    "build-release.ps1",
    "toggle-maintenance.ps1",
    "test_launch.py",
    "test_pill.py",
    ".gitignore",
    ".gitattributes",
}

SUBDIRS_TO_SCAN = [
    "src",
    "assets",
    "scripts",
    "installer",
    "msix",
    "docs",
    "maintenance_template",
    ".github",
    "site_backup",
]

def should_include_file(rel_path: Path) -> bool:
    parts = rel_path.parts
    # Check directory exclusions
    for part in parts[:-1]:
        if part in EXCLUDED_DIR_NAMES:
            return False
    
    # Check extension exclusions
    if rel_path.suffix.lower() in EXCLUDED_EXTENSIONS:
        return False
        
    return True

def create_backup():
    print(f"Creating essential backup zip: {OUTPUT_ZIP.name}...")
    files_to_zip = []

    # 1. Root files
    for filename in sorted(ROOT_FILES):
        p = ROOT_DIR / filename
        if p.is_file():
            files_to_zip.append(p)

    # 2. Subdirectories
    for subdir_name in SUBDIRS_TO_SCAN:
        subdir = ROOT_DIR / subdir_name
        if not subdir.is_dir():
            continue
        for root, dirs, files in os.walk(subdir):
            # Prune excluded dirs
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIR_NAMES]
            for file in sorted(files):
                file_path = Path(root) / file
                rel_path = file_path.relative_to(ROOT_DIR)
                if should_include_file(rel_path):
                    files_to_zip.append(file_path)

    # Deduplicate while preserving order
    seen = set()
    unique_files = []
    for f in files_to_zip:
        rel = f.relative_to(ROOT_DIR).as_posix()
        if rel not in seen:
            seen.add(rel)
            unique_files.append(f)

    # Write zip file
    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()

    with zipfile.ZipFile(OUTPUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for file_path in unique_files:
            arcname = file_path.relative_to(ROOT_DIR).as_posix()
            zf.write(file_path, arcname=arcname)
            print(f"  + {arcname}")

    stat = OUTPUT_ZIP.stat()
    size_mb = stat.st_size / (1024 * 1024)
    print(f"\nDone! Successfully created {OUTPUT_ZIP.name}")
    print(f"Total files archived: {len(unique_files)}")
    print(f"Archive size: {size_mb:.2f} MB ({stat.st_size:,} bytes)")

if __name__ == "__main__":
    create_backup()
