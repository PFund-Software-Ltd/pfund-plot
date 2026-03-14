# VIBE-CODED
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Any

if TYPE_CHECKING:
    from pfund_plot.plots.plot import MessageKey, StreamingDfs

import panel as pn

from pfund_plot.widgets.base import BaseStreamingWidget


class TickerSelectWidget(BaseStreamingWidget):
    """Dropdown for switching between streaming tickers (products).

    Auto-created when a streaming feed has multiple products.
    Switches the active msg_key on the plot so the pane displays
    a different product's data.  All streams continue in the
    background; this widget only controls which one is shown.
    """

    def __init__(
        self,
        streaming_dfs: StreamingDfs,
        active_key: MessageKey,
        update_callback: Callable[[MessageKey], None],
    ):
        super().__init__(streaming_dfs, active_key, update_callback)
        msg_keys = list(streaming_dfs.keys())
        self._select = pn.widgets.Select(
            name='Ticker',
            options=self._build_options(msg_keys),
            value=active_key,
        )
        self._watcher = self._select.param.watch(self._on_select, 'value')

    @staticmethod
    def _build_options(msg_keys: list[MessageKey]) -> dict[str, MessageKey]:
        """Build {display_label: msg_key} dict for the Select widget."""
        resolutions = {res for _, res in msg_keys}
        if len(resolutions) == 1:
            # All same resolution — just show the product name
            return {product: (product, res) for product, res in msg_keys}
        # Mixed resolutions — disambiguate with "(resolution)"
        return {f"{product} ({res})": (product, res) for product, res in msg_keys}

    def _fan_out_to_overlays(self, msg_key: MessageKey) -> None:
        """Switch each overlay widget's active stream to the same msg_key.
        Must be called BEFORE the parent's _update_callback so the DynamicMap re-render
        picks up the updated overlay dfs.
        """
        for overlay_widget in self._overlays:
            overlay_widget._update_callback(msg_key)

    def _on_select(self, event: Any) -> None:
        self._fan_out_to_overlays(event.new)
        self._update_callback(event.new)

    def update_streaming_state(self, streaming_dfs: StreamingDfs) -> None:
        """Update dropdown options when new products start streaming."""
        msg_keys = list(streaming_dfs.keys())
        current_keys = set(self._select.options.values()) if isinstance(self._select.options, dict) else set()
        if set(msg_keys) == current_keys:
            return
        current_value = self._select.value
        self._select.param.unwatch(self._watcher)
        try:
            self._select.options = self._build_options(msg_keys)
            if current_value in self._select.options.values():
                self._select.value = current_value
        finally:
            self._watcher = self._select.param.watch(self._on_select, 'value')

    def get_panel_objects(self) -> list[pn.widgets.Widget]:
        return [self._select]
