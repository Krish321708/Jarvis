#!/usr/bin/env python3
"""
PROJECT HERMES - Omnimind Absolute Edition
File: ui_widgets.py
Monolithic Compilation Standard
"The earth and sky will break before I fail you."

Description:
This module provides the structural drawing primitives and base UI containers
for the HERMES Omnimind HUD. It includes advanced text rendering, word-wrapping,
geometric primitives, anti-aliased line drawing, and base Panel classes.
All functions are designed for high-performance immediate-mode rendering
against Pygame surfaces.
"""

import math
from typing import List, Tuple, Optional, Dict, Any, Sequence

from config import Config
from palette import BLACK, WHITE, CYAN, AMBER, ALERT, INK, GRID, DIM, STRUCT, MUTED, mix, depth_shade

try:
    import pygame
    import pygame.gfxdraw
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False
    pygame = None
    pygame.gfxdraw = None


# ===========================================================================
# SECTION 7.1 — Base Panel Container
# ===========================================================================
class Panel:
    """
    Base container for sub-viewport rendering with bracketed borders.
    Manages geometric bounds and provides utilities for clearing and framing.
    """
    def __init__(self, x: int, y: int, w: int, h: int) -> None:
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def rect(self) -> Tuple[int, int, int, int]:
        """Returns Pygame rect tuple (x, y, w, h)."""
        return (self.x, self.y, self.w, self.h)

    def clear(self, surface: "pygame.Surface", color: Tuple[int, int, int] = BLACK) -> None:
        """Clear the panel area to a solid color."""
        surface.fill(color, self.rect())

    def draw_brackets(self, surface: "pygame.Surface",
                      length: int = 16, thickness: int = 1,
                      color: Tuple[int, int, int] = STRUCT) -> None:
        """Draws futuristic corner brackets around the panel bounds."""
        x0, y0, x1, y1 = self.x, self.y, self.x + self.w, self.y + self.h
        
        # top-left
        pygame.draw.line(surface, color, (x0, y0), (x0 + length, y0), thickness)
        pygame.draw.line(surface, color, (x0, y0), (x0, y0 + length), thickness)
        # top-right
        pygame.draw.line(surface, color, (x1 - length, y0), (x1, y0), thickness)
        pygame.draw.line(surface, color, (x1, y0), (x1, y0 + length), thickness)
        # bottom-left
        pygame.draw.line(surface, color, (x0, y1), (x0 + length, y1), thickness)
        pygame.draw.line(surface, color, (x0, y1 - length), (x0, y1), thickness)
        # bottom-right
        pygame.draw.line(surface, color, (x1 - length, y1), (x1, y1), thickness)
        pygame.draw.line(surface, color, (x1, y1 - length), (x1, y1), thickness)

    def draw_border(self, surface: "pygame.Surface",
                    thickness: int = 1,
                    color: Tuple[int, int, int] = STRUCT) -> None:
        """Draws a continuous rectangular border around the panel."""
        pygame.draw.rect(surface, color, self.rect(), thickness)

    def get_clipped_surface(self, parent_surface: "pygame.Surface") -> "pygame.Surface":
        """Returns a subsurface of the parent bounded by this panel."""
        return parent_surface.subsurface(self.rect())


# ===========================================================================
# SECTION 7.2 — Typography & Text Utilities
# ===========================================================================

def wrap_text(text: str, font: "pygame.font.Font", max_width: int) -> List[str]:
    """
    Word-wrap text to fit within max_width pixels.
    Handles hard-breaking words that exceed max_width on their own.
    """
    words = text.split(" ")
    lines = []
    current = ""
    
    for word in words:
        test = word if not current else current + " " + word
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            # Hard-break long words
            while font.size(word)[0] > max_width and len(word) > 1:
                cut = len(word)
                while cut > 1 and font.size(word[:cut])[0] > max_width:
                    cut -= 1
                lines.append(word[:cut])
                word = word[cut:]
            current = word
            
    if current:
        lines.append(current)
    return lines


def measure_text(font: "pygame.font.Font", text: str) -> Tuple[int, int]:
    """Returns the width and height of a string in the given font."""
    return font.size(text)


def draw_text(surface: "pygame.Surface", font: "pygame.font.Font", text: str,
              pos: Tuple[int, int], color: Tuple[int, int, int] = WHITE,
              right_align: bool = False, center_align: bool = False) -> None:
    """
    Renders a single line of text at pos.
    Pos is topleft by default, top-right if right_align, mid-top if center_align.
    """
    img = font.render(text, True, color)
    rect = img.get_rect()
    
    if right_align:
        rect.topright = pos
    elif center_align:
        rect.midtop = pos
    else:
        rect.topleft = pos
        
    surface.blit(img, rect)


def draw_text_wrapped(surface: "pygame.Surface", font: "pygame.font.Font", text: str,
                      pos: Tuple[int, int], max_width: int,
                      color: Tuple[int, int, int] = WHITE,
                      line_spacing: int = 2) -> int:
    """
    Renders multi-line wrapped text starting at pos.
    Returns the Y coordinate of the next available line after rendering.
    """
    lines = wrap_text(text, font, max_width)
    x, y = pos
    for line in lines:
        img = font.render(line, True, color)
        surface.blit(img, (x, y))
        y += img.get_height() + line_spacing
    return y


def draw_text_vertical(surface: "pygame.Surface", font: "pygame.font.Font", text: str,
                       pos: Tuple[int, int], color: Tuple[int, int, int] = WHITE,
                       spacing: int = 1) -> None:
    """Renders text vertically (top to bottom), character by character."""
    x, y = pos
    for char in text:
        img = font.render(char, True, color)
        surface.blit(img, (x, y))
        y += img.get_height() + spacing


def draw_scrolling_text(surface: "pygame.Surface", font: "pygame.font.Font", text: str,
                        pos: Tuple[int, int], max_width: int, scroll_offset: int,
                        color: Tuple[int, int, int] = WHITE) -> None:
    """
    Renders a horizontal scrolling text line if it exceeds max_width.
    scroll_offset determines how many pixels the text has shifted left.
    """
    img = font.render(text, True, color)
    img_w = img.get_width()
    
    if img_w <= max_width:
        surface.blit(img, pos)
        return

    # Create a temporary surface for clipping
    clip_surf = pygame.Surface((max_width, img.get_height()), pygame.SRCALPHA)
    
    # Loop the text seamlessly
    offset = scroll_offset % (img_w + 50)  # 50px gap between loops
    clip_surf.blit(img, (-offset, 0))
    if offset > (img_w - max_width):
        clip_surf.blit(img, (img_w - offset + 50, 0))
        
    surface.blit(clip_surf, pos)


# ===========================================================================
# SECTION 7.3 — Geometric Primitives & Lines
# ===========================================================================

def draw_dashed_h(surface: "pygame.Surface", y: int, x0: int, x1: int,
                  dash: int = 6, gap: int = 4,
                  color: Tuple[int, int, int] = DIM) -> None:
    """Draws a horizontal dashed line."""
    x = x0
    while x < x1:
        x2 = min(x1, x + dash)
        pygame.draw.line(surface, color, (x, y), (x2, y), 1)
        x = x2 + gap


def draw_dashed_v(surface: "pygame.Surface", x: int, y0: int, y1: int,
                  dash: int = 6, gap: int = 4,
                  color: Tuple[int, int, int] = DIM) -> None:
    """Draws a vertical dashed line."""
    y = y0
    while y < y1:
        y2 = min(y1, y + dash)
        pygame.draw.line(surface, color, (x, y), (x, y2), 1)
        y = y2 + gap


def draw_dashed_line(surface: "pygame.Surface", p0: Tuple[int, int], p1: Tuple[int, int],
                     dash: int = 6, gap: int = 4,
                     color: Tuple[int, int, int] = DIM) -> None:
    """Draws a dashed line between two arbitrary points."""
    x0, y0 = p0
    x1, y1 = p1
    
    dx = x1 - x0
    dy = y1 - y0
    dist = math.hypot(dx, dy)
    
    if dist == 0:
        return
        
    # Normalized direction vector
    nx, ny = dx / dist, dy / dist
    
    d = 0.0
    while d < dist:
        d_end = min(dist, d + dash)
        sx = x0 + nx * d
        sy = y0 + ny * d
        ex = x0 + nx * d_end
        ey = y0 + ny * d_end
        pygame.draw.line(surface, color, (sx, sy), (ex, ey), 1)
        d += dash + gap


def draw_grid(surface: "pygame.Surface", rect: Tuple[int, int, int, int],
              spacing: int = 20, color: Tuple[int, int, int] = GRID) -> None:
    """Draws a rectangular grid within the given bounds."""
    x, y, w, h = rect
    for gx in range(x, x + w, spacing):
        pygame.draw.line(surface, color, (gx, y), (gx, y + h), 1)
    for gy in range(y, y + h, spacing):
        pygame.draw.line(surface, color, (x, gy), (x + w, gy), 1)


def draw_circle_aa(surface: "pygame.Surface", color: Tuple[int, int, int],
                   pos: Tuple[int, int], radius: int) -> None:
    """Draws an anti-aliased filled circle using gfxdraw."""
    x, y = pos
    pygame.gfxdraw.aacircle(surface, x, y, radius, color)
    pygame.gfxdraw.filled_circle(surface, x, y, radius, color)


def draw_rect_aa(surface: "pygame.Surface", color: Tuple[int, int, int],
                 rect: Tuple[int, int, int, int]) -> None:
    """Draws an anti-aliased rectangle outline."""
    x, y, w, h = rect
    pygame.gfxdraw.rectangle(surface, pygame.Rect(x, y, w, h), color)


def draw_polygon_aa(surface: "pygame.Surface", color: Tuple[int, int, int],
                    points: List[Tuple[int, int]]) -> None:
    """Draws an anti-aliased filled polygon."""
    if len(points) < 3:
        return
    int_points = [(int(p[0]), int(p[1])) for p in points]
    pygame.gfxdraw.aapolygon(surface, int_points, color)
    pygame.gfxdraw.filled_polygon(surface, int_points, color)


def draw_crosshair(surface: "pygame.Surface", cx: int, cy: int, size: int = 8,
                   color: Tuple[int, int, int] = WHITE, gap: int = 2) -> None:
    """Draws a targeting crosshair at (cx, cy)."""
    # Top
    pygame.draw.line(surface, color, (cx, cy - gap), (cx, cy - gap - size), 1)
    # Bottom
    pygame.draw.line(surface, color, (cx, cy + gap), (cx, cy + gap + size), 1)
    # Left
    pygame.draw.line(surface, color, (cx - gap, cy), (cx - gap - size, cy), 1)
    # Right
    pygame.draw.line(surface, color, (cx + gap, cy), (cx + gap + size, cy), 1)


# ===========================================================================
# SECTION 7.4 — Data Visualization Helpers
# ===========================================================================

def map_value_to_pixel(value: float, min_val: float, max_val: float,
                       pixel_range: int, invert: bool = False) -> float:
    """Maps a scalar value to a pixel offset within a given pixel_range."""
    if abs(max_val - min_val) < 1e-6:
        return 0.0
    t = (value - min_val) / (max_val - min_val)
    t = max(0.0, min(1.0, t))
    if invert:
        t = 1.0 - t
    return t * pixel_range


def draw_line_graph(surface: "pygame.Surface", data: Sequence[float],
                    rect: Tuple[int, int, int, int],
                    min_val: float, max_val: float,
                    color: Tuple[int, int, int] = CYAN, thickness: int = 1) -> None:
    """Draws a standard line graph within a bounding rect."""
    if len(data) < 2:
        return
        
    x, y, w, h = rect
    pts = []
    n = len(data)
    
    for i, v in enumerate(data):
        px = x + (i / (n - 1)) * w
        py_offset = map_value_to_pixel(v, min_val, max_val, h, invert=True)
        py = y + py_offset
        pts.append((px, py))
        
    if len(pts) >= 2:
        pygame.draw.lines(surface, color, False, pts, thickness)


def draw_fill_graph(surface: "pygame.Surface", data: Sequence[float],
                    rect: Tuple[int, int, int, int],
                    min_val: float, max_val: float,
                    color: Tuple[int, int, int, int] = (180, 220, 230, 60)) -> None:
    """Draws a filled polygon graph with alpha channel."""
    if len(data) < 2:
        return
        
    x, y, w, h = rect
    pts = [(x, y + h)]
    n = len(data)
    
    for i, v in enumerate(data):
        px = x + (i / (n - 1)) * w
        py_offset = map_value_to_pixel(v, min_val, max_val, h, invert=True)
        py = y + py_offset
        pts.append((px, py))
        
    pts.append((x + w, y + h))
    
    # Use a separate surface to support alpha blending
    graph_surf = pygame.Surface((w + 2, h + 2), pygame.SRCALPHA)
    offset_pts = [(p[0] - x, p[1] - y) for p in pts]
    pygame.draw.polygon(graph_surf, color, offset_pts)
    surface.blit(graph_surf, (x, y))


def draw_bar_chart(surface: "pygame.Surface", data: Sequence[float],
                   rect: Tuple[int, int, int, int],
                   min_val: float, max_val: float,
                   color: Tuple[int, int, int] = CYAN,
                   bar_color_high: Tuple[int, int, int] = ALERT,
                   threshold: float = 80.0) -> None:
    """Draws a vertical bar chart (e.g., for per-core CPU usage)."""
    x, y, w, h = rect
    n = len(data)
    if n == 0:
        return
        
    bar_w = max(2, (w - (n - 1) * 2) // n)
    spacing = (w - bar_w * n) // max(1, n - 1) if n > 1 else 0
    
    for i, v in enumerate(data):
        bx = x + i * (bar_w + spacing)
        bh = map_value_to_pixel(v, min_val, max_val, h, invert=False)
        by = y + h - bh
        
        # background
        pygame.draw.rect(surface, DIM, (bx, y, bar_w, h), 1)
        # bar
        col = bar_color_high if v >= threshold else color
        if bh > 1:
            pygame.draw.rect(surface, col, (bx + 1, by + 1, bar_w - 2, bh - 1))


# ===========================================================================
# SECTION 7.5 — Specialized HUD Elements
# ===========================================================================

def draw_arc(surface: "pygame.Surface", center: Tuple[int, int], radius: int,
             start_angle: float, stop_angle: float, color: Tuple[int, int, int],
             thickness: int = 1, segments: int = 60) -> None:
    """
    Draws an arc using line segments for custom thickness and AA control.
    Angles are in radians. 0 is right, PI/2 is up (if Y is inverted), etc.
    """
    cx, cy = center
    pts = []
    
    # Ensure we go the short way
    if stop_angle < start_angle:
        stop_angle += math.tau
        
    for i in range(segments + 1):
        t = i / segments
        ang = start_angle + t * (stop_angle - start_angle)
        px = cx + math.cos(ang) * radius
        py = cy - math.sin(ang) * radius  # Negative sin because Pygame Y is down
        pts.append((px, py))
        
    if len(pts) >= 2:
        pygame.draw.lines(surface, color, False, pts, thickness)


def draw_arc_gauge(surface: "pygame.Surface", cx: int, cy: int, r: int,
                   frac: float, base_color: Tuple[int, int, int] = DIM,
                   active_color: Tuple[int, int, int] = CYAN,
                   start_angle: float = math.pi, stop_angle: float = 2.0 * math.pi) -> None:
    """
    Draws a curved gauge indicator (like a speedometer).
    frac: 0.0 to 1.0
    """
    frac = max(0.0, min(1.0, frac))
    
    # Draw background arc
    draw_arc(surface, (cx, cy), r, start_angle, stop_angle, base_color, 2)
    
    # Draw active arc
    active_stop = start_angle + frac * (stop_angle - start_angle)
    if frac > 0.01:
        col = active_color
        if frac <= 0.3:
            col = ALERT
        elif frac <= 0.6:
            col = AMBER
            
        draw_arc(surface, (cx, cy), r, start_angle, active_stop, col, 3)
        
    # Tick marks
    for i in range(11):
        t = i / 10.0
        ang = start_angle + t * (stop_angle - start_angle)
        r1 = r - 4
        r2 = r + 2
        p1 = (cx + math.cos(ang) * r1, cy - math.sin(ang) * r1)
        p2 = (cx + math.cos(ang) * r2, cy - math.sin(ang) * r2)
        pygame.draw.line(surface, STRUCT, p1, p2, 1)


def draw_radar_sweep(surface: "pygame.Surface", cx: int, cy: int, radius: int,
                     angle: float, color: Tuple[int, int, int] = CYAN,
                     sweep_width_rad: float = 0.5) -> None:
    """
    Draws a radar sweep with a fading trailing wedge.
    angle is the leading edge of the sweep in radians.
    """
    # Draw background circles
    for r_frac in [0.33, 0.66, 1.0]:
        pygame.gfxdraw.aacircle(surface, cx, cy, int(radius * r_frac), DIM)
        
    # Draw crosshairs
    pygame.draw.line(surface, DIM, (cx - radius, cy), (cx + radius, cy), 1)
    pygame.draw.line(surface, DIM, (cx, cy - radius), (cx, cy + radius), 1)
    
    # Draw sweep wedge
    # We approximate the wedge by drawing multiple lines from center with fading alpha
    steps = 10
    for i in range(steps):
        t = i / steps
        ang = angle - t * sweep_width_rad
        alpha = int(150 * (1.0 - t))
        if alpha <= 0:
            continue
            
        ex = cx + math.cos(ang) * radius
        ey = cy + math.sin(ang) * radius
        
        # To draw an alpha line, we need a surface with SRCALPHA
        line_surf = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        pygame.draw.line(line_surf, (color[0], color[1], color[2], alpha), (cx, cy), (ex, ey), 2)
        surface.blit(line_surf, (0, 0))


def draw_ekg(surface: "pygame.Surface", x: int, y: int, w: int, h: int,
             phase: float, color: Tuple[int, int, int] = CYAN,
             cycle_len: float = 60.0) -> None:
    """Draws an EKG-style vital sign waveform."""
    pygame.draw.rect(surface, DIM, (x, y, w, h), 1)
    mid_y = y + h // 2
    n = w
    pts = []
    
    for i in range(n):
        t_local = ((i / n) * cycle_len + phase * 12.0) % cycle_len
        dy = _ekg_shape(t_local, cycle_len)
        py = mid_y - dy * (h * 0.4)
        pts.append((x + i, py))
        
    if len(pts) > 1:
        pygame.draw.lines(surface, color, False, pts, 1)


def _ekg_shape(t: float, cycle: float) -> float:
    """Mathematical model of PQRST waveform for EKG drawing."""
    phase = t / cycle
    if phase < 0.1:
        return 0.15 * math.sin(phase / 0.1 * math.pi)
    elif phase < 0.15:
        return 0.0
    elif phase < 0.18:
        return -0.2 * ((phase - 0.15) / 0.03)
    elif phase < 0.22:
        return -0.2 + 2.2 * ((phase - 0.18) / 0.04)
    elif phase < 0.26:
        return 2.0 - 3.0 * ((phase - 0.22) / 0.04)
    elif phase < 0.30:
        return -1.0 + 0.5 * ((phase - 0.26) / 0.04)
    elif phase < 0.40:
        return -0.5 * math.sin((phase - 0.30) / 0.10 * math.pi)
    else:
        return 0.0