#!/usr/bin/env python3
"""
PROJECT HERMES - Omnimind Absolute Edition
File: palette.py
Monolithic Compilation Standard
"The earth and sky will break before I fail you."
"""

from typing import Tuple

BLACK = (0, 0, 0)
WHITE = (235, 235, 235)
CYAN = (180, 220, 230)
AMBER = (220, 200, 150)
ALERT = (255, 90, 70)
INK = (170, 170, 170)
GRID = (45, 45, 45)
DIM = (70, 70, 70)
STRUCT = (90, 90, 90)
MUTED = (110, 110, 110)


def with_alpha(color: Tuple[int, int, int], alpha: int) -> Tuple[int, int, int, int]:
    """Attach alpha channel to an RGB triple."""
    r, g, b = color[0], color[1], color[2]
    return (r, g, b, max(0, min(255, alpha)))


def mix(c1: Tuple[int, int, int], c2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    """Linear blend between two colors. t in [0,1]."""
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def depth_shade(base: Tuple[int, int, int], depth_t: float) -> Tuple[int, int, int]:
    """Fade a base color toward black based on normalized depth [0,1].
    0 = near (full brightness), 1 = far (faded)."""
    depth_t = max(0.0, min(1.0, depth_t))
    return mix(base, BLACK, depth_t * 0.82)