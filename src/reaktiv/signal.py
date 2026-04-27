"""Writable Signal implementation.

Migrated to Edge-based dependency tracking and minimal scheduler.
"""

from __future__ import annotations

import threading
from typing import Callable, Generic, Optional, TypeVar, Union, cast, overload

from ._debug import debug_log
from . import graph
from .scheduler import start_batch, end_batch
from .thread_safety import is_thread_safety_enabled

T = TypeVar("T")


class Signal(Generic[T]):
    """A reactive writable signal that notifies dependents when its value changes.
    
    Signal is the core building block in reaktiv. It creates a container for values
    that can change over time and automatically notify effects and computed signals
    that depend on it.
    
    Args:
        value: The initial value of the signal
        equal: Optional custom equality function to determine if two values should be 
            considered equal. By default, identity (`is`) is used.
    
    Examples:
        Basic usage:
        ```python
        from reaktiv import Signal
        
        # Create a signal with an initial value
        counter = Signal(0)
        
        # Get the current value
        value = counter()  # 0
        
        # Set a new value
        counter.set(5)
        
        # Update using a function
        counter.update(lambda x: x + 1)  # Now 6
        ```
        
        Custom equality:
        ```python
        from reaktiv import Signal
        
        # Custom equality function for dictionaries
        def dict_equal(a, b):
            return isinstance(a, dict) and isinstance(b, dict) and a == b
        
        user = Signal({"name": "Alice", "age": 30}, equal=dict_equal)
        
        # This won't trigger updates (same key-value pairs)
        user.set({"name": "Alice", "age": 30})
        
        # This will trigger updates (different age)
        user.set({"name": "Alice", "age": 31})
        ```
        
        Readonly wrapper:
        ```python
        from reaktiv import Signal
        
        # Internal writable signal
        _counter = Signal(0)
        
        # Expose readonly view
        counter = _counter.as_readonly()
        
        def increment():
            _counter.update(lambda x: x + 1)
        
        print(counter())  # 0
        increment()
        print(counter())  # 1
        # counter.set(5)  # Error: ReadonlySignal has no 'set' method
        ```
    """

    __slots__ = (
        "_value",
        "_equal",
        "_readonly_cache",
        "_version",
        "_targets",
        "_node",
        "_lock",
    )

    def __init__(self, value: T, *, equal: Optional[Callable[[T, T], bool]] = None):
        """Initialize a new Signal with an initial value.
        
        Args:
            value: The initial value of the signal
            equal: Optional custom equality function. If provided, it will be used to
                determine if a new value is different from the current value. If not
                provided, identity comparison (`is`) is used.
        """
        self._value = value
        self._equal = equal
        self._readonly_cache: Optional[ReadonlySignal[T]] = None
        self._version: int = 0
        self._targets: Optional[graph.Edge] = None
        self._node: Optional[graph.Edge] = None
        # RLock for thread-safe operations - only when thread safety is enabled
        self._lock = threading.RLock() if is_thread_safety_enabled() else None
        debug_log(f"Signal initialized with value: {value}")

    def __repr__(self) -> str:
        try:
            return f"Signal(value={repr(self._value)})"
        except Exception as e:
            return f"Signal(error_displaying_value: {str(e)})"

    def __call__(self) -> T:
        return self.get()

    # Producer API expected by graph core
    def _subscribe_edge(self, edge: graph.Edge) -> None:
        pass

    def _unsubscribe_edge(self, edge: graph.Edge) -> None:
        pass

    def _refresh(self) -> bool:
        pass

    def get(self) -> T:
        """Get the current value of the signal.
        
        When called within an active effect or computed signal, it establishes a 
        dependency relationship, so changes to this signal will notify the dependent.
        
        Returns:
            The current value of the signal
            
        Examples:
            ```python
            counter = Signal(42)
            value = counter.get()  # 42
            # Or use the callable syntax
            value = counter()      # 42
            ```
        """
        pass

    def set(self, new_value: T) -> None:
        """Set a new value for the signal and notify subscribers if it changed.
        
        A notification is triggered only if the new value is considered different
        from the current value. By default, identity comparison (`is`) is used
        unless a custom equality function was provided.
        
        Args:
            new_value: The new value to set
            
        Raises:
            RuntimeError: If called from within a ComputeSignal computation
            
        Examples:
            ```python
            counter = Signal(0)
            counter.set(5)
            print(counter())  # 5
            
            # Setting the same value (by identity) won't trigger updates
            obj = {"x": 1}
            signal = Signal(obj)
            signal.set(obj)  # No notification
            signal.set({"x": 1})  # Notification (different object)
            ```
        """
        pass

    def _set_internal(self, new_value: T) -> None:
        """Internal set method that does the actual work without locking."""
        pass

    def update(self, update_fn: Callable[[T], T]) -> None:
        """Atomically update the signal using a function of its current value.
        
        This method is useful for updates that depend on the current value,
        such as incrementing a counter or modifying an object.
        
        Args:
            update_fn: A function that takes the current value and returns the new value
            
        Examples:
            ```python
            counter = Signal(0)
            counter.update(lambda x: x + 1)
            print(counter())  # 1
            
            counter.update(lambda x: x * 2)
            print(counter())  # 2
            
            # Works with any type
            name = Signal("Alice")
            name.update(lambda s: s.upper())
            print(name())  # "ALICE"
            ```
        """
        pass

    def as_readonly(self) -> "ReadonlySignal[T]":
        """Return a readonly wrapper that exposes only read access to this signal.
        
        Useful for encapsulation when you want to share a value but prevent
        external code from mutating it.
        
        Returns:
            A ReadonlySignal that wraps this signal
            
        Examples:
            ```python
            # Keep internal signal private
            _counter = Signal(0)
            
            # Expose readonly view
            counter = _counter.as_readonly()
            
            def increment():
                _counter.update(lambda x: x + 1)
            
            print(counter())  # 0
            increment()
            print(counter())  # 1
            # counter.set(5)  # AttributeError: 'ReadonlySignal' has no attribute 'set'
            ```
        """
        pass


class ReadonlySignal(Generic[T]):
    """A readonly wrapper around a Signal that prevents modification.
    
    ReadonlySignal provides only read access (`get()` and `__call__()`) to the 
    underlying signal, preventing direct modification. Useful for encapsulation
    and API design.
    
    Note:
        You typically don't create ReadonlySignal directly. Use `Signal.as_readonly()` instead.
        
    Examples:
        ```python
        from reaktiv import Signal
        
        _counter = Signal(0)
        counter = _counter.as_readonly()
        
        # Can read
        print(counter())  # 0
        
        # Cannot write
        # counter.set(5)  # AttributeError
        ```
    """

    __slots__ = ("_signal",)

    def __init__(self, signal: Signal[T]):
        self._signal = signal

    def __repr__(self) -> str:
        try:
            return f"ReadonlySignal(value={repr(self._signal._value)})"
        except Exception as e:
            return f"ReadonlySignal(error_displaying_value: {str(e)})"

    def __call__(self) -> T:
        return self.get()

    def get(self) -> T:
        """Get the current value of the underlying signal.
        
        Returns:
            The current value
        """
        pass


class ComputeSignal(Signal[T]):
    """A computed signal that derives its value from other signals.
    
    ComputeSignal automatically tracks dependencies on other signals and recomputes
    its value when any dependency changes. Computations are lazy and cached - they
    only run when accessed and dependencies have changed.
    
    Args:
        compute_fn: A function that computes the signal's value from other signals
        equal: Optional custom equality function for change detection
        
    Examples:
        Basic computed signal:
        ```python
        from reaktiv import Signal, Computed
        
        first_name = Signal("John")
        last_name = Signal("Doe")
        
        # Create computed signal
        full_name = Computed(lambda: f"{first_name()} {last_name()}")
        
        print(full_name())  # "John Doe"
        
        first_name.set("Jane")
        print(full_name())  # "Jane Doe"
        ```
        
        Lazy computation:
        ```python
        from reaktiv import Signal, Computed
        
        x = Signal(10)
        y = Signal(20)
        
        def expensive_computation():
            print("Computing...")
            return x() * y()
        
        result = Computed(expensive_computation)
        
        # Nothing happens yet - computation is lazy
        
        # First access - computation runs
        print(result())  # Prints: "Computing..." then "200"
        
        # Second access - no computation (cached)
        print(result())  # Just prints "200"
        
        # Change a dependency
        x.set(5)
        
        # Next access will recompute
        print(result())  # Prints: "Computing..." then "100"
        ```
        
        Decorator pattern:
        ```python
        from reaktiv import Signal, Computed
        
        price = Signal(100)
        quantity = Signal(2)
        
        @Computed
        def total():
            return price() * quantity()
        
        print(total())  # 200
        ```
        
        Error handling:
        ```python
        from reaktiv import Signal, Computed
        
        x = Signal(10)
        
        # Computed signal with potential error
        result = Computed(lambda: 100 / x())
        
        print(result())  # 10.0 (100 / 10)
        
        # Set x to 0, causing division by zero
        x.set(0)
        
        # Exception is propagated to caller
        try:
            print(result())
        except ZeroDivisionError as e:
            print(f"Error: {e}")
        
        # After fixing, computation works again
        x.set(5)
        print(result())  # 20.0 (100 / 5)
        ```
        
    Note:
        Computed signals are lazy - they only compute when accessed and cache the
        result until dependencies change. When a computation raises an exception,
        it is propagated to the caller for flexible error handling.
    """

    __slots__ = (
        "_fn",
        "_sources",
        "_global_version_seen",
        "_flags",
        "_last_error",
        "_dependencies",
        "_thread_local",
        "_computation_lock",
    ) + Signal.__slots__

    def __init__(
        self,
        compute_fn: Callable[[], T],
        *,
        equal: Optional[Callable[[T, T], bool]] = None,
    ):
        super().__init__(None, equal=equal)  # type: ignore[arg-type]
        self._fn = compute_fn
        # Explicit typing for consumer sources list
        self._sources: Optional[graph.Edge] = None
        self._global_version_seen: int = graph.global_version - 1
        self._flags: int = graph.OUTDATED
        self._last_error: Optional[BaseException] = None
        self._dependencies: set[object] = set()
        # Thread-local storage for tracking running state per thread
        self._thread_local = threading.local()
        # RLock for thread-safe computation - only when thread safety is enabled
        self._computation_lock = (
            threading.RLock() if is_thread_safety_enabled() else None
        )

    def _is_running_in_current_thread(self) -> bool:
        """Check if this signal is currently being computed in the current thread."""
        pass

    def _set_running_in_current_thread(self, running: bool) -> None:
        """Set the running state for the current thread."""
        pass

    # Producer API (override to detect first/last subscriber)
    def _subscribe_edge(self, edge: graph.Edge) -> None:
        pass

    def _unsubscribe_edge(self, edge: graph.Edge) -> None:
        pass

    # Consumer refresh logic
    def _refresh(self) -> bool:
        # clear NOTIFIED
        pass

    def _notify(self) -> None:
        pass

    def get(self) -> T:
        # Thread-safe circular dependency detection
        pass

    def set(self, new_value: T) -> None:
        raise AttributeError("Cannot manually set value of ComputeSignal")


# Decorator overloads for Computed
@overload
def Computed(func: Callable[[], T], /) -> ComputeSignal[T]: ...


@overload
def Computed(
    func: Callable[[], T], /, *, equal: Callable[[T, T], bool]
) -> ComputeSignal[T]: ...


@overload
def Computed(
    *, equal: Callable[[T, T], bool]
) -> Callable[[Callable[[], T]], ComputeSignal[T]]: ...


def Computed(
    func: Optional[Callable[[], T]] = None,
    /,
    *,
    equal: Optional[Callable[[T, T], bool]] = None,
) -> Union[ComputeSignal[T], Callable[[Callable[[], T]], ComputeSignal[T]]]:
    """Create a computed signal that derives its value from other signals.
    
    Can be used as a function or as a decorator (with or without parameters).
    
    Args:
        func: The computation function (when used as factory or decorator without params)
        equal: Optional custom equality function for change detection
        
    Returns:
        A ComputeSignal instance or a decorator function
        
    Examples:
        As a function:
        ```python
        from reaktiv import Signal, Computed
        
        x = Signal(10)
        result = Computed(lambda: x() * 2)
        print(result())  # 20
        ```
        
        As a decorator (no parameters):
        ```python
        from reaktiv import Signal, Computed
        
        price = Signal(100)
        quantity = Signal(2)
        
        @Computed
        def total():
            return price() * quantity()
        
        print(total())  # 200
        ```
        
        As a decorator (with custom equality):
        ```python
        from reaktiv import Signal, Computed
        
        items = Signal([1, 2, 3])
        
        @Computed(equal=lambda a, b: a == b)
        def sorted_items():
            return sorted(items())
        
        print(sorted_items())  # [1, 2, 3]
        ```
    """
    pass
