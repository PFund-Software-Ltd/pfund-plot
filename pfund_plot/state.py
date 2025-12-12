from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pfund_plot._typing import Component
    from panel.io.callbacks import PeriodicCallback
    
from threading import Lock
from dataclasses import dataclass, field


@dataclass
class LayoutState:
    in_layout: bool = False
    streaming: bool = False
    components: list[Component] = field(default_factory=list)
    periodic_callbacks: list[PeriodicCallback] = field(default_factory=list)

    def add(self, *components):
        """Add components to the layout"""
        self.components.extend(components)
    
    def add_periodic_callback(self, periodic_callback: PeriodicCallback):
        self.periodic_callbacks.append(periodic_callback)


class RuntimeState:
    _instance: RuntimeState | None = None
    _lock = Lock()

    def __init__(self):
        self.layout = LayoutState()

    @classmethod
    def get_instance(cls) -> RuntimeState:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def reset_layout(self):
        self.layout = LayoutState()

# Global instance
state = RuntimeState.get_instance()