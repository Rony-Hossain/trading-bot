from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Protocol, TypeVar, runtime_checkable

from ..base_types.types import BaseMessage  # your BaseMessage / Command / Event base


MessageT = TypeVar("MessageT", bound=BaseMessage)


@runtime_checkable
class ReactorQueue(Protocol[MessageT]):
    """
    Minimal interface for the single-threaded reactor queue.

    Implementations can wrap:
      - queue.Queue[BaseMessage]
      - asyncio.Queue[BaseMessage]
      - a custom ring buffer

    The adapter, engine, and processors should all depend on THIS,
    not on a concrete queue implementation.
    """

    def put(self, message: MessageT) -> None:
        """
        Enqueue a message (Command/Event) to be processed by the reactor.

        Must be thread-safe: adapters will push from broker callbacks while
        the reactor thread consumes.
        """
        ...

    def get(self, block: bool = True, timeout: Optional[float] = None) -> MessageT:
        """
        Dequeue the next message.

        - In the reactor thread, you typically call get(block=True).
        - Tests may call get(block=False) to assert queue emptiness.
        """
        ...

    def qsize(self) -> int:
        """Return approximate queue size (for monitoring / tests)."""
        ...

    def empty(self) -> bool:
        """Return True if the queue is currently empty."""
        ...

    def clear(self) -> None:
        """
        Optional: clear all pending messages.

        Useful in tests or during controlled shutdowns.
        Implementations may raise NotImplementedError if unsupported.
        """
        ...


class ReactorInterface(ABC):
    """
    Abstract interface for the single-threaded OMS reactor.

    Responsibility:
      - Own a ReactorQueue[BaseMessage]
      - Run the main `while True: msg = queue.get(); dispatch(msg)` loop
      - Ensure only ONE writer mutates DB / OrderState (single-writer invariant)
    """

    @abstractmethod
    def start(self) -> None:
        """
        Start the reactor loop.

        Typically:
          - run in its own thread
          - block until stop() is called or a fatal error occurs
        """
        ...

    @abstractmethod
    def stop(self) -> None:
        """
        Stop the reactor loop gracefully.

        Implementation detail:
          - may use a sentinel message
          - or a shutdown flag + dummy wakeup
        """
        ...

    @abstractmethod
    def queue(self) -> ReactorQueue[MessageT]:
        """
        Access the underlying message queue.

        Adapters and the engine will use this to enqueue Commands/Events.
        """
        ...
