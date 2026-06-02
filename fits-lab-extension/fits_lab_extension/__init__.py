"""FITS image viewer for JupyterLab.

Provides two ways to view FITS files inside a JupyterLab instance:

* ``fits_viewer.show("image.fits")`` — render the interactive viewer inline in a
  notebook output cell.
* A file-browser labextension that opens ``.fits`` / ``.fit`` files on double click.

Both are powered by the same self-contained viewer assets shipped in ``static/``
and served by a small Jupyter Server extension.
"""

from .fits_viewer import show
from .handlers import setup_handlers

__version__ = "0.1.0"

__all__ = ["show", "__version__"]


def _jupyter_labextension_paths():
    # Maps the built labextension assets into share/jupyter/labextensions.
    return [{"src": "labextension", "dest": "fits-lab-extension"}]


def _jupyter_server_extension_points():
    return [{"module": "fits_lab_extension"}]


def _load_jupyter_server_extension(server_app):
    """Register the static asset handler with the Jupyter Server."""
    setup_handlers(server_app.web_app)
    server_app.log.info("Registered fits_lab_extension server extension")


# Compatibility alias for older Jupyter Server versions.
load_jupyter_server_extension = _load_jupyter_server_extension
