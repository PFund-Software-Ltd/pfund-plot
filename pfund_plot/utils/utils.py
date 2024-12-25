from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from narwhals.typing import FrameT

import datetime


def is_daily_data(df: FrameT) -> bool:
    '''Checks if the 'resolution' column is '1d' and the "ts" column by comparing the first two rows to see if the data is daily data.'''
    if 'resolution' in df.columns and df.select('resolution').row(0)[0] == '1d':
        return True
    assert 'ts' in df.columns, "DataFrame must have a 'ts' column"
    assert isinstance(df.select('ts').row(0)[0], datetime.datetime), '"ts" column must be of type datetime'
    ts1 = df.select('ts').row(0)[0]
    ts2 = df.select('ts').row(1)[0]
    delta = ts2 - ts1
    return delta == datetime.timedelta(days=1)