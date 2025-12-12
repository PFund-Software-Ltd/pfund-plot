from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from narwhals.typing import Frame

import os
import datetime
import importlib.util
from pathlib import Path

from pfund_plot.enums.notebook_type import NotebookType


def load_js(path: str) -> str:
    js_code = Path(path).read_text()
    return f"<script>{js_code}</script>"


def is_daily_data(df: Frame) -> bool:
    '''Checks if the 'resolution' column is '1d' and the "ts" column by comparing the first two rows to see if the data is daily data.'''
    if df.is_empty():
        return False
    if 'resolution' in df.columns and df.select('resolution').row(0)[0] == '1d':
        return True
    assert 'date' in df.columns, "DataFrame must have a 'date' column"
    assert isinstance(df.select('date').row(0)[0], datetime.datetime), '"date" column must be of type datetime'
    date1 = df.select('date').row(0)[0]
    if df.shape[0] >= 2:
        date2 = df.select('date').row(1)[0]
        delta = date2 - date1
        return delta == datetime.timedelta(days=1)
    else:
        # if only has one data point, check if the time is '00:00:00'
        return str(date1.time()) == '00:00:00'


def get_notebook_type() -> NotebookType | None:
    marimo_spec = importlib.util.find_spec("marimo")
    if marimo_spec is not None:
        import marimo as mo
        if mo.running_in_notebook():
            return NotebookType.marimo
        
    if any(key.startswith(('JUPYTER_', 'JPY_')) for key in os.environ):
        return NotebookType.jupyter
    
    if 'VSCODE_PID' in os.environ:
        return NotebookType.vscode
    
    # None means not in a notebook environment
    return None


def get_free_port():
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))  # Bind to a random free port
        return s.getsockname()[1]


def get_sizing_mode(height: int | None, width: int | None) -> str | None:
    if height is None and width is None:
        return 'stretch_both'
    elif height is None:
        return 'stretch_height'
    elif width is None:
        return 'stretch_width'
    else:
        return None


def load_panel_extensions():
    notebook_type = get_notebook_type()

    # Skip loading Panel extensions in marimo as it (very likely "ipywidgets") causes conflicts during data update
    if notebook_type == NotebookType.marimo:
        return

    import panel as pn

    extensions = ['ipywidgets', 'gridstack', 'tabulator', 'perspective']
    for extension in extensions:
        if extension not in pn.extension._loaded_extensions:
            pn.extension(extension)
            print(f'loaded Panel extension: {extension}')