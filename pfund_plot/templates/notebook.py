from typing import Literal

from pfeed.types.literals import tDATA_SOURCE
from pfund_plot.templates.template import Template
from pfund_plot.const.enums import NotebookType


class Notebook(Template):
    def __init__(
        self,
        data_sources: list[tDATA_SOURCE],
        nb_type: Literal['jupyter', 'marimo'],
    ):
        super().__init__(data_sources)
        self._nb_type = NotebookType[nb_type.upper()]
