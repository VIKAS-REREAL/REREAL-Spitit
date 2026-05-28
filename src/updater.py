"""
REREAL - Spitit: GitHub Releases update checker.
"""

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
    Check GitHub Releases API for a newer version.
    
    Returns:
        dict with keys:
            - available (bool): True if update is available
            - version (str): Latest version string
            - url (str): URL to the release page
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
        latest = data["tag_name"].lstrip("v")
        url = data["html_url"]
        available = _version_gt(latest, CURRENT_VERSION)
        return {"available": available, "version": latest, "url": url}
    except Exception:
        return {"available": False, "version": CURRENT_VERSION, "url": ""}
