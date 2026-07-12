#!/usr/bin/env python3
"""
PROJECT HERMES - Omnimind Absolute Edition
File: ui_panels.py
Monolithic Compilation Standard
"The earth and sky will break before I fail you."

Description:
This module contains the exhaustive, precision-tuned rendering logic for every
visual sector of the HERMES Omnimind HUD. 

Every panel is engineered for absolute visual perfection, featuring dense data
visualization, anti-aliased geometry, dynamic camera projections, and smooth
typographic layouts. It treats the screen as a high-end tactical interface,
where every pixel is accounted for and no element is left to default styling.
"""

import math
import time
from typing import List, Tuple, Optional, Dict, Any, Sequence

from config import Config
from palette import (BLACK, WHITE, CYAN, AMBER, ALERT, INK, GRID, DIM, STRUCT, MUTED,
                     with_alpha, mix, depth_shade)
from math_engine import Vector3, Matrix4x4, PerlinNoise3D, catmull_rom
from ui_widgets import (Panel, wrap_text, draw_text, draw_text_wrapped, draw_dashed_h,
                        draw_dashed_v, draw_grid, draw_circle_aa, draw_arc_gauge, draw_ekg,
                        draw_line_graph, draw_fill_graph, draw_bar_chart)

try:
    import pygame
    import pygame.gfxdraw
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False
    pygame = None


# ===========================================================================
# PANEL A: System Header Bar
# ===========================================================================
class HeaderBarRenderer:
    """Top-most status bar spanning the screen width (0-1920, 0-44)."""
    
    def __init__(self) -> None:
        self.title_font = None
        self.small_font = None
        self.tiny_font = None
        self._init_fonts()

    def _init_fonts(self) -> None:
        if not HAS_PYGAME: return
        cands = ["consolas", "menlo", "dejavusansmono", "couriernew", "monospace"]
        self.title_font = pygame.font.SysFont(cands, 18, bold=True)
        self.small_font = pygame.font.SysFont(cands, 11)
        self.tiny_font = pygame.font.SysFont(cands, 9)

    def render(self, surface: "pygame.Surface", snap: Dict[str, Any]) -> None:
        if not HAS_PYGAME: return
        
        # Base background with subtle gradient line
        surface.fill(BLACK, (0, 0, Config.WIDTH, 44))
        pygame.draw.line(surface, STRUCT, (0, 43), (Config.WIDTH, 43), 1)
        pygame.draw.line(surface, GRID, (0, 44), (Config.WIDTH, 44), 1)

        # Center Title
        title = "HERMES - O M N I M I N D   A B S O L U T E   E D I T I O N"
        img = self.title_font.render(title, True, WHITE)
        rect = img.get_rect(center=(Config.WIDTH // 2, 22))
        surface.blit(img, rect)
        
        # Subtitle below main title
        sub_title = "[ S I N G U L A R I T Y   M A T R I X ]"
        sub_img = self.tiny_font.render(sub_title, True, AMBER)
        sub_rect = sub_img.get_rect(center=(Config.WIDTH // 2, 36))
        surface.blit(sub_img, sub_rect)

        # Left Status Block
        left_lines = [
            f"ARC REACTOR :: OPTIMAL",
            f"SUIT INTEGRITY :: {snap.get('core_health', 100.0):5.1f}%",
            f"DIAGNOSTICS :: THREADS={snap.get('active_threads', 0):03d}",
            f"STABILITY :: {snap.get('stability_score', 100.0):5.1f}%"
        ]
        y = 4
        for line in left_lines:
            img2 = self.small_font.render(line, True, MUTED)
            surface.blit(img2, (8, y))
            y += 10

        # Right Status Block
        bt = snap.get("boot_time", time.time())
        up = time.time() - bt
        h = int(up // 3600); m = int((up % 3600) // 60); s = int(up % 60)
        
        right_lines = [
            f"UPTIME :: {h:02d}:{m:02d}:{s:02d}",
            f"CORE THERMAL :: {snap.get('cpu_temp', 0.0):5.1f}C",
            f"ACTIVE PROCS :: {snap.get('active_threads', 0):03d}",
            f"AUX POWER :: ONLINE"
        ]
        y = 4
        for line in right_lines:
            img3 = self.small_font.render(line, True, INK)
            r = img3.get_rect(topright=(Config.WIDTH - 8, y))
            surface.blit(img3, r)
            y += 10


# ===========================================================================
# PANEL B: 3D Topological Terrain Mesh
# ===========================================================================
class TerrainRenderer:
    """Left viewport 3D wireframe terrain reacting to audio and noise (0-1248, 44-631)."""

    def __init__(self) -> None:
        self.noise = PerlinNoise3D(seed=42)
        self.font = None
        self.tiny = None
        self._time = 0.0
        if HAS_PYGAME:
            cands = ["consolas", "menlo", "dejavusansmono", "couriernew", "monospace"]
            self.font = pygame.font.SysFont(cands, 12)
            self.tiny = pygame.font.SysFont(cands, 10)
            
        gs = Config.GRID_SIZE
        self.grid_pts: List[Tuple[float, float]] = []
        for j in range(gs):
            for i in range(gs):
                u = (i / (gs - 1)) * 2.0 - 1.0
                v = (j / (gs - 1)) * 2.0 - 1.0
                self.grid_pts.append((u, v))

    def _project(self, u: float, v: float, h: float, fft_disp: float,
                 cx: float, cy: float) -> Tuple[float, float, float, float]:
        wx = u * 8.0
        wz = v * 8.0
        wy = h + fft_disp
        
        pitch = Config.CAMERA_PITCH
        cosP = math.cos(pitch)
        sinP = math.sin(pitch)
        
        ry = wy * cosP - wz * sinP
        rz = wy * sinP + wz * cosP
        rx = wx
        
        rz_cam = rz + Config.CAMERA_DEPTH
        if rz_cam < 0.5: rz_cam = 0.5
        
        f = Config.FOCAL_LENGTH
        sx = cx + (rx / rz_cam) * f
        sy = cy - (ry / rz_cam) * f
        depth_t = 1.0 - max(0.0, min(1.0, (rz_cam - 6.0) / 18.0))
        return (sx, sy, rz_cam, depth_t)

    def render(self, surface: "pygame.Surface", snap: Dict[str, Any], dt: float) -> None:
        if not HAS_PYGAME: return
        self._time += dt
        
        x0, y0, x1, y1 = Config.LEFT_VIEWPORT
        w = x1 - x0
        h = y1 - y0

        # Offscreen buffer for mesh
        buf = pygame.Surface((w, h))
        buf.fill(BLACK)

        cx = w * 0.5
        cy = h * 0.62
        fft = snap.get("audio_fft", [0.0] * 64)
        gs = Config.GRID_SIZE

        # Calculate all points
        pts = []
        for idx, (u, v) in enumerate(self.grid_pts):
            elev = self.noise.fbm(
                u * 1.2 + self._time * 0.05, v * 1.2, self._time * 0.02,
                octaves=Config.PERLIN_OCTAVES, persistence=Config.PERLIN_PERSISTENCE,
                lacunarity=Config.PERLIN_LACUNARITY
            )
            h_val = elev * 2.5
            d_center = math.sqrt(u * u + v * v)
            fft_band = fft[idx % len(fft)] if fft else 0.0
            fft_disp = fft_band * (1.0 - min(1.0, d_center)) * 2.0
            sx, sy, rz, depth_t = self._project(u, v, h_val, fft_disp, cx, cy)
            pts.append((sx, sy, rz, depth_t, h_val, fft_disp, u, v))

        # Draw mesh lines back-to-front for proper occlusion
        # We sort by depth to draw further points first
        indexed_pts = list(enumerate(pts))
        indexed_pts.sort(key=lambda p: -p[1][2])

        drawn_lines = set()
        
        for idx, (sx, sy, rz, depth_t, h_val, fft_disp, u, v) in indexed_pts:
            row = idx // gs
            col = idx % gs
            
            # Connect to right neighbor
            if col < gs - 1:
                n_idx = idx + 1
                if n_idx in [p[0] for p in indexed_pts]: # Should always be true, just safety
                    nsx, nsy, nrz, ndepth_t, _, _, _, _ = pts[n_idx]
                    avg_depth = (depth_t + ndepth_t) / 2.0
                    col_val = mix(INK, BLACK, (1.0 - avg_depth) * 0.5)
                    if h_val > 0.6 or fft_disp > 0.4:
                        col_val = mix(CYAN, BLACK, (1.0 - avg_depth) * 0.3)
                    pygame.draw.line(buf, col_val, (sx, sy), (nsx, nsy), 1)
                    
            # Connect to bottom neighbor
            if row < gs - 1:
                n_idx = idx + gs
                nsx, nsy, nrz, ndepth_t, _, _, _, _ = pts[n_idx]
                avg_depth = (depth_t + ndepth_t) / 2.0
                col_val = mix(INK, BLACK, (1.0 - avg_depth) * 0.5)
                if h_val > 0.6 or fft_disp > 0.4:
                    col_val = mix(CYAN, BLACK, (1.0 - avg_depth) * 0.3)
                pygame.draw.line(buf, col_val, (sx, sy), (nsx, nsy), 1)

        # Blit to main surface
        surface.blit(buf, (x0, y0))

        # Bracketing and HUD overlays directly on main surface
        bracket_len = 16
        pygame.draw.line(surface, STRUCT, (x0, y0), (x0 + bracket_len, y0), 1)
        pygame.draw.line(surface, STRUCT, (x0, y0), (x0, y0 + bracket_len), 1)
        pygame.draw.line(surface, STRUCT, (x1 - bracket_len, y0), (x1, y0), 1)
        pygame.draw.line(surface, STRUCT, (x1, y0), (x1, y0 + bracket_len), 1)
        pygame.draw.line(surface, STRUCT, (x0, y1 - bracket_len), (x0, y1), 1)
        pygame.draw.line(surface, STRUCT, (x0, y1), (x0 + bracket_len, y1), 1)
        pygame.draw.line(surface, STRUCT, (x1 - bracket_len, y1), (x1, y1), 1)
        pygame.draw.line(surface, STRUCT, (x1, y1 - bracket_len), (x1, y1), 1)

        # Left Telemetry Column
        left_x = x0 + 14
        left_y = y0 + 14
        left_lines = [
            "DATASTREAM MATRIX SRC: 712. / 1210",
            "2090..930.9..032.111-C",
            "1022130",
            "89370"
        ]
        for line in left_lines:
            img = self.font.render(line, True, MUTED)
            surface.blit(img, (left_x, left_y))
            left_y += 14

        # Right Telemetry Column
        right_x = x1 - 14
        right_y = y0 + 14
        right_lines = [
            "-8/7C6", "259112A", "2001520", "10022007", "10200000"
        ]
        for line in right_lines:
            img = self.font.render(line, True, MUTED)
            r = img.get_rect(topright=(right_x, right_y))
            surface.blit(img, r)
            right_y += 14

        # Mini preview graph
        self._draw_preview_graph(surface, x0 + 14, y1 - 84)
        
        # LLM stream overlay box along bottom
        self._draw_llm_overlay(surface, snap, x0, y1 - 92, w, 80)

    def _draw_preview_graph(self, surface: "pygame.Surface", x: int, y: int) -> None:
        w, h = 70, 60
        pygame.draw.rect(surface, DIM, (x, y, w, h), 1)
        img = self.tiny.render(".268", True, MUTED)
        surface.blit(img, (x + 3, y + 3))
        
        pts = []
        for i in range(w - 6):
            t = i / (w - 6)
            val = 0.5 + 0.35 * math.sin(t * 8.0 + self._time * 2.0) * math.exp(-t * 0.8)
            py = y + h - 6 - val * (h - 16)
            pts.append((x + 3 + i, py))
        if len(pts) > 1:
            pygame.draw.lines(surface, INK, False, pts, 1)

    def _draw_llm_overlay(self, surface: "pygame.Surface", snap: Dict[str, Any],
                          x: int, y: int, w: int, h: int) -> None:
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        pygame.draw.rect(overlay, (120, 120, 120, 255), (0, 0, w, h), 1)
        surface.blit(overlay, (x, y))
        
        # Header tag
        hdr = self.tiny.render("COGNITIVE UPLINK :: OPENROUTER STREAM", True, AMBER)
        surface.blit(hdr, (x + 8, y + 4))
        
        stream_text = snap.get("llm_stream", "") or "[ Awaiting cognitive uplink... ]"
        col = WHITE if stream_text else INK
        draw_text_wrapped(surface, self.font, stream_text, (x + 8, y + 20), w - 16, col, 1)


# ===========================================================================
# PANEL C-TOP: Rotating Wireframe Geo-Vector Globe
# ===========================================================================
class GlobeRenderer:
    """Right-top viewport rotating geospatial vector globe (1248-1920, 44-240)."""

    def __init__(self) -> None:
        self.font = None
        self.tiny = None
        self._time = 0.0
        if HAS_PYGAME:
            cands = ["consolas", "menlo", "dejavusansmono", "couriernew", "monospace"]
            self.font = pygame.font.SysFont(cands, 11)
            self.tiny = pygame.font.SysFont(cands, 9)
            
        n = Config.GLOBE_POINTS
        phi = (1.0 + math.sqrt(5.0)) / 2.0
        self.sphere_pts: List[Vector3] = []
        for i in range(n):
            y = 1.0 - (i / float(n - 1)) * 2.0
            r = math.sqrt(1.0 - y * y)
            theta = 2.0 * math.pi * i / phi
            x = math.cos(theta) * r
            z = math.sin(theta) * r
            self.sphere_pts.append(Vector3(x, y, z))
            
        # Precompute latitude/longitude graticule lines
        self.graticule: List[List[Vector3]] = []
        # Latitudes
        for lat in range(-60, 90, 30):
            line = []
            la = math.radians(lat)
            for lon in range(0, 361, 5):
                lo = math.radians(lon)
                line.append(Vector3(math.cos(la)*math.cos(lo), math.sin(la), math.cos(la)*math.sin(lo)))
            self.graticule.append(line)
        # Longitudes
        for lon in range(0, 180, 30):
            line = []
            lo = math.radians(lon)
            for lat in range(-90, 91, 5):
                la = math.radians(lat)
                line.append(Vector3(math.cos(la)*math.cos(lo), math.sin(la), math.cos(la)*math.sin(lo)))
            self.graticule.append(line)

    def render(self, surface: "pygame.Surface", snap: Dict[str, Any], dt: float) -> None:
        if not HAS_PYGAME: return
        self._time += dt
        
        x0, y0, x1, y1 = Config.RIGHT_TOP_VIEWPORT
        sphere_y0 = 44
        sphere_y1 = 240
        cx = (x0 + x1) // 2
        cy = (sphere_y0 + sphere_y1) // 2
        R = Config.GLOBE_RADIUS

        yaw = self._time * Config.GLOBE_YAW_RATE
        pitch = Config.GLOBE_PITCH_TILT
        Ry = Matrix4x4.rotation_y(yaw)
        Rx = Matrix4x4.rotation_x(pitch)
        view_vec = Vector3(0.0, 0.0, 1.0)

        # 1. Draw atmospheric glow
        glow_surf = pygame.Surface((R*3, R*3), pygame.SRCALPHA)
        for r in range(int(R*1.15), R, -1):
            alpha = int(80 * (1.0 - (r - R) / (R * 0.15)))
            pygame.gfxdraw.aacircle(glow_surf, R+20, R+20, r, (120, 180, 220, alpha))
        surface.blit(glow_surf, (cx - R - 20, cy - R - 20))

        # 2. Draw Graticule (Lat/Lon lines)
        for line in self.graticule:
            pts_2d = []
            for pt in line:
                rotated = Rx.transform_point(Ry.transform_point(pt))
                dot = rotated.dot(view_vec)
                if dot < 0.0:
                    if pts_2d:
                        if len(pts_2d) > 1:
                            pygame.draw.aalines(surface, DIM, False, pts_2d)
                        pts_2d.clear()
                    continue
                sx = cx + rotated.x * R
                sy = cy - rotated.y * R
                pts_2d.append((sx, sy))
            if len(pts_2d) > 1:
                pygame.draw.aalines(surface, DIM, False, pts_2d)

        # 3. Draw sphere wireframe points
        front_pts = []
        for pt in self.sphere_pts:
            rotated = Rx.transform_point(Ry.transform_point(pt))
            dot = rotated.dot(view_vec)
            if dot < 0.0:
                continue
            sx = cx + rotated.x * R
            sy = cy - rotated.y * R
            depth_t = 1.0 - (rotated.z + 1.0) * 0.5
            front_pts.append((sx, sy, depth_t, rotated))

        if len(front_pts) > 1:
            for i in range(len(front_pts) - 1):
                p1 = front_pts[i]
                p2 = front_pts[i + 1]
                dx = p1[0] - p2[0]
                dy = p1[1] - p2[1]
                if dx * dx + dy * dy < 900:
                    col = depth_shade(STRUCT, (1.0 - p1[3].z) * 0.5)
                    pygame.draw.aaline(surface, col, (p1[0], p1[1]), (p2[0], p2[1]))

        for sx, sy, depth_t, rotated in front_pts:
            col = depth_shade(INK, 1.0 - depth_t)
            ix, iy = int(sx), int(sy)
            pygame.gfxdraw.pixel(surface, ix, iy, col)
            if depth_t > 0.7: # Front facing highlights
                pygame.gfxdraw.pixel(surface, ix+1, iy, col)
                pygame.gfxdraw.pixel(surface, ix, iy+1, col)

        # 4. Draw scraped coordinate pins & routes
        coords = snap.get("globe_coords", [])
        visible_pins = []
        for lat, lon in coords[:12]:
            la = math.radians(lat)
            lo = math.radians(lon) + yaw
            px = math.cos(la) * math.cos(lo)
            py = math.sin(la)
            pz = math.cos(la) * math.sin(lo)
            v = Vector3(px, py, pz)
            rotated = Rx.transform_point(v)
            dot = rotated.dot(view_vec)
            if dot < 0.0:
                continue
            sx = cx + rotated.x * R
            sy = cy - rotated.y * R
            visible_pins.append((sx, sy, rotated.z))
            
            # Pin glow
            glow_surf = pygame.Surface((12, 12), pygame.SRCALPHA)
            pygame.gfxdraw.filled_circle(glow_surf, 6, 6, 5, (255, 255, 255, 40))
            pygame.gfxdraw.aacircle(glow_surf, 6, 6, 4, WHITE)
            surface.blit(glow_surf, (int(sx)-6, int(sy)-6))
            draw_circle_aa(surface, WHITE, (int(sx), int(sy)), 2)

        # Draw great circle routes between visible pins
        if len(visible_pins) > 1:
            for i in range(len(visible_pins)-1):
                p1 = visible_pins[i]
                p2 = visible_pins[i+1]
                # Simple curved arc projection
                mx = (p1[0] + p2[0]) / 2
                my = (p1[1] + p2[1]) / 2
                dx = mx - cx
                dy = my - cy
                dist = math.hypot(dx, dy)
                if dist > 0:
                    # pull toward center to simulate sphere curve
                    tx = mx - dx * 0.15
                    ty = my - dy * 0.15
                else:
                    tx, ty = mx, my
                pygame.draw.aaline(surface, p1, p2[0], p2[1])
                pygame.draw.aalines(surface, AMBER, False, [(p1[0], p1[1]), (tx, ty), (p2[0], p2[1])])

        # Header
        hdr = self.tiny.render("GEOVECTOR LATTICE :: live sync", True, MUTED)
        surface.blit(hdr, (x0 + 8, sphere_y0 + 4))
        coords_txt = self.tiny.render(f"TRACKED NODES: {len(visible_pins)}", True, INK)
        surface.blit(coords_txt, (x0 + 8, sphere_y0 + 16))


# ===========================================================================
# PANEL C-BOTTOM: Scrolling Live World Feed
# ===========================================================================
class NewsFeedRenderer:
    """Right-top bottom feed scrolling scraped bulletins (1248-1920, 240-405)."""

    def __init__(self) -> None:
        self.font = None
        self.tiny = None
        self._scroll = 0.0
        if HAS_PYGAME:
            cands = ["consolas", "menlo", "dejavusansmono", "couriernew", "monospace"]
            self.font = pygame.font.SysFont(cands, 11)
            self.tiny = pygame.font.SysFont(cands, 9)

    def render(self, surface: "pygame.Surface", snap: Dict[str, Any], dt: float) -> None:
        if not HAS_PYGAME: return
        self._scroll += dt * 24.0
        
        x0, y0, x1, y1 = Config.RIGHT_TOP_VIEWPORT
        feed_y0 = 240
        feed_y1 = 405
        w = x1 - x0
        h = feed_y1 - feed_y0

        buf = pygame.Surface((w, h))
        buf.fill(BLACK)

        items = snap.get("news_items", [])
        if not items:
            items = [{"title": "[ No feed data ]", "pub": ""}]

        lines = []
        for it in items:
            title = it.get("title", "")
            pub = it.get("pub", "")
            if pub:
                lines.append(f"> {title}  [{pub}]")
            else:
                lines.append(f"> {title}")

        all_lines = lines * 3
        line_h = 16
        offset = int(self._scroll) % max(1, len(lines) * line_h)

        y = -offset
        for line in all_lines:
            if y > h: break
            if y + line_h > 0:
                img = self.font.render(line, True, INK)
                buf.blit(img, (8, y))
            y += line_h

        # Fade mask top and bottom
        fade_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(12):
            alpha = int(255 * (1.0 - i / 12))
            pygame.draw.line(fade_surf, (0, 0, 0, alpha), (0, i), (w, i))
            pygame.draw.line(fade_surf, (0, 0, 0, alpha), (0, h - 1 - i), (w, h - 1 - i))
        buf.blit(fade_surf, (0, 0))

        surface.blit(buf, (x0, feed_y0))
        pygame.draw.line(surface, GRID, (x0, feed_y0), (x1, feed_y0), 1)
        
        hdr = self.tiny.render("LIVE WORLD FEED :: scraper-daemon active", True, MUTED)
        surface.blit(hdr, (x0 + 8, feed_y0 + 2))


# ===========================================================================
# PANEL D: Personal Monitor, Social, Critical Notifications
# ===========================================================================
class PersonalMonitorRenderer:
    """Right-bottom viewport media, social, and alerts (1248-1920, 405-810)."""

    def __init__(self) -> None:
        self.font = None
        self.tiny = None
        self._time = 0.0
        self._bell_phase = 0.0
        if HAS_PYGAME:
            cands = ["consolas", "menlo", "dejavusansmono", "couriernew", "monospace"]
            self.font = pygame.font.SysFont(cands, 11)
            self.tiny = pygame.font.SysFont(cands, 9)

    def render(self, surface: "pygame.Surface", snap: Dict[str, Any], dt: float) -> None:
        if not HAS_PYGAME: return
        self._time += dt
        self._bell_phase += dt * 4.0
        
        x0, y0, x1, y1 = Config.RIGHT_BOTTOM_VIEWPORT
        w = x1 - x0
        h = y1 - y0

        pygame.draw.rect(surface, STRUCT, (x0, y0, w, h), 1)

        # Section A: Media Feed
        media_y = y0 + 8
        media_h = 76
        self._draw_media(surface, x0 + 8, media_y, w - 16, media_h)

        # Section B: Social Feed
        social_y = media_y + media_h + 8
        social_h = 80
        self._draw_social(surface, x0 + 8, social_y, w - 16, social_h, snap)

        # Section C: Critical Notifications
        notif_y = social_y + social_h + 8
        notif_h = h - (notif_y - y0) - 8
        self._draw_notifications(surface, x0 + 8, notif_y, w - 16, notif_h, snap)

    def _draw_media(self, surface: "pygame.Surface", x: int, y: int, w: int, h: int) -> None:
        hdr = self.tiny.render("MEDIA FEED :: 4-channel wireframe projection", True, MUTED)
        surface.blit(hdr, (x, y))
        box_y = y + 14
        box_h = h - 14
        box_w = (w - 18) // 4
        labels = ["SUIT-XLII", "DRONE-7", "MATRIX-A", "SAT-RELAY"]
        
        for i in range(4):
            bx = x + i * (box_w + 6)
            pygame.draw.rect(surface, STRUCT, (bx, box_y, box_w, box_h), 1)
            
            # Wireframe projection lines
            for ly in range(4, box_h - 4, 6):
                y_pos = box_y + ly
                phase = math.sin(self._time * 2.0 + i * 0.7 + ly * 0.2)
                col = depth_shade(INK, 0.4 + 0.3 * abs(phase))
                pygame.draw.line(surface, col, (bx + 3, y_pos), (bx + box_w - 3, y_pos), 1)
                
            # Diagonal sweep
            sweep_x = bx + 3 + int((box_w - 6) * (0.5 + 0.5 * math.sin(self._time * 1.5 + i)))
            pygame.draw.line(surface, WHITE, (sweep_x, box_y + 3), (sweep_x, box_y + box_h - 3), 1)
            
            # Label
            lbl = self.tiny.render(labels[i], True, INK)
            surface.blit(lbl, (bx + 3, box_y + box_h - 12))

    def _draw_social(self, surface: "pygame.Surface", x: int, y: int,
                     w: int, h: int, snap: Dict[str, Any]) -> None:
        hdr = self.tiny.render("SOCIAL NETWORK :: priority check-ins", True, MUTED)
        surface.blit(hdr, (x, y))
        feeds = snap.get("social_feeds", [])
        if not feeds:
            feeds = [{"user": "@SYS", "msg": "No social data"}]
        entry_y = y + 16
        entry_h = (h - 16) // max(1, len(feeds))
        
        for i, feed in enumerate(feeds[:4]):
            user = feed.get("user", "@???")
            msg = feed.get("msg", "")
            ey = entry_y + i * entry_h
            
            avatar_sz = entry_h - 6
            pygame.draw.rect(surface, STRUCT, (x, ey, avatar_sz, avatar_sz), 1)
            for ay in range(3, avatar_sz - 3, 4):
                pygame.draw.line(surface, DIM, (x + 2, ey + ay), (x + avatar_sz - 2, ey + ay), 1)
                
            u_img = self.font.render(user, True, WHITE)
            surface.blit(u_img, (x + avatar_sz + 6, ey))
            draw_text_wrapped(surface, self.tiny, msg, (x + avatar_sz + 6, ey + 14), w - avatar_sz - 12, INK, 1)

    def _draw_notifications(self, surface: "pygame.Surface", x: int, y: int,
                            w: int, h: int, snap: Dict[str, Any]) -> None:
        hdr = self.tiny.render("CRITICAL NOTIFICATIONS :: priority queue", True, MUTED)
        surface.blit(hdr, (x, y))
        alerts = snap.get("security_alerts", [])
        if not alerts:
            alerts = ["No active alerts"]
            
        override = snap.get("daemon_override", False)
        daemon_msg = snap.get("daemon_msg", "")
        if override and daemon_msg:
            alerts = [daemon_msg] + alerts[:3]

        entry_y = y + 16
        entry_h = (h - 16) // max(1, len(alerts))
        flash = (math.sin(self._bell_phase) > 0)
        
        for i, alert in enumerate(alerts[:4]):
            ey = entry_y + i * entry_h
            col = ALERT if flash else AMBER
            
            bell_x = x + 6
            bell_y = ey + entry_h // 2
            self._draw_bell(surface, bell_x, bell_y, col)
            draw_text_wrapped(surface, self.tiny, alert, (x + 18, ey + 2), w - 24, col, 1)
            pygame.draw.line(surface, col, (x, ey), (x + 3, ey), 1)

    def _draw_bell(self, surface: "pygame.Surface", cx: int, cy: int,
                   color: Tuple[int, int, int]) -> None:
        pygame.draw.line(surface, color, (cx, cy - 5), (cx, cy + 4), 1)
        pygame.draw.line(surface, color, (cx - 3, cy - 3), (cx - 3, cy + 3), 1)
        pygame.draw.line(surface, color, (cx + 3, cy - 3), (cx + 3, cy + 3), 1)
        pygame.draw.line(surface, color, (cx - 3, cy + 4), (cx + 3, cy + 4), 1)
        pygame.draw.line(surface, color, (cx, cy + 5), (cx, cy + 7), 1)


# ===========================================================================
# PANEL E: Bottom Diagnostic Sub-Panels (4 columns)
# ===========================================================================
class StatusMatrixRenderer:
    """Bottom row 4-panel diagnostic matrix (0-1920, 631-810)."""

    def __init__(self) -> None:
        self.font = None
        self.tiny = None
        self._time = 0.0
        self._ekg_phase = 0.0
        if HAS_PYGAME:
            cands = ["consolas", "menlo", "dejavusansmono", "couriernew", "monospace"]
            self.font = pygame.font.SysFont(cands, 11)
            self.tiny = pygame.font.SysFont(cands, 9)

    def render(self, surface: "pygame.Surface", snap: Dict[str, Any], dt: float) -> None:
        if not HAS_PYGAME: return
        self._time += dt
        self._ekg_phase += dt
        
        x0, y0, x1, y1 = Config.BOTTOM_ROW
        pygame.draw.line(surface, GRID, (0, y0), (Config.WIDTH, y0), 1)

        pw = Config.BOTTOM_PANEL_W
        ph = y1 - y0
        self._draw_temp(surface, x0 + 0 * pw, y0, pw, ph, snap)
        self._draw_latency(surface, x0 + 1 * pw, y0, pw, ph, snap)
        self._draw_resources(surface, x0 + 2 * pw, y0, pw, ph, snap)
        self._draw_health(surface, x0 + 3 * pw, y0, pw, ph, snap)

        for i in range(1, 4):
            dx = x0 + i * pw
            pygame.draw.line(surface, GRID, (dx, y0), (dx, y1), 1)

    def _draw_temp(self, surface: "pygame.Surface", x: int, y: int,
                   w: int, h: int, snap: Dict[str, Any]) -> None:
        title = self.font.render("CPU CORE THERMAL :: C", True, MUTED)
        surface.blit(title, (x + 8, y + 4))
        temp = snap.get("cpu_temp", 0.0)
        col = WHITE if temp > Config.TEMP_CRITICAL else CYAN
        val_str = self.font.render(f"{temp:.1f}C", True, col)
        surface.blit(val_str, (x + w - 8 - val_str.get_width(), y + 4))

        graph_x = x + 8
        graph_y = y + 24
        graph_w = w - 16
        graph_h = h - 32

        for threshold, label in [(50, "50"), (70, "70"), (85, "85")]:
            gy = graph_y + graph_h - int((threshold / 100.0) * graph_h)
            draw_dashed_h(surface, gy, graph_x, graph_x + graph_w, 5, 4, DIM)
            lbl = self.tiny.render(label, True, DIM)
            surface.blit(lbl, (graph_x + graph_w - 22, gy - 9))

        hist = snap.get("temp_hist", [])
        if len(hist) >= 2:
            pts = []
            n = len(hist)
            for i, v in enumerate(hist):
                px = graph_x + int((i / max(1, n - 1)) * graph_w)
                py = graph_y + graph_h - int(max(0.0, min(1.0, v / 100.0)) * graph_h)
                pts.append((px, py))
            if len(pts) >= 4:
                interp = []
                for i in range(len(pts) - 3):
                    p0, p1, p2, p3 = pts[i], pts[i+1], pts[i+2], pts[i+3]
                    steps = 8
                    for s in range(steps):
                        t = s / steps
                        ix, iy = catmull_rom(p0, p1, p2, p3, t)
                        interp.append((int(ix), int(iy)))
                interp.append(pts[-2])
                if len(interp) > 1:
                    pygame.draw.lines(surface, col, False, interp, 1)
            elif len(pts) > 1:
                pygame.draw.lines(surface, col, False, pts, 1)

        pygame.draw.rect(surface, DIM, (graph_x, graph_y, graph_w, graph_h), 1)

    def _draw_latency(self, surface: "pygame.Surface", x: int, y: int,
                      w: int, h: int, snap: Dict[str, Any]) -> None:
        title = self.font.render("NETWORK LATENCY :: ms", True, MUTED)
        surface.blit(title, (x + 8, y + 4))
        ping = snap.get("ping_ms", 0.0)
        up = snap.get("internet_up", False)
        col = WHITE if up else ALERT
        val_str = self.font.render(f"{ping:.0f}ms", True, col)
        surface.blit(val_str, (x + w - 8 - val_str.get_width(), y + 4))

        graph_x = x + 8
        graph_y = y + 24
        graph_w = w - 16
        graph_h = h - 32

        for threshold, label in [(50, "50"), (150, "150"), (300, "300")]:
            gy = graph_y + graph_h - int((threshold / 400.0) * graph_h)
            draw_dashed_h(surface, gy, graph_x, graph_x + graph_w, 5, 4, DIM)
            lbl = self.tiny.render(label, True, DIM)
            surface.blit(lbl, (graph_x + graph_w - 28, gy - 9))

        hist = snap.get("ping_hist", [])
        max_scale = 400.0
        for i, v in enumerate(hist):
            px = graph_x + int((i / max(1, len(hist) - 1)) * graph_w)
            if v >= 9999.0:
                py_offline = graph_y + graph_h - 4
                if i % 3 == 0:
                    pygame.draw.line(surface, ALERT, (px, py_offline - 6), (px, py_offline), 1)
                continue
            py = graph_y + graph_h - int(max(0.0, min(1.0, v / max_scale)) * graph_h)
            p_col = WHITE if v < 150 else (AMBER if v < 300 else ALERT)
            pygame.draw.circle(surface, p_col, (px, py), 2)

        if not up:
            warn = self.font.render("OFFLINE", True, ALERT)
            surface.blit(warn, (graph_x + graph_w // 2 - 24, graph_y + 4))

        pygame.draw.rect(surface, DIM, (graph_x, graph_y, graph_w, graph_h), 1)

    def _draw_resources(self, surface: "pygame.Surface", x: int, y: int,
                        w: int, h: int, snap: Dict[str, Any]) -> None:
        title = self.font.render("CPU / RAM LOAD :: %", True, MUTED)
        surface.blit(title, (x + 8, y + 4))
        cpu = snap.get("cpu_usage", 0.0)
        ram = snap.get("ram_usage", 0.0)
        val_str = self.font.render(f"CPU {cpu:.0f}%  RAM {ram:.0f}%", True, WHITE)
        surface.blit(val_str, (x + w - 8 - val_str.get_width(), y + 4))

        graph_x = x + 8
        graph_y = y + 24
        graph_w = w - 16
        graph_h = h - 56

        cpu_hist = snap.get("cpu_hist", [])
        ram_hist = snap.get("ram_hist", [])

        if len(cpu_hist) >= 2:
            poly_pts = [(graph_x, graph_y + graph_h)]
            n = len(cpu_hist)
            for i, v in enumerate(cpu_hist):
                px = graph_x + int((i / max(1, n - 1)) * graph_w)
                py = graph_y + graph_h - int(max(0.0, min(1.0, v / 100.0)) * graph_h)
                poly_pts.append((px, py))
            poly_pts.append((graph_x + graph_w, graph_y + graph_h))
            
            fill_surf = pygame.Surface((graph_w + 2, graph_h + 2), pygame.SRCALPHA)
            offset_pts = [(p[0] - graph_x, p[1] - graph_y) for p in poly_pts]
            pygame.draw.polygon(fill_surf, (180, 220, 230, 60), offset_pts)
            surface.blit(fill_surf, (graph_x, graph_y))
            
            outline_pts = poly_pts[1:-1]
            if len(outline_pts) > 1:
                pygame.draw.lines(surface, CYAN, False, outline_pts, 1)

        if len(ram_hist) >= 2:
            n = len(ram_hist)
            pts = []
            for i, v in enumerate(ram_hist):
                px = graph_x + int((i / max(1, n - 1)) * graph_w)
                py = graph_y + graph_h - int(max(0.0, min(1.0, v / 100.0)) * graph_h)
                pts.append((px, py))
            if len(pts) > 1:
                pygame.draw.lines(surface, AMBER, False, pts, 1)

        pygame.draw.rect(surface, DIM, (graph_x, graph_y, graph_w, graph_h), 1)

        per_core = snap.get("cpu_per_core", [])
        if per_core:
            bar_y = graph_y + graph_h + 6
            bar_area_h = h - (bar_y - y) - 6
            n_cores = len(per_core)
            bar_w = max(4, (graph_w - (n_cores - 1) * 3) // n_cores)
            for i, cv in enumerate(per_core):
                bx = graph_x + i * (bar_w + 3)
                bh = int(max(0.0, min(1.0, cv / 100.0)) * bar_area_h)
                pygame.draw.rect(surface, DIM, (bx, bar_y, bar_w, bar_area_h), 1)
                if bh > 0:
                    p_col = CYAN if cv < 80 else ALERT
                    pygame.draw.rect(surface, p_col, (bx + 1, bar_y + bar_area_h - bh + 1, bar_w - 2, bh - 1))

    def _draw_health(self, surface: "pygame.Surface", x: int, y: int,
                     w: int, h: int, snap: Dict[str, Any]) -> None:
        title = self.font.render("SYSTEM HEALTH :: stability + EKG", True, MUTED)
        surface.blit(title, (x + 8, y + 4))

        stability = snap.get("stability_score", 100.0)
        gauge_cx = x + w // 4
        gauge_cy = y + h - 16
        gauge_r = min(w // 4 - 12, h - 40)
        
        draw_arc_gauge(surface, gauge_cx, gauge_cy, gauge_r, stability / 100.0)
        stab_lbl = self.tiny.render(f"{stability:.0f}%", True, WHITE)
        surface.blit(stab_lbl, (gauge_cx - stab_lbl.get_width() // 2, gauge_cy - 8))
        stab_sub = self.tiny.render("STABILITY", True, MUTED)
        surface.blit(stab_sub, (gauge_cx - stab_sub.get_width() // 2, gauge_cy + 4))

        ekg_x0 = x + w // 2 + 8
        ekg_x1 = x + w - 8
        ekg_y0 = y + 24
        ekg_y1 = y + h - 8
        draw_ekg(surface, ekg_x0, ekg_y0, ekg_x1 - ekg_x0, ekg_y1 - ekg_y0, self._ekg_phase, CYAN)


# ===========================================================================
# PANEL OVERLAY: Daemon Status, Voice Activity, Global Alerts
# ===========================================================================
class DaemonOverlayRenderer:
    """Renders daemon status indicators, voice activity, and global alerts."""

    def __init__(self) -> None:
        self.font = None
        self.tiny = None
        self.title_font = None
        if HAS_PYGAME:
            cands = ["consolas", "menlo", "dejavusansmono", "couriernew", "monospace"]
            self.font = pygame.font.SysFont(cands, 12, bold=True)
            self.tiny = pygame.font.SysFont(cands, 10)
            self.title_font = pygame.font.SysFont(cands, 16, bold=True)

    def render(self, surface: "pygame.Surface", snap: Dict[str, Any], dt: float) -> None:
        if not HAS_PYGAME: return

        daemons = [
            ("HW", snap.get("cpu_temp", 0.0) > 0.0),
            ("NET", snap.get("internet_up", False)),
            ("DSP", snap.get("audio_volume", 0.0) >= 0.0),
            ("VOX", True),
            ("RSS", len(snap.get("news_items", [])) > 0),
            ("LLM", bool(snap.get("llm_stream", ""))),
            ("PRO", snap.get("daemon_override", False))
        ]

        x_start = Config.WIDTH - 280
        y = 6
        for name, active in daemons:
            col = CYAN if active else DIM
            if name == "PRO" and active:
                col = ALERT if (time.time() % 0.5 < 0.25) else AMBER
            
            pygame.draw.circle(surface, col, (x_start + 4, y + 5), 3)
            if active:
                pygame.draw.circle(surface, col, (x_start + 4, y + 5), 5, 1)
                
            img = self.tiny.render(name, True, col)
            surface.blit(img, (x_start + 10, y))
            x_start += 36

        transcript = snap.get("transcript", "")
        vol = snap.get("audio_volume", 0.0)
        
        if transcript or vol > 0.01:
            overlay_y = 611
            overlay_x = 10
            overlay_w = 1238
            bar = pygame.Surface((overlay_w, 18), pygame.SRCALPHA)
            bar.fill((0, 0, 0, 200))
            pygame.draw.rect(bar, (90, 90, 90, 255), (0, 0, overlay_w, 18), 1)
            surface.blit(bar, (overlay_x, overlay_y))
            
            vol_w = int(40 * min(1.0, vol * 15.0))
            pygame.draw.rect(surface, DIM, (overlay_x + 6, overlay_y + 5, 40, 8), 1)
            if vol_w > 0:
                pygame.draw.rect(surface, CYAN, (overlay_x + 7, overlay_y + 6, vol_w - 1, 6))
            
            display_text = transcript if transcript else "[ AWAITING VOICE INPUT ]"
            text_col = WHITE if transcript else INK
            text_img = self.font.render(f"> {display_text}", True, text_col)
            surface.blit(text_img, (overlay_x + 55, overlay_y + 2))

        if snap.get("daemon_override", False):
            msg = snap.get("daemon_msg", "")
            if msg:
                banner_y = Config.HEIGHT // 2 - 30
                banner_x = 200
                banner_w = Config.WIDTH - 400
                banner_h = 60
                
                banner = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
                flash_alpha = 180 + int(75 * abs(math.sin(time.time() * 4.0)))
                banner.fill((255, 30, 20, flash_alpha))
                pygame.draw.rect(banner, (255, 255, 255, 200), (0, 0, banner_w, banner_h), 2)
                surface.blit(banner, (banner_x, banner_y))
                
                text_img = self.title_font.render(msg, True, WHITE)
                text_rect = text_img.get_rect(center=(banner_x + banner_w // 2, banner_y + banner_h // 2))
                surface.blit(text_img, text_rect)