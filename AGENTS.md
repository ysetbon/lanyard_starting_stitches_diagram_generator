# OpenStrand Studio

A PyQt5 desktop GUI application for creating strand/knot diagrams. There is no
backend, server, or database — persistence is local `.json` project files. The
entry point is `python src/main.py`. See `README.md` and `PYTHON_FILES_OVERVIEW.md`
for product/feature details.

## Cursor Cloud specific instructions

### Python environment
- Dependencies live in a virtualenv at `$HOME/osenv` (the committed `.venv/` is a
  Windows venv and does not work on Linux — ignore it). Run everything with
  `"$HOME/osenv/bin/python"` (or `source "$HOME/osenv/bin/activate"`).
- The update script installs `requirements.txt` and then force-installs
  `PyQt5==5.15.11`. This override is required: the pinned `PyQt5==5.15.4` wheel is
  ABI-incompatible with the newer `PyQt5-sip` on Python 3.12 and **segfaults at
  import time** whenever a class uses multiple inheritance with a Qt base
  (e.g. `class LayerPanel(StrandDataClipboardMixin, QWidget)` in
  `src/layer_panel.py`). Do not downgrade PyQt5 back to 5.15.4 here.

### Running the GUI (headless VM)
- This is a GUI app, so it needs a display. A TigerVNC server runs on `DISPLAY=:1`
  (visible in the Desktop pane) — launch the app there for interactive/manual
  testing: `DISPLAY=:1 "$HOME/osenv/bin/python" src/main.py`.
- For non-interactive/import checks you can use `QT_QPA_PLATFORM=offscreen`.
- Gotcha: creating a strand in the UI is a two-step action — click **New Strand**,
  then click on the canvas to place it. A `1_1` layer button then appears.

### Tests
- Two styles coexist under `tests/`:
  - True pytest files (e.g. `tests/copy_paste/`): `QT_QPA_PLATFORM=offscreen "$HOME/osenv/bin/python" -m pytest tests/copy_paste/ -q`
  - Script-style tests that call `sys.exit()` at import (most others). Do **not**
    run these through `pytest` (collection crashes on their `SystemExit`); run them
    directly, e.g. `QT_QPA_PLATFORM=offscreen "$HOME/osenv/bin/python" tests/selection/test_selection_hit.py`.

### Notes / gotchas
- The root `Procfile` (`web: gunicorn app:app`) is vestigial — there is no `app.py`
  and no web service. Ignore it.
- The optional `json_to_png_exporter/` tool renders offscreen widget grabs; on this
  headless Linux setup some exports come out blank even though the on-screen GUI
  renders correctly. It is not part of the core product.
