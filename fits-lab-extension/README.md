# fits-lab-extension

View FITS images inside JupyterLab. Two ways to use it:

- **File browser:** double-click any `.fits` / `.fit` file and it opens in an
  interactive viewer tab.
- **Inline in a notebook:**

  ```python
  from fits_lab_extension import show
  show("data/some_image.fits")
  ```

Both are powered by the [`simple-fits-viewer`](https://github.com/ppp-one/simple-fits-viewer)
rendering library (zoom/pan, header table, line profiles, FWHM, WCS grid),
which is bundled in `fits_lab_extension/static/`.

## How it works

- A small **Jupyter Server extension** serves the bundled viewer assets at
  `<base_url>/fits-lab-extension/static/`.
- The **labextension** registers the `.fits` / `.fit` file type and opens each
  file in an iframe pointing at that viewer.
- The viewer fetches the file bytes from Jupyter's `/files/` endpoint.

The viewer runs in an iframe so its CSS/DOM are fully isolated from JupyterLab.

## Build & install

Requires Node.js (for the labextension build) and JupyterLab 4.

```bash
cd fits-lab-extension
pip install .
```

`pip install` triggers the JupyterLab build (via `hatch-jupyter-builder`), then
installs the prebuilt labextension and the server extension. The server
extension is auto-enabled via `jupyter-config/server-config/`.

Verify:

```bash
jupyter labextension list      # should list fits-lab-extension
jupyter server extension list  # should list fits_lab_extension (enabled)
```

## Development

```bash
jlpm install
jlpm build
jupyter labextension develop . --overwrite
jupyter server extension enable fits_lab_extension
jlpm watch   # rebuild on change
```

## Updating the viewer library

The viewer assets in `fits_lab_extension/static/` are copied verbatim from
`simple-fits-viewer` (`lib/*.js`, `d3.v7.min.js`, `style.css`). To update,
re-copy those files. `viewer.html` is specific to this extension (it loads a
file from a `?path=` query parameter).
