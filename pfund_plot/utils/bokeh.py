# pyright: reportArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false
from __future__ import annotations
from typing import Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from bokeh.models import CustomJSHover, HoverTool
    import narwhals as nw

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


def create_hover_col_format(
    df: nw.DataFrame[Any],
    col: str,
    datetime_precision: DatetimePrecision = "s",
) -> tuple[tuple[str, str], tuple[str, str | CustomJSHover] | None]:
    """Create the tooltip and formatter for a single column based on its dtype.

    Returns:
        (tooltip, formatter_entry or None)
        - tooltip: e.g. ("date", "@{date}{%Y-%m-%d %H:%M:%S}")
        - formatter_entry: e.g. ("@{date}", "datetime"), or None if no formatter needed
    """
    num_formatter = create_number_formatter_for_hover_tool()
    schema = df.collect_schema()
    col_dtype = schema[col]
    is_datetime = 'datetime' in str(col_dtype).lower() or 'date' in str(col_dtype).lower()
    if is_datetime:
        date_format = get_datetime_hover_format(datetime_precision)
        return (col, f"@{{{col}}}{{{date_format}}}"), (f"@{{{col}}}", "datetime")
    elif col_dtype.is_numeric():
        return (col, f"@{{{col}}}{{custom}}"), (f"@{{{col}}}", num_formatter)
    else:
        return (col, f"@{{{col}}}"), None


def _bundle_hover_config(
    df: nw.DataFrame[Any],
    x_col: str | None,
    y_cols: list[str],
    datetime_precision: DatetimePrecision = "s",
) -> tuple[list[tuple[str, str]], dict[str, str | CustomJSHover]]:
    """Build a single tooltip that bundles x + all y_cols together.

    Only works when a single renderer's ColumnDataSource contains all the columns
    (e.g. single-y plots, or the scatter workaround). For multi-y overlays where
    hvplot creates separate renderers per y column, use create_hover_col_format()
    to build per-column tooltips instead.
    """
    tooltips: list[tuple[str, str]] = []
    formatters: dict[str, str | CustomJSHover] = {}
    cols = ([x_col] if x_col is not None else []) + y_cols
    for col in cols:
        tooltip, formatter_entry = create_hover_col_format(df, col, datetime_precision)
        tooltips.append(tooltip)
        if formatter_entry is not None:
            formatters[formatter_entry[0]] = formatter_entry[1]
    return tooltips, formatters


def create_bundled_hover_tool(
    df: nw.DataFrame[Any],
    x_col: str | None,
    y_cols: list[str],
    datetime_precision: DatetimePrecision = "s",
) -> HoverTool:
    """Create a HoverTool that shows all specified columns in one tooltip.

    Only use when a single renderer's ColumnDataSource contains all the columns
    (e.g. single-y plots, or the scatter workaround where one Scatter holds the
    full dataframe). For multi-y overlays with separate renderers per y column
    """
    from bokeh.models import HoverTool
    tooltips, formatters = _bundle_hover_config(df, x_col, y_cols, datetime_precision)
    return HoverTool(tooltips=tooltips, formatters=formatters, mode="vline")


def create_hover_scatter(
    df: nw.DataFrame[Any],
    x_col: str | None,
    y_cols: list[str],
    datetime_precision: DatetimePrecision = "s",
    marker: str | None = None,
) -> Any:
    """Workaround: create a scatter overlay that provides hover tooltips.

    Some hvplot chart types (e.g. area) render as Bokeh glyphs that transform
    the data (e.g. Patch polygons), destroying the original column values in
    the ColumnDataSource.

    This works by overlaying scatter points whose ColumnDataSource contains the
    original, untransformed data, so a HoverTool attached to it can reference
    the real column values.

    Args:
        marker: marker shape string (e.g. 'circle', 'cross'). If None, points
            are invisible (alpha=0) but still large enough for Bokeh's hit-testing.
    """
    import holoviews as hv

    native_df = df.to_native()
    hover_tool = create_bundled_hover_tool(df, x_col, y_cols, datetime_precision)
    scatter_opts: dict[str, Any] = dict(
        size=7 if marker else 15,
        alpha=1 if marker else 0,
        marker=marker or "circle",
        tools=[hover_tool],
        hover_mode="vline",
    )
    kdims = [x_col or "index"]

    if len(y_cols) == 1:
        return hv.Scatter(native_df, kdims=kdims, vdims=[y_cols[0]]).opts(**scatter_opts)
    else:
        scatters = {
            y_col: hv.Scatter(native_df, kdims=kdims, vdims=[y_col]).opts(**scatter_opts)
            for y_col in y_cols
        }
        return hv.NdOverlay(scatters)


def create_vline_hover_opts(
    df: nw.DataFrame[Any],
    x_col: str | None,
    y_cols: list[str],
    datetime_precision: DatetimePrecision = "s",
) -> Any:
    """This shows the tooltip without needing the cursor to hover over the data points
    Useful in plots like plt.line() for multi-line plots where the tooltips are separated for each line
    """
    from holoviews import opts
    tooltips, formatters = _bundle_hover_config(df, x_col, y_cols, datetime_precision)
    return opts.Curve(
        tools=["hover"],
        hover_mode="vline",
        hover_tooltips=[("series", "@{Variable}"), *tooltips],
        hover_formatters=formatters,
    )