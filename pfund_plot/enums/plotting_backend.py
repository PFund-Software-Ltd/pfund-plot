from enum import StrEnum


class PlottingBackend(StrEnum):
    panel = 'panel'  # for general stuff (e.g. GridStack) that don't fall into other plotting backends
    holoviews = 'holoviews'  # for directly passing in holoviews objects only using plt.holoviews()
    bokeh = 'bokeh'
    svelte = 'svelte'
    plotly = 'plotly'
    altair = 'altair'
    matplotlib = 'matplotlib'
    perspective = 'perspective'
