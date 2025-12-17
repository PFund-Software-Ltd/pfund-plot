from enum import StrEnum


class PlottingBackend(StrEnum):
    panel = 'panel'  # for general stuff (e.g. GridStack) that don't fall into other plotting backends
    bokeh = 'bokeh'
    svelte = 'svelte'
    plotly = 'plotly'
    altair = 'altair'
    matplotlib = 'matplotlib'
    perspective = 'perspective'
