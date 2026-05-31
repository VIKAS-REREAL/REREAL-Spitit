"""
REREAL - Spitit: GitHub Releases update checker & parser.
"""

import re

REPO = "VIKAS-REREAL/REREAL-Spitit"
CURRENT_VERSION = "2.0.0"


def _version_tuple(v: str) -> tuple:
    """Convert version string to comparable tuple."""
    parts = v.lstrip("v").split(".")
    result = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            result.append(0)
    return tuple(result)


def _version_gt(a: str, b: str) -> bool:
    """Return True if version a > version b."""
    return _version_tuple(a) > _version_tuple(b)


def check_for_update() -> dict:
    """
    Check GitHub Releases API for a newer version by parsing release assets.
    
    Returns:
        dict with keys:
            - available (bool): True if update is available
            - version (str): Latest version string (e.g. 2.0.1)
            - url (str): URL to the release page
            - setup_url (str): URL to download the setup installer
            - portable_url (str): URL to download the portable executable
    """
    try:
        import httpx

        r = httpx.get(
            f"https://api.github.com/repos/{REPO}/releases/latest",
            timeout=5,
            headers={"User-Agent": "REREAL-Spitit"},
        )
        r.raise_for_status()
        data = r.json()
        
        url = data.get("html_url", "")
        tag_version = data.get("tag_name", "").lstrip("v")
        
        # Parse assets to extract direct URLs and look for the version in the setup name
        version = None
        setup_url = ""
        portable_url = ""
        
        for asset in data.get("assets", []):
            name = asset.get("name", "")
            download_url = asset.get("browser_download_url", "")
            
            if "Setup" in name and name.endswith(".exe"):
                # E.g. REREAL-Spitit-Setup-2.0.0.exe -> 2.0.0
                match = re.search(r"Setup-(\d+\.\d+\.\d+(?:\.\d+)?)", name)
                if match:
                    version = match.group(1)
                setup_url = download_url
            elif name == "REREAL-Spitit.exe":
                portable_url = download_url
                
        # Fall back to tag name version if we couldn't parse it from the filename
        if not version or version == "latest":
            if tag_version and tag_version != "latest":
                version = tag_version
            else:
                version = CURRENT_VERSION
                
        available = _version_gt(version, CURRENT_VERSION)
        return {
            "available": available,
            "version": version,
            "url": url,
            "setup_url": setup_url,
            "portable_url": portable_url,
        }
    except Exception as e:
        print(f"[Updater] Error checking for updates: {e}")
        return {
            "available": False,
            "version": CURRENT_VERSION,
            "url": "",
            "setup_url": "",
            "portable_url": "",
        }
