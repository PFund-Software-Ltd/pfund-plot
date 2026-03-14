# pyright: reportUnusedParameter=false
from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from holoviews.core.overlay import Overlay

import narwhals as nw


__all__ = ["plot", "style", "control"]


# Shape mapping from user-friendly names to Bokeh marker types
SHAPE_MAP = {
    'circle': 'circle',
    'square': 'square',
    'triangle_up': 'triangle',
    'triangle_down': 'inverted_triangle',
    'diamond': 'diamond',
    'cross': 'cross',
    'x': 'x',
    'star': 'star',
}

DEFAULT_SHAPE = 'circle'
DEFAULT_SIZE = 10
DEFAULT_COLOR = '#1f77b4'


def style(
    label: str | None = None,
    color: str | None = None,
    shape: str | None = None,
    size: int | str | None = None,
    opacity: float = 0.8,
    label_offset: int = 10,
    label_font_size: str = '8pt',
):
    """
    Args:
        label: Column name for text labels, or None
        color: Column name for per-point color, or a literal color string
        shape: Column name for per-point shape, or a literal shape string.
            Supported shapes: circle, square, triangle_up, triangle_down,
            diamond, cross, x, star
        size: Column name for per-point size, or a literal int
        opacity: marker opacity (0.0 to 1.0)
        label_offset: vertical offset for text labels above/below markers
        label_font_size: font size for text labels
    """
    return locals()


def control():
    """Marker overlay has no control parameters by default."""
    return {}


def plot(
    df: nw.DataFrame[Any],
    x: str,
    y: str,
    style: dict[str, Any],
    control: dict[str, Any],
    **kwargs: Any,
) -> Overlay:
    import holoviews as hv

    label_col = style.get('label')
    color = style.get('color')
    shape = style.get('shape')
    size = style.get('size')

    pdf = df.to_native()

    # Determine if color/shape/size refer to columns or are literals
    columns = df.columns
    color_is_col = isinstance(color, str) and color in columns
    shape_is_col = isinstance(shape, str) and shape in columns
    size_is_col = isinstance(size, str) and size in columns

    # Build vdims (extra data columns available for hover/styling)
    vdims = []
    if label_col and label_col in columns:
        vdims.append(label_col)
    if color_is_col:
        vdims.append(color)
    if shape_is_col:
        vdims.append(shape)
    if size_is_col:
        vdims.append(size)

    scatter = hv.Points(pdf, kdims=[x, y], vdims=vdims)

    # Apply marker styling via opts
    opts_kwargs: dict[str, Any] = {
        'alpha': style.get('opacity', 0.8),
    }

    # Color: column-based or literal
    if color_is_col:
        opts_kwargs['color'] = color
    elif color is not None:
        opts_kwargs['color'] = color
    else:
        opts_kwargs['color'] = DEFAULT_COLOR

    # Size: column-based or literal
    if size_is_col:
        opts_kwargs['size'] = size
    elif isinstance(size, (int, float)):
        opts_kwargs['size'] = size
    else:
        opts_kwargs['size'] = DEFAULT_SIZE

    # Shape: column-based or literal
    if shape_is_col:
        # Per-point shapes via column — use hv.dim to map
        opts_kwargs['marker'] = hv.dim(shape).categorize(SHAPE_MAP, default=DEFAULT_SHAPE)
    elif shape is not None:
        opts_kwargs['marker'] = SHAPE_MAP.get(shape, shape)
    else:
        opts_kwargs['marker'] = DEFAULT_SHAPE

    scatter = scatter.opts(**opts_kwargs)

    layers = [scatter]

    # Optional text labels
    if label_col and label_col in columns:
        labels = hv.Labels(pdf, kdims=[x, y], vdims=[label_col])
        labels = labels.opts(
            text_font_size=style.get('label_font_size', '8pt'),
            yoffset=style.get('label_offset', 10),
        )
        layers.append(labels)

    return hv.Overlay(layers)
