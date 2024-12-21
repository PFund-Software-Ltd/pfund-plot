from pfeed.types.literals import tDATA_SOURCE
from pfund_plot.templates.template import Template
from pfund_plot.const.enums import DashboardType


class Dashboard(Template):
    def __init__(
        self,
        data_sources: list[tDATA_SOURCE],
        db_type: DashboardType,
    ):
        super().__init__(data_sources)
        self._db_type = DashboardType[db_type.upper()]
