"""Serve the static FITS viewer assets from the Jupyter Server.

The assets in ``static/`` (viewer.html, d3, the FITS viewer library and styles)
are served at ``<base_url>/fits-lab-extension/static/...`` so that both the
inline ``show()`` helper and the labextension can load them in an iframe.

These are static front-end assets (a JavaScript library and HTML), not user
data. The FITS files themselves are fetched by the viewer through Jupyter's
own authenticated ``/files/`` endpoint.
"""

import os

from jupyter_server.utils import url_path_join
from tornado.web import StaticFileHandler

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


def setup_handlers(web_app):
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]
    route = url_path_join(base_url, "fits-lab-extension", "static", "(.*)")
    web_app.add_handlers(
        host_pattern,
        [(route, StaticFileHandler, {"path": STATIC_DIR})],
    )
