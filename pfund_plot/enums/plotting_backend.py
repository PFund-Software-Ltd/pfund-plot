from enum import StrEnum


class PlottingBackend(StrEnum):
    bokeh = 'bokeh'
    svelte = 'svelte'
    plotly = 'plotly'
    altair = 'altair'
    matplotlib = 'matplotlib'
