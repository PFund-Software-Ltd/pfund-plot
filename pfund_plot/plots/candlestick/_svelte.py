from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd
    from narwhals.typing import Frame

import os
from pathlib import Path

from anywidget import AnyWidget
import traitlets


PYTHON_ENV = os.getenv("PYTHON_ENV", "production")
VITE_PORT = os.getenv("VITE_PORT", "5173")
DEFAULT_HEIGHT_FOR_NOTEBOOK = 300


__all__ = ["CandlestickWidget", "plot", "style", "control"]


class CandlestickWidget(AnyWidget):
    if PYTHON_ENV == "development":
        _esm = (
            f"http://localhost:{VITE_PORT}/src/widgets/tradingview/candlestick/index.ts"
        )
    else:
        _esm = Path(__file__).parents[3] / "ui" / "dist" / "widgets" / "candlestick.js"
    data = traitlets.List(default_value=[]).tag(
        sync=True
    )  # list of dicts with OHLC + time

    def __init__(self, df: Frame, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.update_data(df)

    @staticmethod
    def _format_data(df: pd.DataFrame) -> list[dict]:
        """
        Convert dataframe to format supported by TradingView,
        e.g. [ { "open": 10, "high": 10.63, "low": 9.49, "close": 9.55, "time": '2022-01-17' } ]
        """
        if "date" in df.columns:
            df = df.assign(date=df["date"].astype("str")).rename(
                columns={"date": "time"}
            )
        return df.to_dict(orient="records")

    def update_data(self, df: Frame):
        """Update the widget's data from a DataFrame"""
        self.data = self._format_data(df.to_pandas())


def style(
    height: int | None = None,
    width: int | None = None,
    show_volume: bool = True,
):
    style_dict = locals()
    from pfund_plot.enums import NotebookType
    from pfund_plot.utils.utils import get_notebook_type

    notebook_type: NotebookType | None = get_notebook_type()
    is_notebook = notebook_type is not None
    if is_notebook and height is None:
        height = DEFAULT_HEIGHT_FOR_NOTEBOOK
        style_dict["height"] = height
    return style_dict


def control(
    num_data: int = 100,
    slider_step: int = 100,
):
    return locals()


def plot(df: Frame, style: dict) -> CandlestickWidget:
    return CandlestickWidget(df)
