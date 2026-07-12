#!/usr/bin/env python3
"""
PROJECT HERMES - Omnimind Absolute Edition
File: state.py
Monolithic Compilation Standard
"The earth and sky will break before I fail you."

Description:
This module contains the absolute state management for the HERMES Omnimind.
It provides a thread-safe core telemetry store and interface data registry.
All daemons write to this state, and all UI panels read from it.
It utilizes fixed-capacity ring buffers for historical telemetry tracking
to ensure bounded memory usage during infinite runtime loops.
"""

import threading
import time
from collections import deque
from typing import List, Optional, Dict, Any, Iterator

from config import Config


# ===========================================================================
# SECTION 4.1 — RingBuffer
# ===========================================================================
class RingBuffer:
    """
    Fixed-capacity FIFO ring buffer backed by collections.deque.
    Provides O(1) appends and pops, and automatically discards the oldest
    items when capacity is reached. Designed for high-frequency telemetry.
    """

    def __init__(self, capacity: int = 120) -> None:
        if capacity <= 0:
            raise ValueError("RingBuffer capacity must be a positive integer.")
        self.capacity = int(capacity)
        self._dq: deque = deque(maxlen=self.capacity)

    def push(self, value: float) -> None:
        """Push a new value into the buffer, evicting the oldest if full."""
        self._dq.append(float(value))

    def data(self) -> List[float]:
        """Return a list copy of the current buffer contents."""
        return list(self._dq)

    def latest(self) -> Optional[float]:
        """Return the most recently pushed value, or None if empty."""
        if not self._dq:
            return None
        return self._dq[-1]

    def oldest(self) -> Optional[float]:
        """Return the oldest value in the buffer, or None if empty."""
        if not self._dq:
            return None
        return self._dq[0]

    def is_full(self) -> bool:
        """Return True if the buffer is at maximum capacity."""
        return len(self._dq) == self.capacity

    def clear(self) -> None:
        """Remove all items from the buffer."""
        self._dq.clear()

    def __len__(self) -> int:
        return len(self._dq)

    def __iter__(self) -> Iterator[float]:
        return iter(self._dq)

    def __repr__(self) -> str:
        return f"RingBuffer(capacity={self.capacity}, size={len(self._dq)})"


# ===========================================================================
# SECTION 4.2 — HermesState
# ===========================================================================
class HermesState:
    """
    Thread-safe core telemetry and interface data store.
    
    Uses a reentrant lock (RLock) to allow nested locking if a thread
    needs to read multiple keys and set a derived key atomically.
    All data is stored in a single dictionary for fast snapshotting.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        
        # Initialize core data dictionary with default values
        self._data: Dict[str, Any] = {
            # Hardware telemetry
            "cpu_temp": 40.0,
            "cpu_usage": 0.0,
            "cpu_per_core": [],
            "ram_usage": 0.0,
            "disk_read_mb": 0.0,
            "disk_write_mb": 0.0,
            "net_sent_mb": 0.0,
            "net_recv_mb": 0.0,
            
            # Network telemetry
            "ping_ms": 0.0,
            "internet_up": False,
            
            # System scoring
            "stability_score": 100.0,
            "core_health": 100.0,
            "active_threads": 0,
            
            # Audio DSP
            "audio_fft": [0.0] * 64,
            "audio_volume": 0.0,
            
            # Voice/STT
            "transcript": "",
            "last_transcript": "",
            
            # LLM Cognitive Stream
            "llm_stream": "",
            "llm_full": "",
            
            # Scraped Data
            "news_items": [],
            "globe_coords": [],
            
            # Social & Security Feeds (Pre-seeded for boot visuals)
            "social_feeds": [
                {"user": "@P-SOCIAL", "msg": "New drone model verified [cite: P-SOCIAL]"},
                {"user": "@P-SOCIAL", "msg": "ARC reactor field test complete [cite: P-SOCIAL]"},
                {"user": "@STARK-NET", "msg": "Mark XLII suit telemetry uplink stable [cite: STARK-NET]"},
                {"user": "@AVENGERS", "msg": "Perimeter sweep negative, all clear [cite: AVENGERS]"},
            ],
            "security_alerts": [
                "SECURITY ALERT: PERIMETER BREACH SECTOR 7 [cite: ALARM]",
                "ARC REACTOR ANOMALY IN GEN-3 [cite: DIAGNOSTIC]",
                "UNKNOWN SIGNATURE DETECTED ON GRID [cite: SCAN]",
                "FIREWALL PROBE BLOCKED 128.91.x.x [cite: NETSEC]",
            ],
            
            # Daemon Override & Messaging
            "daemon_override": False,
            "daemon_msg": "",
            
            # Timing
            "boot_time": time.time(),
        }
        
        # Historical ring buffers for telemetry graphing
        self.temp_history = RingBuffer(Config.TEMP_HISTORY)
        self.ping_history = RingBuffer(Config.PING_HISTORY)
        self.cpu_history = RingBuffer(Config.CPU_HISTORY)
        self.ram_history = RingBuffer(Config.RAM_HISTORY)
        self.ekg_history = RingBuffer(Config.EKG_HISTORY)

    def get(self, key: str, default: Any = None) -> Any:
        """Thread-safe retrieval of a state value."""
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Thread-safe setting of a state value."""
        with self._lock:
            self._data[key] = value

    def update(self, updates: Dict[str, Any]) -> None:
        """Thread-safe bulk update of multiple state keys."""
        with self._lock:
            self._data.update(updates)

    def snapshot(self) -> Dict[str, Any]:
        """
        Fast non-blocking snapshot copy of all telemetry and history.
        This is used by the UI render loop to get a consistent state
        without blocking the daemon threads from writing.
        """
        with self._lock:
            snap = dict(self._data)
            # Copy history data into the snapshot to avoid passing references
            snap["temp_hist"] = self.temp_history.data()
            snap["ping_hist"] = self.ping_history.data()
            snap["cpu_hist"] = self.cpu_history.data()
            snap["ram_hist"] = self.ram_history.data()
            snap["ekg_hist"] = self.ekg_history.data()
            return snap

    def uptime_str(self) -> str:
        """Calculate and format system uptime as HH:MM:SS."""
        with self._lock:
            up = time.time() - self._data["boot_time"]
        h = int(up // 3600)
        m = int((up % 3600) // 60)
        s = int(up % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def push_history(self, temp: Optional[float] = None, ping: Optional[float] = None,
                     cpu: Optional[float] = None, ram: Optional[float] = None,
                     ekg: Optional[float] = None) -> None:
        """Helper to push multiple telemetry history values atomically."""
        with self._lock:
            if temp is not None:
                self.temp_history.push(temp)
            if ping is not None:
                self.ping_history.push(ping)
            if cpu is not None:
                self.cpu_history.push(cpu)
            if ram is not None:
                self.ram_history.push(ram)
            if ekg is not None:
                self.ekg_history.push(ekg)

    def __repr__(self) -> str:
        return f"<HermesState uptime={self.uptime_str()}>"