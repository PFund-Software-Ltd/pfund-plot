# pyright: reportArgumentType=false, reportOptionalMemberAccess=false, reportOptionalSubscript=false, reportCallIssue=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from narwhals.typing import IntoFrame

from pfund_plot.enums import PlottingBackend
from pfund_plot.plots.plot import BasePlot

__all__ = ["Label"]


class LabelStyle:
    from pfund_plot.plots.label.bokeh import style as bokeh_style

    bokeh = bokeh_style


class LabelControl:
    from pfund_plot.plots.label.bokeh import control as bokeh_control

    bokeh = bokeh_control


class Label(BasePlot):
    SUPPORTED_BACKENDS: ClassVar[list[PlottingBackend]] = [PlottingBackend.bokeh]
    style = LabelStyle
    control = LabelControl

    def __init__(
        self,
        data: IntoFrame,
        text: str,
        x: str | None = None,
        y: str | list[str] | None = None,
        name: str | None = None,
        **reactive_params: Any,
    ):
        self._text = text
        super().__init__(data=data, x=x, y=y, name=name, **reactive_params)
        self._plot_kwargs["text"] = text
