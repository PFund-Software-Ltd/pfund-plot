from pfeed.types.literals import tDATA_SOURCE
from pfeed.const.enums import DataSource



# TODO: move Analyzer from pfund to here
class Template:
    def __init__(self, data_sources: list[tDATA_SOURCE]):
        self.data_sources = [DataSource[ds.upper()] for ds in data_sources]
    
