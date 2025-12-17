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
    
    # if 'VSCODE_PID' in os.environ:
    #     return NotebookType.vscode
    
    # None means not in a notebook environment
    return None


# NOTE: loading panel extensions ALWAYS break sth (could be anywidget, displaying in marimo, etc.)
# be VERY CAREFUL WHEN to load an extension
def load_panel_extensions():
    import panel as pn

    extensions = ['ipywidgets', 'tabulator', 'perspective']
    for extension in extensions:
        if extension not in pn.extension._loaded_extensions:
            pn.extension(extension)
            print(f'loaded Panel extension: {extension}')