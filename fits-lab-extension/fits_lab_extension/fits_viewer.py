"""Inline FITS viewer helper for notebooks.

Usage in a notebook cell::

    from fits_lab_extension import show
    show("data/some_image.fits")

This renders the interactive FITS viewer in the cell output, inside an isolated
iframe pointing at the viewer served by the Jupyter Server extension.
"""

import os
from urllib.parse import quote


def _server_relative_path(path):
    """Return ``path`` relative to the Jupyter server root (the user's home).

    Jupyter serves files at ``/files/<path-relative-to-server-root>``. In this
    deployment the server root is the user's home directory, so we make the
    given path relative to it.
    """
    abspath = os.path.abspath(os.path.expanduser(str(path)))
    root = os.path.abspath(os.path.expanduser("~"))
    rel = os.path.relpath(abspath, root)
    # Normalise Windows separators to URL separators.
    return rel.replace(os.sep, "/")


def show(path, width="100%", height=600):
    """Display an interactive FITS viewer for ``path`` in the notebook output.

    Parameters
    ----------
    path : str
        Path to the ``.fits`` / ``.fit`` file (relative to the notebook or
        absolute, anywhere under the server root).
    width : str or int
        Width of the viewer iframe (CSS value or pixels). Defaults to ``"100%"``.
    height : str or int
        Height of the viewer iframe (CSS value or pixels). Defaults to ``600``.
    """
    from IPython.display import HTML, display

    rel = _server_relative_path(path)
    # Resolve the server base URL. Under JupyterHub each single-user server runs
    # behind a prefix (e.g. /user/<name>/), exposed via JUPYTERHUB_SERVICE_PREFIX.
    base = os.environ.get("JUPYTERHUB_SERVICE_PREFIX", "/").rstrip("/")
    src = base + "/fits-lab-extension/static/viewer.html?path=" + quote(rel)

    w = width if isinstance(width, str) else "{}px".format(width)
    h = height if isinstance(height, str) else "{}px".format(height)

    html = (
        '<iframe src="{src}" '
        'style="width:{w};height:{h};border:1px solid rgba(128,128,128,0.3);'
        'border-radius:4px;" '
        'sandbox="allow-scripts allow-same-origin allow-popups"></iframe>'
    ).format(src=src, w=w, h=h)

    display(HTML(html))
