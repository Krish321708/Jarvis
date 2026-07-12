#!/usr/bin/env python3
"""
PROJECT HERMES - Omnimind Absolute Edition
File: config.py
Monolithic Compilation Standard
"The earth and sky will break before I fail you."
"""

import os
import math
import time

class Config:
    """Static configuration registry. No executable logic."""
    # Display
    WIDTH = 1920
    HEIGHT = 810
    FPS = 60

    # Thread poll rates (seconds)
    HARDWARE_POLL = 1.0
    NETWORK_POLL = 1.0
    SCRAPER_POLL = 60.0
    PROACTIVE_POLL = 1.0
    AUDIO_CHUNK = 1024
    AUDIO_RATE = 44100

    # Math constants
    FOCAL_LENGTH = 420.0
    GRID_SPACING = 1.0
    GRID_SIZE = 48
    CAMERA_PITCH = math.radians(38)
    CAMERA_DEPTH = 18.0
    GLOBE_RADIUS = 88
    GLOBE_POINTS = 480
    GLOBE_YAW_RATE = 0.4
    GLOBE_PITCH_TILT = math.radians(22)
    PERLIN_OCTAVES = 5
    PERLIN_PERSISTENCE = 0.5
    PERLIN_LACUNARITY = 2.0

    # Safety thresholds
    TEMP_CRITICAL = 85.0
    RAM_CRITICAL = 90.0
    STABILITY_MIN = 60.0
    PING_TIMEOUT = 3.0

    # OpenRouter cognitive API
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    OPENROUTER_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"

    # Viewport geometric bounds (x0, y0, x1, y1)
    HEADER = (0, 0, 1920, 44)
    LEFT_VIEWPORT = (0, 44, 1248, 631)
    RIGHT_TOP_VIEWPORT = (1248, 44, 1920, 405)
    RIGHT_BOTTOM_VIEWPORT = (1248, 405, 1920, 810)
    BOTTOM_ROW = (0, 631, 1920, 810)

    # Sub-panel widths in bottom row
    BOTTOM_PANEL_W = 480
    BOTTOM_PANEL_H = 179

    # Ring buffer sizes
    TEMP_HISTORY = 120
    PING_HISTORY = 120
    CPU_HISTORY = 120
    RAM_HISTORY = 120
    EKG_HISTORY = 240