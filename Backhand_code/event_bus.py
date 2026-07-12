#!/usr/bin/env python3
"""
PROJECT HERMES - Omnimind Absolute Edition
File: event_bus.py
Monolithic Compilation Standard
"The earth and sky will break before I fail you."

Description:
This module implements a lightweight, asynchronous Event Bus for decoupled
communication between system daemons and the core application controller.
It allows threads to publish events and register handlers without needing
direct references to each other, maintaining a strict separation of concerns.
"""

import threading
from typing import Dict, List, Callable, Any, Optional


class EventBus:
    """
    Asynchronous event publish/subscribe mechanism with thread-safe dispatch.
    
    Daemons emit events (e.g., 'hardware.tick', 'voice.transcript') and the
    application controller or other listeners subscribe to these topics.
    Exceptions in handlers are caught and swallowed to ensure a single
    failing listener does not crash the dispatching thread.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._subs: Dict[str, List[Callable[[Any], None]]] = {}

    def subscribe(self, topic: str, handler: Callable[[Any], None]) -> None:
        """
        Subscribe a handler function to a specific topic.
        
        Args:
            topic: The event name to listen for (e.g., 'network.tick').
            handler: A callable that accepts a single payload argument.
        """
        if not callable(handler):
            raise TypeError("EventBus handler must be callable")
            
        with self._lock:
            if topic not in self._subs:
                self._subs[topic] = []
            # Prevent duplicate subscriptions of the exact same function
            if handler not in self._subs[topic]:
                self._subs[topic].append(handler)

    def unsubscribe(self, topic: str, handler: Callable[[Any], None]) -> None:
        """
        Unsubscribe a handler from a specific topic.
        
        Args:
            topic: The event name.
            handler: The callable to remove.
        """
        with self._lock:
            if topic in self._subs:
                try:
                    self._subs[topic].remove(handler)
                    # Clean up empty lists to prevent memory leaks over long runtimes
                    if not self._subs[topic]:
                        del self._subs[topic]
                except ValueError:
                    # Handler not in list, silently ignore
                    pass

    def publish(self, topic: str, payload: Any = None) -> None:
        """
        Publish an event to all subscribers of a topic.
        
        This method iterates over a snapshot of the handlers to allow
        handlers themselves to unsubscribe without causing iteration errors.
        
        Args:
            topic: The event name to publish.
            payload: The data to pass to the handler functions.
        """
        # Snapshot the handlers list under the lock to ensure thread safety
        # during iteration, allowing handlers to modify subscriptions safely.
        with self._lock:
            handlers = list(self._subs.get(topic, []))
            
        for h in handlers:
            try:
                h(payload)
            except Exception:
                # In a production environment, this would log to a file.
                # Here, we swallow the exception to protect the daemon thread.
                pass

    def clear(self) -> None:
        """Remove all subscriptions from the event bus."""
        with self._lock:
            self._subs.clear()

    def listener_count(self, topic: Optional[str] = None) -> int:
        """
        Return the number of listeners for a specific topic, or total listeners
        if no topic is provided.
        """
        with self._lock:
            if topic:
                return len(self._subs.get(topic, []))
            return sum(len(handlers) for handlers in self._subs.values())

    def __repr__(self) -> str:
        with self._lock:
            topics = len(self._subs)
            total = sum(len(h) for h in self._subs.values())
        return f"<EventBus topics={topics} total_handlers={total}>"