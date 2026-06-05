from pfund_kit.style import RichColor, TextStyle, cprint

from pfund_plot.enums import DisplayMode
from pfund_plot.plots.layout.layout import BaseLayout
from pfund_plot.plots.lazy import LazyPlot


class LayoutStyle:
    from pfund_plot.plots.layout.panel import style as panel_style

    panel = panel_style


class LayoutControl:
    from pfund_plot.plots.layout.panel import control as panel_control

    panel = panel_control


class Layout(BaseLayout):
    _MAX_COLS = 12  # maximum number of columns in a grid when using GridStack

    style = LayoutStyle
    control = LayoutControl

    def __init__(self, *plots: LazyPlot):  # pyright: ignore[reportInconsistentConstructor]
        super().__init__(*plots)
        default_mode = DisplayMode.browser
        self._set_mode(default_mode)

    def _render(self):
        if self._mode == DisplayMode.desktop:
            cprint(
                "There is a known issue in resizing when using plt.layout (GridStack) in desktop mode. Please consider switching to browser mode instead.",
                style=TextStyle.BOLD + RichColor.YELLOW,
            )
        return super()._render()

    def _validate_grid_specs(self):
        # Check grid_spec consistency: either all plots have it or none do
        grid_specs = [plot._grid_spec for plot in self._plots]
        has_grid_spec = [grid_spec is not None for grid_spec in grid_specs]
        all_has_grid_spec = all(has_grid_spec)
        if any(has_grid_spec):
            if not all_has_grid_spec:
                raise ValueError("All plots must have grid_spec defined if any do.")
            else:
                # REVIEW: somehow when column index exceeds 12, GridStack doesn't work, columns must be within 0-12
                if any(
                    grid_spec[1].stop is not None and grid_spec[1].stop > self._MAX_COLS
                    for grid_spec in grid_specs
                ):
                    raise ValueError(
                        f"Column index exceeds maximum of {self._MAX_COLS}. Grid uses a {self._MAX_COLS}-column system."
                    )
        assert self._control is not None, "control is not set"
        assert self._control["num_cols"] <= self._MAX_COLS, (
            f"'num_cols' must be less than or equal to {self._MAX_COLS}"
        )

    def _warn_if_widgets_with_drag(self):
        """Warn if child plots have widgets and GridStack drag is enabled.

        GridStack's drag handler intercepts pointer events, which prevents
        click-based widgets (e.g. Select dropdowns, buttons) from working.
        Drag-based widgets (e.g. sliders) are unaffected.
        """
        if self._control is None or not self._control.get("allow_drag", True):
            return
        for lazyplot in self._plots:
            plot = lazyplot._plot
            has_widgets = (
                plot._widgets or plot._streaming_widgets or plot._reactive_widgets
            )
            if not has_widgets:
                for overlay in plot._overlays:
                    has_widgets = (
                        overlay._widgets
                        or overlay._streaming_widgets
                        or overlay._reactive_widgets
                    )
                    if has_widgets:
                        break
            if has_widgets:
                cprint(
                    "Widgets detected inside Layout with allow_drag=True. Click-based widgets (e.g. dropdowns, buttons) may not work. "
                    + "Use plt.layout(...).control(allow_drag=False) to fix this.",
                    style=TextStyle.BOLD + RichColor.YELLOW,
                )
                break

    def _create_component(self):
        self._validate_grid_specs()
        super()._create_component()

    def _create(self):
        super()._create()
        self._warn_if_widgets_with_drag()
