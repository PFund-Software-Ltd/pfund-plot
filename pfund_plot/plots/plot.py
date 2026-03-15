# pyright: reportAttributeAccessIssue=false, reportOptionalMemberAccess=false, reportConstantRedefinition=false, reportUnusedParameter=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false
from __future__ import annotations
from typing import Callable, TYPE_CHECKING, ClassVar, Any, Literal, cast, TypeAlias

if TYPE_CHECKING:
    from narwhals.typing import IntoFrame
    from holoviews.streams import Pipe
    from anywidget import AnyWidget
    from panel.pane import Pane
    from panel.widgets import Widget as PanelWidget
    from pfeed.streaming.streaming_message import StreamingMessage
    from pfeed.feeds.market_feed import MarketFeed
    from pfund_plot.renderers.base import BaseRenderer
    from pfund_plot.plots.lazy import LazyPlot
    from pfund.typing import ProductName, ResolutionRepr
    from pfund_plot.typing import (
        RenderedResult,
        Figure,
        Component,
        Plot,
        RawFigure,
        Style,
        Control,
    )
    MessageKey: TypeAlias = tuple[ProductName, ResolutionRepr]
    StreamingDfs: TypeAlias = dict[MessageKey, Any]  # MessageKey -> nw.DataFrame

import asyncio
import time
import warnings
import importlib
from threading import Thread
from abc import ABC

import narwhals as nw
import panel as pn

from pfund_kit.style import cprint, RichColor, TextStyle
from pfund_plot.enums import PlottingBackend, DisplayMode, NotebookType
from pfund_plot.widgets.base import BaseWidget, BaseStreamingWidget


class BasePlot(ABC):
    REQUIRED_COLS: ClassVar[list[str] | None] = None
    SUPPORTED_BACKENDS: ClassVar[list[PlottingBackend] | None] = None
    SUPPORT_STREAMING: ClassVar[bool] = False
    SUPPORTED_WIDGETS: ClassVar[list[type[BaseWidget]] | None] = None
    SUPPORTED_STREAMING_WIDGETS: ClassVar[list[type[BaseStreamingWidget]] | None] = None
    _ChosenWidgetClasses: ClassVar[list[type[BaseWidget]]] = []
    _ChosenStreamingWidgetClasses: ClassVar[list[type[BaseStreamingWidget]]] = []
    # Wrapper class like CandlestickStyle, used to access the style() function based on backend
    style: ClassVar[Any | None] = None
    # Wrapper class like CandlestickControl, used to access the control() function based on backend
    control: ClassVar[Any | None] = None
    _style: ClassVar[Style | None] = None  # actual style dictionary
    _control: ClassVar[Control | None] = None  # actual control dictionary
    _backend: ClassVar[PlottingBackend | None] = None
    _mode: ClassVar[DisplayMode | None] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> LazyPlot:
        from pfund_plot.plots.lazy import LazyPlot

        instance: BasePlot = super().__new__(cls)
        # manually call __init__ to initialize the instance
        instance.__init__(*args, **kwargs)
        return LazyPlot(instance)

    def __deepcopy__(self, memo: dict) -> BasePlot:
        from copy import deepcopy
        cls = type(self)
        # bypass __new__ which would call __init__ and wrap in LazyPlot
        new = object.__new__(cls)
        memo[id(self)] = new
        for k, v in self.__dict__.items():
            setattr(new, k, deepcopy(v, memo))
        return new

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        class_name = cls.__name__
        assert cls.SUPPORTED_BACKENDS is not None, (
            f"SUPPORTED_BACKENDS is not defined for class {class_name}"
        )
        if cls.SUPPORTED_WIDGETS is not None:
            cls._ChosenWidgetClasses = list(cls.SUPPORTED_WIDGETS)
        if cls.SUPPORTED_STREAMING_WIDGETS is not None:
            cls._ChosenStreamingWidgetClasses = list(cls.SUPPORTED_STREAMING_WIDGETS)
        for backend in cls.SUPPORTED_BACKENDS:
            if cls.style is not None:
                assert hasattr(cls.style, backend.value), (
                    f"style for {backend} is not defined for class {class_name}"
                )
            if cls.control is not None:
                assert hasattr(cls.control, backend.value), (
                    f"control for {backend} is not defined for class {class_name}"
                )

    def __init__(
        self,
        data: IntoFrame | MarketFeed,
        x: str | None = None,
        y: str | list[str] | None = None,
        callback: Callable[..., Any] | None = None,
        name: str | None = None,
        **reactive_params: Any,
    ):
        '''
        Args:
            data: The dataframe for static plot or pfeed's feed object for streaming plot
            x: the column name of the x-axis, if None, will use the index or the first column of the dataframe
            y: the column name of the y-axis, if None, will plot all numeric columns of the dataframe
            callback: A reactive callback function. When provided with **reactive_params,
                      auto-creates widgets that re-fetch data on change.
            name: Display name for this plot (used as label when widgets are shown alongside overlays).
                  Defaults to the class name lowercased (e.g. "candlestick", "line").
            **reactive_params: name=value pairs for reactive widgets (e.g. ticker=["BTC", "ETH"]).
                               Requires callback to be set.
        '''
        from pfeed.feeds.base_feed import BaseFeed
        from pfund_kit.utils import get_notebook_type

        # check if data is a dataframe or a feed
        if not isinstance(data, BaseFeed):
            self._df: nw.DataFrame[Any] = data
            self._feed: MarketFeed | None = None
        else:
            self._df: nw.DataFrame[Any] | None = None
            self._feed: MarketFeed | None = data
        self.name: str | None = name or self._class_name
        self._reactive_params: dict[str, Any] = reactive_params
        self._reactive_callback: Callable[..., Any] | None = callback
        self._reactive_widgets: dict[str, PanelWidget] = {}
        self._setup()
        self._x: str | None = x
        self._y: str | list[str] | None = y
        if self._df is not None:
            self._df = self._standardize_df(self._df)
        self._anywidget: AnyWidget | None = None
        self._plot: Plot | None = None
        self._pane: Pane | None = None
        self._widgets: dict[type[BaseWidget], BaseWidget] = {}
        self._active_msg_key: MessageKey | None = None
        self._streaming_dfs: dict[MessageKey, nw.DataFrame[Any]] = {}
        self._streaming_pipe: Pipe | None = None
        self._streaming_thread: Thread | None = None
        self._streaming_widgets: dict[type[BaseStreamingWidget], BaseStreamingWidget] = {}
        self._component: Component | None = None
        self._overlays: list[BasePlot] = []
        self._holoviews_opts: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
        self._parent_plot: BasePlot | None = None  # set when this plot is used as an overlay

        self._notebook_type: NotebookType | None = get_notebook_type()

        cls = self.__class__
        if cls._backend is None:
            cls.set_backend(cls.SUPPORTED_BACKENDS[0])
        if cls._mode is None:
            cls.set_mode(
                DisplayMode.notebook if self._notebook_type else DisplayMode.browser
            )

        # Initialize instance variables
        self._backend: PlottingBackend | None = None
        self._mode: DisplayMode | None = None
        self._renderer: BaseRenderer | None = None
        self._style: Style | None = None
        self._control: Control | None = None
        self._ChosenWidgetClasses: list[type[BaseWidget]] = list(cls._ChosenWidgetClasses)
        self._ChosenStreamingWidgetClasses: list[type[BaseStreamingWidget]] = list(cls._ChosenStreamingWidgetClasses)
        self._set_backend(cls._backend)
        self._set_mode(cls._mode)

    @staticmethod
    def _is_hvplot(plot: Plot) -> bool:
        from holoviews.core.overlay import Overlay, NdOverlay
        from holoviews.core.element import Element
        return isinstance(plot, (Overlay, NdOverlay, Element))
    
    @property
    def _class_name(self) -> str:
        return self.__class__.__name__.lower()
    
    def _standardize_df(self, df: IntoFrame) -> nw.DataFrame[Any]:
        import datetime

        df = nw.from_native(df)
        if isinstance(df, nw.LazyFrame):
            df = df.collect()
        # convert all columns to lowercase
        df = df.rename({col: col.lower() for col in df.columns})
        # rename common datetime column names to 'date'
        date_original_name = "date"
        for alias in ("datetime", "timestamp"):
            if alias in df.columns and "date" not in df.columns:
                date_original_name = alias
                df = df.rename({alias: "date"})
        # if 'date' column exists, ensure it's a proper datetime type
        if "date" in df.columns:
            date_value = df.select("date").row(0)[0]
            if not isinstance(date_value, datetime.datetime):
                try:
                    df = df.with_columns(
                        nw.col("date").str.to_datetime(format=None),
                    )
                except Exception:
                    raise TypeError(f"Column '{date_original_name}' cannot be converted to datetime (got {type(date_value).__name__})")
            # normalize to naive UTC — Panel/Bokeh widgets don't handle tz-aware datetimes consistently
            date_dtype = df.collect_schema()["date"]
            if hasattr(date_dtype, 'time_zone') and date_dtype.time_zone is not None:  # pyright: ignore[reportAttributeAccessIssue]
                df = df.with_columns(
                    nw.col("date").dt.convert_time_zone("UTC").dt.replace_time_zone(None)
                )
        if self.REQUIRED_COLS:
            missing_cols = [col for col in self.REQUIRED_COLS if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
        return df

    def _create_msg_key(self, msg: StreamingMessage) -> MessageKey:
        '''Create a message key for streaming'''
        msg_key = (msg.product, msg.resolution)
        # set the first product as active by default
        if self._active_msg_key is None:
            self._active_msg_key = msg_key
        return msg_key


    def _create_widgets(self) -> None:
        def _has_required_cols(WidgetClass: type[BaseWidget]) -> bool:
            """Check if the df has the columns required by the widget."""
            required = WidgetClass.REQUIRED_COLS
            if not required:
                return True
            return all(col in self._df.columns for col in required)
        
        from pfund_plot.config import get_config
        if get_config().disable_widgets or not self._control.get('widgets', True):
            return

        for WidgetClass in self._ChosenWidgetClasses:
            if WidgetClass not in self._widgets and _has_required_cols(WidgetClass):
                self._widgets[WidgetClass] = WidgetClass(self._df, self._control, self._update_pane)

        if self._feed is not None:
            for WidgetClass in self._ChosenStreamingWidgetClasses:
                if WidgetClass not in self._streaming_widgets:
                    self._streaming_widgets[WidgetClass] = WidgetClass(
                        self._streaming_dfs, self._active_msg_key, self._update_active_stream,
                    )

    def _update_widgets(self, df: nw.DataFrame[Any]) -> None:
        if not self._widgets and not self._streaming_widgets:
            self._create_widgets()
        for widget in self._widgets.values():
            widget.update_df(df)
        for widget in self._streaming_widgets.values():
            widget.update_streaming_state(self._streaming_dfs)

    def _append_toolbox(self, widget_objects: list[PanelWidget], label: str = "", position: Literal["top", "bottom"] = "bottom") -> None:
        """Add a group of widget objects to the component, optionally with a label header.

        Args:
            position: "bottom" appends after the plot, "top" inserts before it.
        """
        if not widget_objects:
            return
        items: list[PanelWidget] = list(widget_objects)
        if label:
            items.insert(0, pn.pane.Markdown(f"**{label}**"))
        toolbox = pn.FlexBox(
            *items,
            align_items="center",
            justify_content="center",
        )
        if position == "top":
            if isinstance(self._component, pn.Column):
                self._component.insert(0, toolbox)
            else:
                self._component = pn.Column(toolbox, self._component)
        else:
            if isinstance(self._component, pn.Column):
                self._component.append(toolbox)
            else:
                self._component = pn.Column(self._component, toolbox)

    def _resolve_widget_merging(
        self,
        parent_widgets: dict[type, BaseWidget | BaseStreamingWidget],
        overlay_widgets_attr: str,
    ) -> set[type]:
        """Merge parent widgets with overlay widgets of the same class.

        For each parent widget, if an overlay has the same widget class and
        can_merge_with returns True, register the overlay as a participant
        (one widget controls both). Track which overlay widget classes were
        merged so they can be skipped during individual rendering.

        Returns the set of widget classes that were merged.
        """
        merged: set[type] = set()
        for WidgetClass, widget in parent_widgets.items():
            for overlay in self._overlays:
                overlay_widgets = getattr(overlay, overlay_widgets_attr)
                if WidgetClass in overlay_widgets and widget.can_merge_with(overlay_widgets[WidgetClass]):
                    widget.add_overlay(overlay_widgets[WidgetClass])
                    merged.add(WidgetClass)
        return merged

    def _collect_unmerged_overlay_widgets(
        self,
        overlay_widgets_attr: str,
        merged_classes: set[type],
        position: Literal["top", "bottom"] = "bottom",
    ) -> bool:
        """Render overlay widgets that weren't merged with the parent, each with a label.

        Returns True if any unmerged overlay widgets were found.
        """
        has_unmerged = False
        for overlay in self._overlays:
            overlay_widgets = getattr(overlay, overlay_widgets_attr)
            overlay_objects: list[PanelWidget] = []
            for WidgetClass, widget in overlay_widgets.items():
                if WidgetClass in merged_classes:
                    continue
                overlay_objects.extend(widget.get_panel_objects())
            if overlay_objects:
                has_unmerged = True
            self._append_toolbox(overlay_objects, label=overlay.name, position=position)
        return has_unmerged

    def _attach_widgets(self) -> None:
        """Append non-streaming widgets at the bottom of the component.

        Smart merging: parent widgets with matching class are auto-merged
        so one widget (e.g. datetime slider) controls both the parent plot
        and its overlays. Overlay-only widgets that can't be merged are
        rendered individually with a label.
        """
        if not self._widgets and not self._streaming_widgets:
            self._create_widgets()

        # Set overlay parent refs and create their widgets
        for overlay in self._overlays:
            overlay._parent_plot = self
            if not overlay._widgets and not overlay._streaming_widgets:
                overlay._create_widgets()

        # Merge + collect parent widgets
        merged = self._resolve_widget_merging(self._widgets, '_widgets')
        widget_objects: list[PanelWidget] = []
        for widget in self._widgets.values():
            widget_objects.extend(widget.get_panel_objects())
        # Unmerged overlay widgets
        has_unmerged = self._collect_unmerged_overlay_widgets('_widgets', merged)
        label = self.name if has_unmerged else ""
        self._append_toolbox(widget_objects, label=label)

    @staticmethod
    def _infer_widget(name: str, value: Any) -> PanelWidget:
        """Infer and create a Panel widget from a reactive param's name and value.

        The value's Python type determines which widget is created:
            Panel widget    → used as-is (escape hatch for full customization)
            list            → Select dropdown (first item is default)
            (min, max, val) → IntSlider if val is int, FloatSlider if float
            bool            → Toggle button
            str             → TextInput

        The param name is used as the widget label,
        with underscores replaced by spaces and title-cased (e.g. 'num_bars' → 'Num Bars').
        """
        if isinstance(value, pn.widgets.Widget):
            return value
        if isinstance(value, list):
            return pn.widgets.Select(name=name.replace('_', ' ').title(), options=value, value=value[0])
        if isinstance(value, tuple) and len(value) == 3:
            min_val, max_val, default = value
            if isinstance(default, float):
                return pn.widgets.FloatSlider(name=name.replace('_', ' ').title(), start=min_val, end=max_val, value=default)
            return pn.widgets.IntSlider(name=name.replace('_', ' ').title(), start=min_val, end=max_val, value=default)
        # NOTE: bool check must come before any future int check, since bool is a subclass of int
        if isinstance(value, bool):
            return pn.widgets.Toggle(name=name.replace('_', ' ').title(), value=value)
        if isinstance(value, str):
            return pn.widgets.TextInput(name=name.replace('_', ' ').title(), value=value)
        raise ValueError(f"Cannot create widget from {type(value).__name__} for param '{name}'. " +
                         "Pass a list, tuple (min, max, default), bool, str, or a Panel widget.")

    def _create_reactive_widgets(self) -> None:
        """Create Panel widgets from reactive params. Binding is deferred to _attach_reactive_widgets."""
        if not self._reactive_params:
            return
        for name, value in self._reactive_params.items():
            self._reactive_widgets[name] = self._infer_widget(name, value)

    def _setup_reactive_binding(self, merged_params: set[str] | None = None) -> None:
        callback = self._reactive_callback
        assert callback is not None, "callback is required when reactive_params are provided"
        widgets = self._reactive_widgets
        overlays = self._overlays

        def on_change(*events: Any) -> None:
            kwargs = {name: w.value for name, w in widgets.items()}
            df = callback(**kwargs)
            df = self._standardize_df(df)
            self._update_df(df)

            # Fan out merged params to overlays
            if merged_params:
                for overlay in overlays:
                    if overlay._reactive_callback is not None:
                        overlay_kwargs = {n: w.value for n, w in overlay._reactive_widgets.items()}
                        # Override merged params with parent's current values
                        for p in merged_params:
                            if p in overlay_kwargs:
                                overlay_kwargs[p] = widgets[p].value
                        overlay_df = overlay._reactive_callback(**overlay_kwargs)
                        overlay_df = overlay._standardize_df(overlay_df)
                        overlay._update_df(overlay_df)

            self._update_pane(df)

        for widget in widgets.values():
            _ = widget.param.watch(on_change, 'value')

    def _attach_reactive_widgets(self) -> None:
        """Insert reactive widgets at the top of the component.

        Smart merging: if an overlay has the exact same reactive params (names
        AND values), its widgets are merged — one set of widgets controls both
        plots via fan-out. Otherwise the overlay's widgets are shown separately
        with a label and their own binding.
        """
        if not self._reactive_widgets and not any(
            overlay._reactive_params for overlay in self._overlays
        ):
            return

        # Create overlay reactive widgets (mirrors _attach_widgets pattern)
        for overlay in self._overlays:
            if overlay._reactive_params and not overlay._reactive_widgets:
                overlay._create_reactive_widgets()

        # Determine which overlays can be fully merged (all params match by name AND value)
        mergeable_overlays: set[int] = set()
        for i, overlay in enumerate(self._overlays):
            if overlay._reactive_params and self._reactive_params == overlay._reactive_params:
                mergeable_overlays.add(i)

        # Set up parent binding with fan-out to mergeable overlays
        if self._reactive_widgets:
            merged_params = set(self._reactive_params.keys()) if mergeable_overlays else None
            self._setup_reactive_binding(merged_params)

        # Show parent reactive widgets (with label when overlays have separate widgets)
        if self._reactive_widgets:
            has_unmerged_overlays = any(
                i not in mergeable_overlays and overlay._reactive_widgets
                for i, overlay in enumerate(self._overlays)
            )
            label = self.name if has_unmerged_overlays else ""
            self._append_toolbox(list(self._reactive_widgets.values()), label=label, position="top")

        # Show non-mergeable overlay reactive widgets separately
        for i, overlay in enumerate(self._overlays):
            if i in mergeable_overlays or not overlay._reactive_widgets:
                continue
            overlay._setup_reactive_binding()
            self._append_toolbox(list(overlay._reactive_widgets.values()), label=overlay.name, position="top")

    def _attach_streaming_widgets(self) -> None:
        """Insert streaming widgets at the top of the component."""
        # Merge + collect parent streaming widgets
        merged = self._resolve_widget_merging(self._streaming_widgets, '_streaming_widgets')
        streaming_objects: list[PanelWidget] = []
        for widget in self._streaming_widgets.values():
            streaming_objects.extend(widget.get_panel_objects())
        # Unmerged overlay streaming widgets (insert first so they end up below parent's)
        has_unmerged = self._collect_unmerged_overlay_widgets('_streaming_widgets', merged, position="top")
        label = self.name if has_unmerged else ""
        self._append_toolbox(streaming_objects, label=label, position="top")

    def _add_overlay(self, overlay: BasePlot):
        self._overlays.append(overlay)

    def _add_opts(self, args: tuple[Any, ...], kwargs: dict[str, Any]):
        self._holoviews_opts.append((args, kwargs))

    def _update_df(self, df: nw.DataFrame[Any]):
        self._df = df

    def _update_active_stream(self, msg_key: MessageKey) -> None:
        """Switch which streaming product is displayed."""
        self._active_msg_key = msg_key
        if msg_key in self._streaming_dfs:
            df = self._streaming_dfs[msg_key]
            self._update_df(df)
            self._update_pane(df)
            # Update other widgets (e.g. datetime range) for the new product's data
            for widget in self._widgets.values():
                widget.update_df(df)

    def _update_streaming_df(self, msg_key: MessageKey, df: nw.DataFrame[Any]):
        # if exceeds max_data, truncate the dataframe
        df = self._truncate_streaming_df(df)
        self._streaming_dfs[msg_key] = df
        # update the data reference if the received message key is the active key
        if msg_key == self._active_msg_key:
            self._update_df(df)

    def _create_component(self) -> None:
        height = self._style.get("total_height")
        width = self._style.get("width")
        self._component = pn.Column(
            self._pane,
            name=self._style.get("title", ""),
            sizing_mode=self._get_sizing_mode(height, width),
            height=height,
            width=width,
        )

    @classmethod
    def get_supported_backends(cls) -> list[PlottingBackend]:
        return cast(list[PlottingBackend], cls.SUPPORTED_BACKENDS)
    
    @classmethod
    def get_required_cols(cls) -> list[str]:
        if cls.REQUIRED_COLS is None:
            return []
        return cls.REQUIRED_COLS
    
    @classmethod
    def get_supported_widgets(cls) -> list[type[BaseWidget]]:
        if cls.SUPPORTED_WIDGETS is None:
            return []
        return cls.SUPPORTED_WIDGETS
    
    @classmethod
    def get_supported_streaming_widgets(cls) -> list[type[BaseStreamingWidget]]:
        if cls.SUPPORTED_STREAMING_WIDGETS is None:
            return []
        return cls.SUPPORTED_STREAMING_WIDGETS
    
    @classmethod
    def is_support_streaming(cls) -> bool:
        return cls.SUPPORT_STREAMING
    
    @staticmethod
    def _derive_y_cols(df: nw.DataFrame[Any], x: str | None, y: str | list[str] | None) -> list[str]:
        if y is None:
            y_cols = [c for c in df.columns if c != x]
        elif isinstance(y, str):
            y_cols = [y]
        else:
            y_cols = y
        return y_cols
    
    @staticmethod
    def _derive_x_col(df: nw.DataFrame[Any], x: str | None) -> str | None:
        x_col = x
        native_df = df.to_native()
        if x is None:
            if hasattr(native_df, 'index') and native_df.index.name is not None:
                x_col = native_df.index.name
        return x_col
    
    def _setup(self):
        from pfund_plot.utils import import_hvplot_df_module, match_df_with_data_tool
        from pfeed import get_config
        from pfeed.feeds.streaming_feed_mixin import StreamingFeedMixin

        if self._df is not None:
            import_hvplot_df_module(match_df_with_data_tool(self._df))

        if self._feed is not None:
            assert self.SUPPORT_STREAMING, f"{self._class_name} does not support streaming"
            if not isinstance(self._feed, StreamingFeedMixin):
                raise ValueError("feed must be a pfeed's Feed object that supports streaming")
            # set pipeline mode to True for streaming to standardize the run method to be feed.run()
            assert self._feed.is_pipeline(), f"{self._feed} must be in pipeline mode"
            assert self._feed._num_workers is None, f"Ray is not supported in streaming plot, {self._feed.__class__.__name__} 'num_workers' must be None"
            pfeed_config = get_config()
            data_tool = pfeed_config.data_tool
            import_hvplot_df_module(data_tool)
        
        if self._reactive_params:
            assert self._reactive_callback is not None, "callback is required when reactive_params are provided"
            assert self._feed is None, "reactive params are not supported with streaming feed"

    def _create(self):
        if self._pane is None:
            self._create_pane()
        if not self._widgets:
            self._create_widgets()
        if self._reactive_params and not self._reactive_widgets:
            self._create_reactive_widgets()
        if self._component is None:
            self._create_component()
            self._attach_widgets()
            self._attach_streaming_widgets()
            self._attach_reactive_widgets()

    def _add_periodic_callback(self, callback: Callable[..., Any]):
        '''Add a periodic callback to the renderer.
        Args:
            periodic_callback: The periodic callback to add.
                it is created by `panel.state.add_periodic_callback`.
        '''
        periodic_callback = pn.state.add_periodic_callback(
            callback, 
            period=self._control['update_interval'],  # in ms
            start=False,
        )
        self._renderer.add_periodic_callback(periodic_callback)
    
    def _on_streaming_callback(self, msg: StreamingMessage) -> StreamingMessage:
        raise NotImplementedError(f"{self._class_name} does not support streaming")
    
    def _is_streaming_ready(self) -> bool:
        return bool(self._streaming_dfs)
    
    def _create_streaming_row(self, msg: StreamingMessage) -> nw.DataFrame[Any]:
        raise NotImplementedError(f"{self._class_name} does not support streaming")
    
    def _create_streaming_df(self, msg_key: MessageKey, msg: StreamingMessage) -> nw.DataFrame[Any]:
        raise NotImplementedError(f"{self._class_name} does not support streaming")
    
    def _truncate_streaming_df(self, df: nw.DataFrame[Any]) -> nw.DataFrame[Any]:
        assert self._control is not None, "control is not set"
        max_data = self._control['max_data']
        if max_data and df.shape[0] > max_data:
            df = df.tail(max_data)
        return df
        
    def _start_streaming(self):
        from pfeed.requests.market_feed_stream_request import MarketFeedStreamRequest

        assert self._feed is not None, "feed is not set"
        requests = cast(list[MarketFeedStreamRequest], self._feed._requests)
        assert all(request.is_streaming() for request in requests), "Not all requests in the streaming feed are for streaming"

        self._add_periodic_callback(self._refresh_streaming_ui)

        # add on_callback to the first of the custom_transformations list
        for request in self._feed._requests:
            transformations = self._feed._custom_transformations[request]
            self._feed._custom_transformations[request] = (
                self._on_streaming_callback,
                *transformations,
            )
        if self._notebook_type is None:
            self._streaming_thread = Thread(
                target=self._feed.run,
                daemon=True,
            )
            self._streaming_thread.start()
        else:
            asyncio.get_running_loop().create_task(self._feed.run_async())

        # start streaming for overlays that have their own feeds
        for overlay in self._overlays:
            if overlay._feed is not None:
                overlay._start_streaming()
    
    def _refresh_streaming_ui(self):
        '''during streaming, update pane and widgets accordingly using the newly updated data (updated in _on_streaming_callback)'''
        if self._df is not None and self._is_streaming_ready():
            self._update_pane(self._df)
            self._update_widgets(self._df)
            
    def _wait_for_streaming_ready(self):
        if self._feed is not None and self._df is None:
            while not self._is_streaming_ready():
                cprint("Not enough data to plot, waiting for streaming data...", style=TextStyle.BOLD + RichColor.YELLOW)
                time.sleep(1)
                
    async def _wait_for_streaming_ready_async(self):
        if self._feed is not None and self._df is None:
            while not self._is_streaming_ready():
                cprint("Not enough data to plot, waiting for streaming data...", style=TextStyle.BOLD + RichColor.YELLOW)
                await asyncio.sleep(1)
    
    def _render(self) -> RenderedResult:
        self._create()
        return self._renderer.render(self._component)
    
    def _render_sync(self) -> RenderedResult:
        if self._feed is not None:
            self._start_streaming()
            # NOTE: when streaming, need to wait for enough data before creating plot/pane etc.
            # otherwise the e.g. x-axis might be wrong and cannot be fixed once it's served
            self._wait_for_streaming_ready()
        return self._render()

    async def _render_async(self) -> RenderedResult:
        if self._feed is not None:
            self._start_streaming()
            await self._wait_for_streaming_ready_async()
        return self._render()

    @classmethod
    def set_style(cls, style: dict | None = None):
        """Set the class-level style for the plot."""
        cls._style = cls._create_style(style, cls._backend, cls.style)

    @staticmethod
    def _create_style(
        style: dict | None, backend: PlottingBackend, style_wrapper
    ) -> dict:
        if style_wrapper is None:
            return None

        default_style = getattr(style_wrapper, backend.value)()

        if style is None:
            return default_style

        if not isinstance(style, dict):
            raise ValueError("style must be a dictionary")

        return {**default_style, **style}

    def _set_style(self, style: Style | None = None):
        """Set the instance-level style for the plot."""
        self._style = self._create_style(style, self._backend, self.style)

    @classmethod
    def set_control(cls, control: Control | None = None):
        """Set the class-level control for the plot."""
        cls._control = cls._create_control(control, cls._backend, cls.control)

    @staticmethod
    def _create_control(
        control: Control | None, backend: PlottingBackend, control_wrapper
    ) -> Control | None:
        if control_wrapper is None:
            return None

        default_control = getattr(control_wrapper, backend.value)()

        if control is None:
            return default_control

        if not isinstance(control, dict):
            raise ValueError("control must be a dictionary")

        return {**default_control, **control}

    def _set_control(self, control: Control | None = None):
        """Set the instance-level control for the plot."""
        self._control = self._create_control(control, self._backend, self.control)

    @classmethod
    def set_backend(cls, backend: PlottingBackend | str):
        assert backend in cls.SUPPORTED_BACKENDS, (
            f"Backend {backend} is not in supported backends: {cls.SUPPORTED_BACKENDS}"
        )
        original_backend = cls._backend
        cls._backend = PlottingBackend[backend.lower()]
        is_backend_changed = original_backend != cls._backend
        # reset style and control if backend is changed
        if is_backend_changed or cls._style is None:
            cls.set_style()
        if is_backend_changed or cls._control is None:
            cls.set_control()

    def _set_backend(self, backend: PlottingBackend | str):
        """Set the instance-level backend for the plot."""
        assert backend in self.SUPPORTED_BACKENDS, (
            f"Backend {backend} is not in supported backends: {self.SUPPORTED_BACKENDS}"
        )
        original_backend = self._backend
        self._backend = PlottingBackend[backend.lower()]
        is_backend_changed = original_backend != self._backend
        # reset style and control if backend is changed
        if is_backend_changed or self._style is None:
            self._set_style()
        if is_backend_changed or self._control is None:
            self._set_control()

    @classmethod
    def set_mode(cls, mode: DisplayMode | str):
        assert mode in DisplayMode.__members__, (
            f"Mode {mode} is not in supported modes: {DisplayMode}"
        )
        cls._mode = DisplayMode[mode.lower()]

    def _set_mode(self, mode: DisplayMode | str):
        """Set the instance-level mode for the plot."""
        assert mode in DisplayMode.__members__, (
            f"Mode {mode} is not in supported modes: {DisplayMode}"
        )
        self._mode = DisplayMode[mode.lower()]
        self._set_renderer()
    
    @classmethod
    def remove_widgets(cls, *WidgetClasses: type[BaseWidget | BaseStreamingWidget]) -> None:
        for WidgetClass in WidgetClasses:
            if WidgetClass in cls._ChosenWidgetClasses:
                cls._ChosenWidgetClasses.remove(WidgetClass)
            if WidgetClass in cls._ChosenStreamingWidgetClasses:
                cls._ChosenStreamingWidgetClasses.remove(WidgetClass)
                
    def _remove_widgets(self, *WidgetClasses: type[BaseWidget | BaseStreamingWidget]) -> None:
        for WidgetClass in WidgetClasses:
            if WidgetClass in self._ChosenWidgetClasses:
                self._ChosenWidgetClasses.remove(WidgetClass)
            if WidgetClass in self._ChosenStreamingWidgetClasses:
                self._ChosenStreamingWidgetClasses.remove(WidgetClass)

    def _set_renderer(self):
        if self._mode == DisplayMode.notebook:
            from pfund_plot.renderers.notebook import NotebookRenderer

            self._renderer = NotebookRenderer()
        elif self._mode == DisplayMode.browser:
            from pfund_plot.renderers.browser import BrowserRenderer

            self._renderer = BrowserRenderer()
        elif self._mode == DisplayMode.desktop:
            from pfund_plot.renderers.desktop import DesktopRenderer

            self._renderer = DesktopRenderer()

    @property
    def _plot_func(self) -> Callable[[nw.DataFrame[Any], Style, Control], Plot]:
        """Runs the plot function for the current backend."""
        module_path = f"pfund_plot.plots.{self._class_name}.{self._backend}"
        module = importlib.import_module(module_path)
        return getattr(module, "plot")

    @property
    def figure(self) -> Figure:
        import hvplot

        if self._plot is None:
            self._create_plot()

        plot: Plot = self._plot
        backend = self._backend

        if backend == PlottingBackend.panel:
            raise ValueError("Panel backend does not support figure property")
        elif backend in [PlottingBackend.bokeh, PlottingBackend.plotly, PlottingBackend.matplotlib]:
            if self._is_hvplot(self._plot):
                # use hvplot to convert holoviews Overlay to the underlying plotting library's figure
                fig = hvplot.render(plot, backend=backend)
                if backend == PlottingBackend.plotly:
                    import plotly.graph_objects as go
                    # hvplot.render() returns a dict, convert it to a plotly Figure
                    fig: dict
                    fig = go.Figure(fig)
            else:  # plot is from plt.bokeh(), plt.plotly() or plt.matplotlib()
                plot: RawFigure
                fig = plot
        # TODO
        # elif self._backend == PlottingBackend.altair:
        #     pass
        else:
            raise ValueError(f"Unsupported backend: {backend}")
        return fig

    def _is_using_marimo_svelte_combo(self):
        return (
            self._backend == PlottingBackend.svelte
            and self._mode == DisplayMode.notebook
            and self._notebook_type == NotebookType.marimo
        )

    @staticmethod
    def _get_sizing_mode(height: int | None, width: int | None) -> str | None:
        if height is None and width is None:
            return "stretch_both"
        elif height is None:
            return "stretch_height"
        elif width is None:
            return "stretch_width"
        else:
            return None
    
    def _build_plot(self, df: nw.DataFrame[Any] | None = None) -> Plot:
        """Returns a plot object for the given data, composing overlays and opts if any."""
        df = df if df is not None else self._df
        result = self._plot_func(
            df=df,
            x=self._x,
            y=self._y,
            style=self._style,
            control=self._control,
        )
        if self._overlays:
            for overlay in self._overlays:
                overlay_plot = overlay._build_plot()
                if not self._is_hvplot(overlay_plot):
                    raise TypeError("Operation '*' only supports Holoviews plots.")
                result = result * overlay_plot
        if self._holoviews_opts:
            for args, kwargs in self._holoviews_opts:
                result = result.opts(*args, **kwargs)
        return result

    def _create_plot(self):
        self._plot = self._build_plot(df=self._df)

    def _create_pane(self):
        if self._control and self._control.get("num_data") is not None:
            df = self._df.tail(self._control["num_data"])
        else:
            df = self._df

        if self._plot is None:
            self._create_plot()

        backend = self._backend

        if backend == PlottingBackend.panel:
            # no pane needed for panel backend (e.g. GridStack, use it directly as a component)
            pass
        elif backend in [PlottingBackend.bokeh, PlottingBackend.plotly, PlottingBackend.matplotlib]:
            if self._is_hvplot(self._plot):
                from holoviews.streams import Pipe
                from holoviews import DynamicMap

                self._streaming_pipe = Pipe(data=df)
                dmap = DynamicMap(
                    lambda data: self._build_plot(df=data),
                    streams=[self._streaming_pipe],
                )
                self._pane = pn.pane.HoloViews(
                    dmap, linked_axes=self._control.get("linked_axes", True)
                )
            else:  # from plt.bokeh(), plt.plotly() or plt.matplotlib()
                # TODO: plotly and matplotlib should be able to use DynamicMap as well
                # see: https://www.holoviews.org/reference/containers/plotly/DynamicMap.html
                if backend == PlottingBackend.bokeh:
                    self._pane = pn.pane.Bokeh(self._plot)
                elif backend == PlottingBackend.plotly:
                    self._pane = pn.pane.Plotly(self._plot)
                elif backend == PlottingBackend.matplotlib:
                    self._pane = pn.pane.Matplotlib(self._plot)
        elif backend == PlottingBackend.svelte:
            if pn.extension._loaded_extensions:
                warnings.warn(
                    "Svelte backend may not work correctly with existing panel extensions. Restart kernel to fix if issues arise.",
                    stacklevel=1,
                )
            self._anywidget: AnyWidget = self._plot_func(df, self._style, self._control)
            self._pane = pn.pane.IPyWidget(self._anywidget)
        # TODO
        # elif backend == PlottingBackend.altair:
        #     self._pane = pn.pane.Vega(self._plot)
        else:
            raise ValueError(f"Unsupported backend: {backend}")
    
    def _is_overlay(self) -> bool:
        return self._parent_plot is not None

    def _update_pane(self, df: nw.DataFrame[Any]):
        if self._is_overlay():
            self._update_df(df)
            assert self._parent_plot._streaming_pipe is not None, (
                "Overlay widgets require the base plot to be rendered via a HoloViews pipe."
            )
            # NOTE: the overlay has no rendered pane — it's composited inside the parent's DynamicMap.
            # Re-send the parent's current pipe data to trigger a DynamicMap re-render,
            # which will call _build_plot → overlay._build_plot() with the updated overlay._df.
            # This is not passing new data; it's just a re-render trigger.
            self._parent_plot._streaming_pipe.send(self._parent_plot._streaming_pipe.data)
            return
        if self._pane is None:
            self._create_pane()
        if self._backend == PlottingBackend.bokeh:
            self._streaming_pipe.send(df)
        elif self._backend == PlottingBackend.svelte:
            assert self._anywidget is not None, "anywidget is not set"
            self._anywidget.update_data(df)
        else:
            raise ValueError(f"Unsupported backend: {self._backend}")
