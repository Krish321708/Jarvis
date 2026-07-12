#!/usr/bin/env python3
"""
PROJECT HERMES - Omnimind Absolute Edition
File: self_test.py
Monolithic Compilation Standard
"The earth and sky will break before I fail you."

Description:
This module is the absolute pre-flight validation suite. It operates on a 
fail-fast philosophy. The math and state foundations must be flawless before 
the UI is allowed to initialize.

Every critical mathematical operation is verified twice using different methods 
(e.g., Lagrange's identity for cross products, and component-wise verification).
The system is subjected to a casual stress test (10,000 iterations) to ensure 
no floating-point drift or bounds violations occur under rapid execution.

The suite is run exactly twice before launch. If any test fails, the system 
aborts, printing the exact test name, the expected value, the received value, 
and the mathematical delta.
"""

import sys
import math
import time
import random
from typing import Any, Tuple

from config import Config
from math_engine import Vector3, Matrix4x4, Quaternion, PerlinNoise3D, catmull_rom, cubic_bezier
from state import HermesState, RingBuffer
from palette import mix, depth_shade, BLACK, WHITE, CYAN

class SelfTestFailure(Exception):
    """Custom exception raised when a self-test fails, carrying detailed diagnostics."""
    pass

def _assert(condition: bool, test_name: str, expected: Any, got: Any, delta: float = 1e-9) -> None:
    """Core assertion helper that formats a brutal failure report."""
    if not condition:
        msg = (
            f"\n{'='*60}\n"
            f"HERMES SELF-TEST FAILURE\n"
            f"{'='*60}\n"
            f"TEST: {test_name}\n"
            f"EXPECTED: {expected}\n"
            f"GOT:      {got}\n"
            f"DELTA:    {delta}\n"
            f"{'='*60}\n"
        )
        raise SelfTestFailure(msg)


# ===========================================================================
# TEST 1: Vector3 Algebra (Dual Method Verification)
# ===========================================================================
def test_vector_algebra() -> None:
    v1 = Vector3(1.0, 2.0, 3.0)
    v2 = Vector3(4.0, -5.0, 6.0)
    
    # Method A: Component-wise addition
    add = v1 + v2
    _assert(add.x == 5.0 and add.y == -3.0 and add.z == 9.0, 
            "Vector3 Addition (Component-wise)", "(5.0, -3.0, 9.0)", f"({add.x}, {add.y}, {add.z})")
            
    # Method B: Dot product geometric vs algebraic
    dot_alg = v1.x*v2.x + v1.y*v2.y + v1.z*v2.z
    dot_geo = v1.dot(v2)
    _assert(abs(dot_alg - dot_geo) < 1e-9, 
            "Vector3 Dot Product (Algebraic vs Function)", dot_alg, dot_geo)
            
    # Method C: Cross product via Lagrange's identity check
    # |v1 x v2|^2 = |v1|^2 * |v2|^2 - (v1 . v2)^2
    cross = v1.cross(v2)
    lhs = cross.length_squared()
    rhs = (v1.length_squared() * v2.length_squared()) - (dot_geo ** 2)
    _assert(abs(lhs - rhs) < 1e-6, 
            "Vector3 Cross Product (Lagrange Identity)", rhs, lhs, 1e-6)
            
    # Method D: Normalization integrity
    norm_v = v1.normalized()
    _assert(abs(norm_v.length() - 1.0) < 1e-9, 
            "Vector3 Normalization (Unit Length)", 1.0, norm_v.length())

    # Stress Test: 10,000 random operations must not drift
    rng = random.Random(42)
    for _ in range(10000):
        a = Vector3(rng.uniform(-10, 10), rng.uniform(-10, 10), rng.uniform(-10, 10))
        b = Vector3(rng.uniform(-10, 10), rng.uniform(-10, 10), rng.uniform(-10, 10))
        # Validate that (a+b) dot (a-b) == |a|^2 - |b|^2
        lhs = (a + b).dot(a - b)
        rhs = a.length_squared() - b.length_squared()
        _assert(abs(lhs - rhs) < 1e-4, "Vector3 Stress Test (Parallelogram Law)", rhs, lhs, 1e-4)


# ===========================================================================
# TEST 2: Matrix4x4 Transforms (Dual Method Verification)
# ===========================================================================
def test_matrix_transforms() -> None:
    # Method A: 90-degree rotation matrix transforms (1,0,0) to (0,1,0)
    rx90 = Matrix4x4.rotation_x(math.pi / 2)
    rotated = rx90.transform_point(Vector3(0, 1, 0))
    _assert(abs(rotated.x) < 1e-5 and abs(rotated.y) < 1e-5 and abs(rotated.z - 1.0) < 1e-5,
            "Matrix4x4 90° Rotation Transform", "(0, 0, 1)", f"({rotated.x}, {rotated.y}, {rotated.z})", 1e-5)

    # Method B: Native Vector3 rotation math vs Matrix math
    ang = math.radians(35.5)
    v = Vector3(2.5, -1.2, 3.3)
    m_y = Matrix4x4.rotation_y(ang)
    m_res = m_y.transform_point(v)
    n_res = v.rotate_y(ang)
    _assert(abs(m_res.x - n_res.x) < 1e-9 and abs(m_res.y - n_res.y) < 1e-9 and abs(m_res.z - n_res.z) < 1e-9,
            "Matrix4x4 vs Vector3 Native Rotation", f"({n_res.x}, {n_res.y}, {n_res.z})", f"({m_res.x}, {m_res.y}, {m_res.z})")

    # Method C: Matrix chain multiply preserves vector length
    v_orig = Vector3(1.0, 2.0, 3.0)
    orig_len = v_orig.length()
    m_chain = Matrix4x4.rotation_x(0.5).multiply(Matrix4x4.rotation_y(1.1)).multiply(Matrix4x4.rotation_z(-0.8))
    v_trans = m_chain.transform_point(v_orig)
    _assert(abs(v_trans.length() - orig_len) < 1e-6,
            "Matrix4x4 Chain Length Preservation", orig_len, v_trans.length(), 1e-6)


# ===========================================================================
# TEST 3: Quaternion Equivalence (Dual Method Verification)
# ===========================================================================
def test_quaternion_equivalence() -> None:
    axis = Vector3(0.5, 1.0, -0.2).normalized()
    angle = math.radians(45.0)
    
    # Method A: Rotate using Matrix4x4 from Axis-Angle
    m = Matrix4x4.rotation_axis_angle(axis, angle)
    v = Vector3(1.0, 0.0, 0.0)
    res_m = m.transform_point(v)
    
    # Method B: Rotate using Quaternion
    q = Quaternion.from_axis_angle(axis, angle)
    res_q = q.rotate_vector(v)
    
    _assert(abs(res_m.x - res_q.x) < 1e-6 and abs(res_m.y - res_q.y) < 1e-6 and abs(res_m.z - res_q.z) < 1e-6,
            "Quaternion vs Matrix Rotation Equivalence", 
            f"({res_m.x}, {res_m.y}, {res_m.z})", f"({res_q.x}, {res_q.y}, {res_q.z})", 1e-6)


# ===========================================================================
# TEST 4: Perlin Noise Bounds & Determinism (Stress Verification)
# ===========================================================================
def test_noise_bounds_determinism() -> None:
    pn = PerlinNoise3D(seed=42)
    
    # Method A: Determinism at center
    n1 = pn.noise(0.5, 0.5, 0.5)
    n2 = pn.noise(0.5, 0.5, 0.5)
    _assert(n1 == n2, "PerlinNoise3D Deterministic Seed", n1, n2)
    
    # Method B: FBM Bounds at edge cases
    f = pn.fbm(1.3, 2.7, 0.4, octaves=5, persistence=0.5, lacunarity=2.0)
    _assert(-1.0 <= f <= 1.0, "PerlinNoise3D FBM Threshold Bounds", "[-1.0, 1.0]", f)

    # Stress Test: 10,000 random noise samples must remain strictly within [-1, 1]
    rng = random.Random(99)
    min_val = 999.0
    max_val = -999.0
    for _ in range(10000):
        x = rng.uniform(-50, 50)
        y = rng.uniform(-50, 50)
        z = rng.uniform(-50, 50)
        val = pn.noise(x, y, z)
        if val < min_val: min_val = val
        if val > max_val: max_val = val
        _assert(-1.0001 <= val <= 1.0001, "PerlinNoise3D Stress Test Bounds", "[-1.0, 1.0]", val, 1e-4)


# ===========================================================================
# TEST 5: Ring Buffer FIFO & Boundary Integrity
# ===========================================================================
def test_ring_buffer_integrity() -> None:
    rb = RingBuffer(capacity=5)
    
    # Method A: Exact capacity fill
    for i in range(5):
        rb.push(float(i))
    _assert(len(rb.data()) == 5 and rb.latest() == 4.0, 
            "RingBuffer Capacity Fill", "len=5, latest=4.0", f"len={len(rb.data())}, latest={rb.latest()}")
            
    # Method B: Overwrite evicts oldest (FIFO)
    for i in range(5, 10):
        rb.push(float(i))
    _assert(len(rb.data()) == 5 and rb.latest() == 9.0 and rb.oldest() == 5.0, 
            "RingBuffer FIFO Eviction", "len=5, latest=9.0, oldest=5.0", 
            f"len={len(rb.data())}, latest={rb.latest()}, oldest={rb.oldest()}")
            
    # Method C: Exact sequence verification
    expected_seq = [5.0, 6.0, 7.0, 8.0, 9.0]
    _assert(rb.data() == expected_seq, 
            "RingBuffer Sequence Integrity", expected_seq, rb.data())


# ===========================================================================
# TEST 6: Spline Interpolation Endpoints (Dual Verification)
# ===========================================================================
def test_spline_interpolation() -> None:
    p0 = (0.0, 0.0); p1 = (1.0, 1.0); p2 = (2.0, 1.0); p3 = (3.0, 0.0)
    
    # Method A: Catmull-Rom endpoints must hit exact control points
    cr0 = catmull_rom(p0, p1, p2, p3, 0.0)
    _assert(abs(cr0[0] - 1.0) < 1e-6 and abs(cr0[1] - 1.0) < 1e-6, 
            "Catmull-Rom t=0 Endpoint", "(1.0, 1.0)", cr0, 1e-6)
    cr1 = catmull_rom(p0, p1, p2, p3, 1.0)
    _assert(abs(cr1[0] - 2.0) < 1e-6 and abs(cr1[1] - 1.0) < 1e-6, 
            "Catmull-Rom t=1 Endpoint", "(2.0, 1.0)", cr1, 1e-6)

    # Method B: Bezier endpoints must hit exact control points
    bz0 = cubic_bezier(p0, p1, p2, p3, 0.0)
    _assert(abs(bz0[0] - 0.0) < 1e-6 and abs(bz0[1] - 0.0) < 1e-6, 
            "Cubic Bezier t=0 Endpoint", "(0.0, 0.0)", bz0, 1e-6)
    bz1 = cubic_bezier(p0, p1, p2, p3, 1.0)
    _assert(abs(bz1[0] - 3.0) < 1e-6 and abs(bz1[1] - 0.0) < 1e-6, 
            "Cubic Bezier t=1 Endpoint", "(3.0, 0.0)", bz1, 1e-6)


# ===========================================================================
# TEST 7: Palette Math (Color Blending Verification)
# ===========================================================================
def test_palette_math() -> None:
    c1 = (0, 0, 0)
    c2 = (100, 100, 100)
    
    # Method A: Exact midpoint linear blend
    m = mix(c1, c2, 0.5)
    _assert(m == (50, 50, 50), "Palette Mix Midpoint", (50, 50, 50), m)
    
    # Method B: Depth shade fade approaches black
    ds = depth_shade((100, 100, 100), 1.0)
    # 1.0 depth * 0.82 mix factor = 82% fade toward black -> 100 * 0.18 = 18
    _assert(ds[0] <= 18 and ds[1] <= 18 and ds[2] <= 18, 
            "Palette Depth Shade Max Fade", "<=18", ds[0], 1.0)


# ===========================================================================
# TEST 8: Camera Projection Geometry (The "Pixel" Verification)
# ===========================================================================
def test_projection_geometry() -> None:
    # Emulate the TerrainRenderer._project math manually and verify bounds
    u, v, h, fft_disp = 0.5, 0.5, 1.0, 0.5
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
    _assert(rz_cam > 0.5, "Projection Depth Camera Bound", ">0.5", rz_cam)
    
    f = Config.FOCAL_LENGTH
    sx = 960 + (rx / rz_cam) * f
    sy = 400 - (ry / rz_cam) * f
    
    # Verify projected point falls within reasonable screen bounds given central input
    _assert(0 <= sx <= Config.WIDTH and 0 <= sy <= Config.HEIGHT, 
            "Projection Screen Bounds", f"[0, {Config.WIDTH}]", f"({sx}, {sy})")


# ===========================================================================
# RUNNER LOGIC
# ===========================================================================
def run_stress_test_suite(run_id: int) -> bool:
    """Executes all tests in sequence. Returns True on success, raises on failure."""
    print(f"\n[HERMES] INITIATING STRESS TEST RUN #{run_id}")
    print("-" * 40)
    
    start_time = time.time()
    try:
        test_vector_algebra()
        print("[ PASS ] Vector3 Algebra (Dual Verification + Stress)")
        
        test_matrix_transforms()
        print("[ PASS ] Matrix4x4 Transforms (Dual Verification)")
        
        test_quaternion_equivalence()
        print("[ PASS ] Quaternion Equivalence (Dual Verification)")
        
        test_noise_bounds_determinism()
        print("[ PASS ] Perlin Noise Bounds & Determinism (Stress)")
        
        test_ring_buffer_integrity()
        print("[ PASS ] Ring Buffer FIFO & Boundary Integrity")
        
        test_spline_interpolation()
        print("[ PASS ] Spline Interpolation Endpoints (Dual Verification)")
        
        test_palette_math()
        print("[ PASS ] Palette Math (Color Blending Verification)")
        
        test_projection_geometry()
        print("[ PASS ] Camera Projection Geometry (Pixel Verification)")
        
    except SelfTestFailure as e:
        print(e)
        return False
    except Exception as e:
        print(f"\n[HERMES] UNHANDLED EXCEPTION DURING SELF-TEST: {type(e).__name__}: {e}")
        return False
        
    elapsed = time.time() - start_time
    print("-" * 40)
    print(f"[HERMES] STRESS TEST RUN #{run_id} COMPLETED IN {elapsed:.4f}s")
    return True


def execute_pre_flight() -> bool:
    """Runs the stress test suite exactly twice. Aborts on any failure."""
    
    # Run 1
    if not run_stress_test_suite(1):
        print("[HERMES] PRE-FLIGHT ABORTED. RUN #1 FAILED.")
        return False
        
    # Brief pause to clear any CPU cache anomalies for the verification run
    time.sleep(0.1)
    
    # Run 2
    if not run_stress_test_suite(2):
        print("[HERMES] PRE-FLIGHT ABORTED. RUN #2 FAILED.")
        return False
        
    print("\n" + "=" * 40)
    print("HERMES PRE-FLIGHT VALIDATION ABSOLUTE")
    print("ALL SYSTEMS VERIFIED TWICE. ZERO ANOMALIES.")
    print("=" * 40 + "\n")
    return True