from __future__ import annotations
from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from bokeh.models import CustomJSHover

DatetimePrecision = Literal["d", "s", "ms"]

DATETIME_PRECISION_FORMATS: dict[DatetimePrecision, str] = {
    "d": "%Y-%m-%d",
    "s": "%Y-%m-%d %H:%M:%S",
    "ms": "%Y-%m-%d %H:%M:%S.%3N",
}


def get_datetime_hover_format(datetime_precision: DatetimePrecision) -> str:
    if datetime_precision not in DATETIME_PRECISION_FORMATS:
        raise ValueError(f"Unsupported datetime_precision: {datetime_precision!r}, must be one of {list(DATETIME_PRECISION_FORMATS)}")
    return DATETIME_PRECISION_FORMATS[datetime_precision]



def create_number_formatter_for_hover_tool(significant_digits: int = 6) -> CustomJSHover:
    '''Create a number formatter for bokeh hover tools.
    Args:
        significant_digits: Number of significant digits to display
    '''
    from bokeh.models import CustomJSHover
    return CustomJSHover(code=f"""
        return value.toPrecision({significant_digits}).replace(/0+$/, '').replace(/\\.$/, '');
    """)