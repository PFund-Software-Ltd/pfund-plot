from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd
    from narwhals.typing import Frame

import os
from pathlib import Path

from anywidget import AnyWidget
import traitlets


__all__ = ["CandlestickWidget", "plot", "style", "control"]
PYTHON_ENV = os.getenv("PYTHON_ENV", "production")
VITE_PORT = os.getenv("VITE_PORT", "5173")
DEFAULT_HEIGHT = 280
DEFAULT_WIDTH = 780
DEFAULT_NUM_DATA = 150
DEFAULT_SLIDER_STEP = 3_600_000  # 1 hour in milliseconds


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
    height = traitlets.Int(default_value=DEFAULT_HEIGHT).tag(sync=True)
    width = traitlets.Int(default_value=DEFAULT_WIDTH).tag(sync=True)

    def __init__(self, df: Frame, height: int, width: int) -> None:
        super().__init__()
        self.height = height
        self.width = width
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
    height: int = DEFAULT_HEIGHT,
    width: int = DEFAULT_WIDTH,
    show_volume: bool = True,
):
    return locals()


def control(
    num_data: int = DEFAULT_NUM_DATA,
    slider_step: int = DEFAULT_SLIDER_STEP,
):
    return locals()


def plot(df: Frame, style: dict, control: dict) -> CandlestickWidget:
    return CandlestickWidget(df, height=style["height"], width=style["width"])
