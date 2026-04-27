"""Reactive graph core inspired by Preact Signals.

Edge-based dependency tracking with versioned producers and
lazy subscription. Not part of the public API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol, Union
import contextvars
import weakref

# ---------------------------------------------------------------------------
# Flags (bit mask) shared by ComputeSignal / Effect
# ---------------------------------------------------------------------------
RUNNING = 1 << 0
NOTIFIED = 1 << 1
OUTDATED = 1 << 2
DISPOSED = 1 << 3
HAS_ERROR = 1 << 4
TRACKING = 1 << 5

# ---------------------------------------------------------------------------
# Global reactive state
# ---------------------------------------------------------------------------
active_consumer: contextvars.ContextVar[Optional["_Consumer"]] = contextvars.ContextVar(
    "active_consumer", default=None
)

global_version = 0  # incremented whenever a writable signal changes
batch_depth = 0
batch_iteration = 0  # cycle guard similar to preact
MAX_BATCH_ITERATIONS = 100


# Batched effect linked list head (set by Effect)
class _BatchedEffect(Protocol):
    _next_batched_effect: Optional["_BatchedEffect"]
    _flags: int

    def _needs_run(self) -> bool: ...
    def _run_callback(self) -> None: ...


batched_effect_head: Optional[_BatchedEffect] = None


# ---------------------------------------------------------------------------
# Protocols for participants
# ---------------------------------------------------------------------------
class _Consumer(Protocol):
    _sources: Optional["Edge"]
    _flags: int

    def _notify(self) -> None: ...


class _Producer(Protocol):
    _version: int
    _targets: Optional["Edge"]
    _node: Optional["Edge"]

    def _subscribe_edge(self, edge: "Edge") -> None: ...
    def _unsubscribe_edge(self, edge: "Edge") -> None: ...
    def _refresh(self) -> bool: ...


# ---------------------------------------------------------------------------
# Edge node connecting a producer to a consumer
# ---------------------------------------------------------------------------
@dataclass
class Edge:
    source: _Producer
    _target_ref: Union[_Consumer, "weakref.ref[_Consumer]"] = field(repr=False)
    prev_source: Optional["Edge"] = None
    next_source: Optional["Edge"] = None
    prev_target: Optional["Edge"] = None
    next_target: Optional["Edge"] = None
    version: int = 0  # last seen producer version (-1 reusable)
    rollback_node: Optional["Edge"] = None

    @property
    def target(self) -> Optional[_Consumer]:
        """Get the target consumer, dereferencing weakref if needed."""
        pass

    def is_alive(self) -> bool:
        """Check if the target is still alive."""
        pass


# ---------------------------------------------------------------------------
# Dependency management
# ---------------------------------------------------------------------------


def _is_effect(consumer: _Consumer) -> bool:
    """Check if consumer is an Effect."""
    pass


def _create_edge_with_weakref_cleanup(source: _Producer, consumer: _Consumer, prev_head: Optional[Edge]) -> Edge:
    """Create an Edge with weakref for Effects and cleanup callback."""
    pass


def add_dependency(source: _Producer) -> Optional[Edge]:
    pass


# ---------------------------------------------------------------------------
# Source list lifecycle
# ---------------------------------------------------------------------------


def prepare_sources(target: _Consumer) -> None:
    pass


def cleanup_sources(target: _Consumer) -> None:
    pass


# ---------------------------------------------------------------------------
# Recompute heuristic
# ---------------------------------------------------------------------------


def needs_to_recompute(target: _Consumer) -> bool:
    pass


# ---------------------------------------------------------------------------
# Active consumer management
# ---------------------------------------------------------------------------


def set_active_consumer(consumer: Optional[_Consumer]) -> Optional[_Consumer]:
    pass
