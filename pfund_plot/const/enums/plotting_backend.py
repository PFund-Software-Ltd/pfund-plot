from enum import StrEnum


class PlottingBackend(StrEnum):
    bokeh = 'bokeh'
    plotly = 'plotly'
