from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from narwhals.typing import FrameT

import os
import datetime
import importlib.util

from pfund_plot.const.enums.notebook_type import NotebookType


def is_daily_data(df: FrameT) -> bool:
    '''Checks if the 'resolution' column is '1d' and the "ts" column by comparing the first two rows to see if the data is daily data.'''
    if 'resolution' in df.columns and df.select('resolution').row(0)[0] == '1d':
        return True
    assert 'ts' in df.columns, "DataFrame must have a 'ts' column"
    assert isinstance(df.select('ts').row(0)[0], datetime.datetime), '"ts" column must be of type datetime'
    ts1 = df.select('ts').row(0)[0]
    ts2 = df.select('ts').row(1)[0]
    delta = ts2 - ts1
    return delta == datetime.timedelta(days=1)


def get_notebook_type() -> NotebookType:
    marimo_spec = importlib.util.find_spec("marimo")
    if marimo_spec is not None:
        import marimo as mo
        if mo.running_in_notebook():
            return NotebookType.marimo
        
    if any(key.startswith(('JUPYTER_', 'JPY_')) for key in os.environ):
        return NotebookType.jupyter
    
    return NotebookType.vscode


def get_free_port():
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))  # Bind to a random free port
        return s.getsockname()[1]