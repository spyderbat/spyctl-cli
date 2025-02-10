"""Handles API calls made to the PyPI API."""

from spyctl.api.primitives import get


def get_pypi_version():
    """
    Retrieves the latest version of the 'spyctl' package from PyPI.

    Returns:
        str: The latest version of the 'spyctl' package, or None if unable to
            retrieve.
    """
    url = "https://pypi.org/pypi/spyctl/json"
    try:
        resp = get(url, key=None, raise_notfound=True)
        version = resp.json().get("info", {}).get("version")
        if not version:
            return None
        return version
    except ValueError:
        pass
    return None
