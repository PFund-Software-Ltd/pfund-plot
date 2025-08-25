from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import pandas as pd
    from narwhals.typing import Frame

from pathlib import Path

import anywidget
import traitlets

from pfund_plot.enums import NotebookType


class CandlestickWidget(anywidget.AnyWidget):
    _esm = Path(__file__).parents[3] / "ui" / "dist" / "candlestick.js"
    data = traitlets.List(default_value=[]).tag(sync=True)       # list of dicts with OHLC + time


def style(
    height: int | None = None,
    width: int | None = None,
    show_volume: bool = True,
):
    return locals()


def control():
    return {}


def _format_data(df: pd.DataFrame) -> list[dict]:
    '''
    Convert dataframe to format supported by TradingView,
    e.g. [ { "open": 10, "high": 10.63, "low": 9.49, "close": 9.55, "time": '2022-01-17' } ]
    '''
    df['date'] = df['date'].astype('str')
    df.rename({'date': 'time'}, inplace=True, axis=1)
    return df.to_dict(orient='records')


def plot(df: Frame, style: dict):
    from pfund_plot.utils.utils import get_notebook_type
    
    notebook_type = get_notebook_type()
    data = _format_data(df.to_pandas())
    widget = CandlestickWidget(data=data)
    if notebook_type == NotebookType.marimo:
        import marimo as mo
        return mo.ui.anywidget(widget)
    else:
        return widget
