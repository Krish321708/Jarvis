#!/usr/bin/env python3
"""
PROJECT HERMES - Omnimind Absolute Edition
File: math_engine.py
Monolithic Compilation Standard
"The earth and sky will break before I fail you."

Description:
This module serves as the absolute mathematical foundation for the HERMES Omnimind.
It contains exhaustive, precision-tuned implementations of 3D vector algebra,
4x4 transformation matrices, Quaternions, Perlin/Simplex noise generators, 
spline interpolations, and computational geometry intersections.

Every function is designed for maximum numerical stability and deterministic output.
No external dependencies are used outside of Python's standard `math` and `random` libraries.
"""

import math
import random
from typing import List, Tuple, Optional, Dict, Any, Callable, Iterator, Sequence

# ===========================================================================
# SECTION 1.1 — Global Math Constants
# ===========================================================================
PI = math.pi
TAU = math.pi * 2.0
HALF_PI = math.pi / 2.0
QUARTER_PI = math.pi / 4.0
EULER = math.e
EPSILON = 1e-9
DEG2RAD = PI / 180.0
RAD2DEG = 180.0 / PI

# ===========================================================================
# SECTION 1.2 — General Math Utility Functions
# ===========================================================================

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a scalar value between min and max bounds."""
    if value < min_val:
        return min_val
    if value > max_val:
        return max_val
    return value

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b by scalar t. t is not clamped."""
    return a + (b - a) * t

def inv_lerp(a: float, b: float, v: float) -> float:
    """Inverse linear interpolation returning the fraction t of v between a and b."""
    if abs(b - a) < EPSILON:
        return 0.0
    return (v - a) / (b - a)

def remap(v: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    """Map a value from one range to another."""
    t = inv_lerp(in_min, in_max, v)
    return lerp(out_min, out_max, t)

def smoothstep(edge0: float, edge1: float, x: float) -> float:
    """Performs smooth Hermite interpolation between 0 and 1 when edge0 < x < edge1."""
    t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)

def smootherstep(edge0: float, edge1: float, x: float) -> float:
    """Ken Perlin's improved smoothstep with zero 1st and 2nd order derivatives at edges."""
    t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)

def is_power_of_two(n: int) -> bool:
    """Returns True if n is a power of two."""
    return n > 0 and (n & (n - 1)) == 0

def next_power_of_two(n: int) -> int:
    """Returns the next highest power of two of n."""
    if n <= 0:
        return 1
    n -= 1
    n |= n >> 1
    n |= n >> 2
    n |= n >> 4
    n |= n >> 8
    n |= n >> 16
    n |= n >> 32
    return n + 1

def factorial(n: int) -> int:
    """Computes n! iteratively."""
    if n < 0:
        raise ValueError("Factorial not defined for negative values")
    res = 1
    for i in range(2, n + 1):
        res *= i
    return res

def binomial_coefficient(n: int, k: int) -> int:
    """Computes n choose k (nCk)."""
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    k = min(k, n - k)
    res = 1
    for i in range(1, k + 1):
        res = res * (n - k + i) // i
    return res

# ===========================================================================
# SECTION 2.1 — Vector3 Class
# ===========================================================================
class Vector3:
    """
    High-precision 3D vector implementation with exhaustive arithmetic,
    geometric, and utility operations. Uses __slots__ for memory efficiency.
    """
    __slots__ = ("x", "y", "z")

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> None:
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    # ------------------------------------------------------------------
    # Basic Arithmetic Operators
    # ------------------------------------------------------------------
    def __add__(self, other: "Vector3") -> "Vector3":
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vector3") -> "Vector3":
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, s: float) -> "Vector3":
        return Vector3(self.x * s, self.y * s, self.z * s)

    __rmul__ = __mul__

    def __truediv__(self, s: float) -> "Vector3":
        if abs(s) < EPSILON:
            raise ZeroDivisionError("Cannot divide Vector3 by zero scalar")
        inv_s = 1.0 / s
        return Vector3(self.x * inv_s, self.y * inv_s, self.z * inv_s)

    def __neg__(self) -> "Vector3":
        return Vector3(-self.x, -self.y, -self.z)

    def __pos__(self) -> "Vector3":
        return Vector3(self.x, self.y, self.z)

    def __iadd__(self, other: "Vector3") -> "Vector3":
        self.x += other.x
        self.y += other.y
        self.z += other.z
        return self

    def __isub__(self, other: "Vector3") -> "Vector3":
        self.x -= other.x
        self.y -= other.y
        self.z -= other.z
        return self

    def __imul__(self, s: float) -> "Vector3":
        self.x *= s
        self.y *= s
        self.z *= s
        return self

    def __itruediv__(self, s: float) -> "Vector3":
        if abs(s) < EPSILON:
            raise ZeroDivisionError("Cannot divide Vector3 by zero scalar")
        inv_s = 1.0 / s
        self.x *= inv_s
        self.y *= inv_s
        self.z *= inv_s
        return self

    # ------------------------------------------------------------------
    # Comparison Operators
    # ------------------------------------------------------------------
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector3):
            return NotImplemented
        return (abs(self.x - other.x) < EPSILON and
                abs(self.y - other.y) < EPSILON and
                abs(self.z - other.z) < EPSILON)

    def __ne__(self, other: object) -> bool:
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __hash__(self) -> int:
        return hash((round(self.x, 6), round(self.y, 6), round(self.z, 6)))

    # ------------------------------------------------------------------
    # Sequence Interface
    # ------------------------------------------------------------------
    def __getitem__(self, index: int) -> float:
        if index == 0: return self.x
        if index == 1: return self.y
        if index == 2: return self.z
        raise IndexError("Vector3 index out of range")

    def __setitem__(self, index: int, value: float) -> None:
        if index == 0: self.x = float(value)
        elif index == 1: self.y = float(value)
        elif index == 2: self.z = float(value)
        else: raise IndexError("Vector3 index out of range")

    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y
        yield self.z

    def __len__(self) -> int:
        return 3

    def __repr__(self) -> str:
        return f"Vector3({self.x:.6f}, {self.y:.6f}, {self.z:.6f})"

    def __str__(self) -> str:
        return f"<{self.x:.3f}, {self.y:.3f}, {self.z:.3f}>"

    # ------------------------------------------------------------------
    # Vector Geometric Operations
    # ------------------------------------------------------------------
    def dot(self, other: "Vector3") -> float:
        """Computes the dot (scalar) product."""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: "Vector3") -> "Vector3":
        """Computes the cross (vector) product."""
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )

    def length_squared(self) -> float:
        """Computes the squared magnitude of the vector. Faster than length()."""
        return self.x * self.x + self.y * self.y + self.z * self.z

    def length(self) -> float:
        """Computes the Euclidean magnitude (L2 norm) of the vector."""
        return math.sqrt(self.length_squared())

    def magnitude(self) -> float:
        """Alias for length()."""
        return self.length()

    def normalize(self) -> "Vector3":
        """Returns a normalized (unit length) copy of this vector."""
        L = self.length()
        if L < EPSILON:
            return Vector3(0.0, 0.0, 0.0)
        inv_L = 1.0 / L
        return Vector3(self.x * inv_L, self.y * inv_L, self.z * inv_L)

    def normalized(self) -> "Vector3":
        """Alias for normalize()."""
        return self.normalize()

    def normalize_ip(self) -> None:
        """Normalizes the vector in-place."""
        L = self.length()
        if L > EPSILON:
            inv_L = 1.0 / L
            self.x *= inv_L
            self.y *= inv_L
            self.z *= inv_L
        else:
            self.x = self.y = self.z = 0.0

    def distance_to(self, other: "Vector3") -> float:
        """Computes the Euclidean distance between two vectors."""
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx*dx + dy*dy + dz*dz)

    def distance_squared_to(self, other: "Vector3") -> float:
        """Computes the squared Euclidean distance between two vectors."""
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return dx*dx + dy*dy + dz*dz

    def angle_to(self, other: "Vector3") -> float:
        """Computes the angle in radians between this vector and another."""
        dot_prod = self.dot(other)
        len_prod = self.length() * other.length()
        if len_prod < EPSILON:
            return 0.0
        # Clamp to handle floating point inaccuracies
        c = clamp(dot_prod / len_prod, -1.0, 1.0)
        return math.acos(c)

    def lerp(self, other: "Vector3", t: float) -> "Vector3":
        """Linearly interpolates between this vector and another by t."""
        t = clamp(t, 0.0, 1.0)
        return Vector3(
            self.x + (other.x - self.x) * t,
            self.y + (other.y - self.y) * t,
            self.z + (other.z - self.z) * t
        )

    def slerp(self, other: "Vector3", t: float) -> "Vector3":
        """Spherically interpolates between two vectors. 
        Vectors should be treated as directions."""
        dot = clamp(self.normalize().dot(other.normalize()), -1.0, 1.0)
        theta = math.acos(dot) * t
        relative_vec = (other - self * dot).normalized()
        return (self * math.cos(theta)) + (relative_vec * math.sin(theta))

    def reflect(self, normal: "Vector3") -> "Vector3":
        """Reflects this vector off a surface with the given normal."""
        d = self.dot(normal)
        return Vector3(
            self.x - 2.0 * d * normal.x,
            self.y - 2.0 * d * normal.y,
            self.z - 2.0 * d * normal.z
        )

    def refract(self, normal: "Vector3", eta: float) -> "Vector3":
        """Refracts this vector through a surface with the given normal and ratio of indices of refraction eta."""
        n = normal
        i = self
        cosi = -n.dot(i)
        sin2t = eta * eta * (1.0 - cosi * cosi)
        if sin2t > 1.0:
            return Vector3(0.0, 0.0, 0.0)  # Total internal reflection
        cost = math.sqrt(1.0 - sin2t)
        return i * eta + n * (eta * cosi - cost)

    def rotate_x(self, angle: float) -> "Vector3":
        """Rotates the vector around the X-axis by angle (radians)."""
        c, s = math.cos(angle), math.sin(angle)
        return Vector3(self.x, self.y * c - self.z * s, self.y * s + self.z * c)

    def rotate_y(self, angle: float) -> "Vector3":
        """Rotates the vector around the Y-axis by angle (radians)."""
        c, s = math.cos(angle), math.sin(angle)
        return Vector3(self.x * c + self.z * s, self.y, -self.x * s + self.z * c)

    def rotate_z(self, angle: float) -> "Vector3":
        """Rotates the vector around the Z-axis by angle (radians)."""
        c, s = math.cos(angle), math.sin(angle)
        return Vector3(self.x * c - self.y * s, self.x * s + self.y * c, self.z)

    def rotate_axis(self, axis: "Vector3", angle: float) -> "Vector3":
        """Rotates the vector around an arbitrary normalized axis by angle (radians).
        Uses Rodrigues' rotation formula."""
        axis_n = axis.normalized()
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        one_minus_cos = 1.0 - cos_a
        
        # Cross product part
        cross = self.cross(axis_n)
        # Dot product part
        dot = self.dot(axis_n)
        
        return Vector3(
            self.x * cos_a + cross.x * sin_a + axis_n.x * dot * one_minus_cos,
            self.y * cos_a + cross.y * sin_a + axis_n.y * dot * one_minus_cos,
            self.z * cos_a + cross.z * sin_a + axis_n.z * dot * one_minus_cos
        )

    def project(self, other: "Vector3") -> "Vector3":
        """Projects this vector onto another vector."""
        denom = other.length_squared()
        if denom < EPSILON:
            return Vector3(0.0, 0.0, 0.0)
        d = self.dot(other) / denom
        return other * d

    def reject(self, other: "Vector3") -> "Vector3":
        """Returns the component of this vector perpendicular to another vector."""
        return self - self.project(other)

    def abs(self) -> "Vector3":
        """Returns a vector with the absolute values of each component."""
        return Vector3(abs(self.x), abs(self.y), abs(self.z))

    def min_comp(self) -> float:
        """Returns the minimum component value of the vector."""
        return min(self.x, self.y, self.z)

    def max_comp(self) -> float:
        """Returns the maximum component value of the vector."""
        return max(self.x, self.y, self.z)

    def min(self, other: "Vector3") -> "Vector3":
        """Returns a vector with the minimum components of both vectors."""
        return Vector3(min(self.x, other.x), min(self.y, other.y), min(self.z, other.z))

    def max(self, other: "Vector3") -> "Vector3":
        """Returns a vector with the maximum components of both vectors."""
        return Vector3(max(self.x, other.x), max(self.y, other.y), max(self.z, other.z))

    def clamp(self, min_v: "Vector3", max_v: "Vector3") -> "Vector3":
        """Clamps each component between the corresponding components of min_v and max_v."""
        return Vector3(
            clamp(self.x, min_v.x, max_v.x),
            clamp(self.y, min_v.y, max_v.y),
            clamp(self.z, min_v.z, max_v.z)
        )

    def to_tuple(self) -> Tuple[float, float, float]:
        """Converts to a standard Python tuple."""
        return (self.x, self.y, self.z)

    def to_list(self) -> List[float]:
        """Converts to a standard Python list."""
        return [self.x, self.y, self.z]

    @staticmethod
    def from_tuple(t: Tuple[float, float, float]) -> "Vector3":
        """Constructs a Vector3 from a tuple."""
        return Vector3(t[0], t[1], t[2])

    @staticmethod
    def zero() -> "Vector3":
        return Vector3(0.0, 0.0, 0.0)

    @staticmethod
    def one() -> "Vector3":
        return Vector3(1.0, 1.0, 1.0)

    @staticmethod
    def up() -> "Vector3":
        return Vector3(0.0, 1.0, 0.0)

    @staticmethod
    def down() -> "Vector3":
        return Vector3(0.0, -1.0, 0.0)

    @staticmethod
    def left() -> "Vector3":
        return Vector3(-1.0, 0.0, 0.0)

    @staticmethod
    def right() -> "Vector3":
        return Vector3(1.0, 0.0, 0.0)

    @staticmethod
    def forward() -> "Vector3":
        return Vector3(0.0, 0.0, 1.0)

    @staticmethod
    def back() -> "Vector3":
        return Vector3(0.0, 0.0, -1.0)


# ===========================================================================
# SECTION 2.2 — Matrix4x4 Class
# ===========================================================================
class Matrix4x4:
    """
    Row-major 4x4 transformation matrix for 3D point projection and linear algebra.
    Supports full transformations, inversions, transpositions, and projections.
    """
    __slots__ = ("m",)

    def __init__(self, m: Optional[List[List[float]]] = None) -> None:
        if m is None:
            self.m = [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]
        else:
            if len(m) != 4 or any(len(row) != 4 for row in m):
                raise ValueError("Matrix4x4 must be initialized with a 4x4 list of lists")
            self.m = [row[:] for row in m]

    def __repr__(self) -> str:
        rows = []
        for r in self.m:
            rows.append("  [" + ", ".join(f"{x:>10.6f}" for x in r) + "]")
        return "Matrix4x4(\n" + "\n".join(rows) + "\n)"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Matrix4x4):
            return NotImplemented
        for i in range(4):
            for j in range(4):
                if abs(self.m[i][j] - other.m[i][j]) > EPSILON:
                    return False
        return True

    def __mul__(self, other: "Matrix4x4") -> "Matrix4x4":
        return self.multiply(other)

    # ------------------------------------------------------------------
    # Static Matrix Generators
    # ------------------------------------------------------------------
    @staticmethod
    def identity() -> "Matrix4x4":
        return Matrix4x4()

    @staticmethod
    def zero() -> "Matrix4x4":
        return Matrix4x4([[0.0]*4 for _ in range(4)])

    @staticmethod
    def translation(tx: float, ty: float, tz: float) -> "Matrix4x4":
        return Matrix4x4([
            [1.0, 0.0, 0.0,  tx],
            [0.0, 1.0, 0.0,  ty],
            [0.0, 0.0, 1.0,  tz],
            [0.0, 0.0, 0.0, 1.0]
        ])

    @staticmethod
    def scaling(sx: float, sy: float, sz: float) -> "Matrix4x4":
        return Matrix4x4([
            [ sx, 0.0, 0.0, 0.0],
            [0.0,  sy, 0.0, 0.0],
            [0.0, 0.0,  sz, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ])

    @staticmethod
    def uniform_scaling(s: float) -> "Matrix4x4":
        return Matrix4x4.scaling(s, s, s)

    @staticmethod
    def rotation_x(angle: float) -> "Matrix4x4":
        c, s = math.cos(angle), math.sin(angle)
        return Matrix4x4([
            [1.0, 0.0, 0.0, 0.0],
            [0.0,   c,  -s, 0.0],
            [0.0,   s,   c, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ])

    @staticmethod
    def rotation_y(angle: float) -> "Matrix4x4":
        c, s = math.cos(angle), math.sin(angle)
        return Matrix4x4([
            [  c, 0.0,   s, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [ -s, 0.0,   c, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ])

    @staticmethod
    def rotation_z(angle: float) -> "Matrix4x4":
        c, s = math.cos(angle), math.sin(angle)
        return Matrix4x4([
            [  c,  -s, 0.0, 0.0],
            [  s,   c, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ])

    @staticmethod
    def rotation_axis_angle(axis: Vector3, angle: float) -> "Matrix4x4":
        """Creates a rotation matrix from an arbitrary axis and angle (Rodrigues)."""
        n = axis.normalized()
        x, y, z = n.x, n.y, n.z
        c = math.cos(angle)
        s = math.sin(angle)
        t = 1.0 - c
        return Matrix4x4([
            [t*x*x + c,   t*x*y - z*s, t*x*z + y*s, 0.0],
            [t*x*y + z*s, t*y*y + c,   t*y*z - x*s, 0.0],
            [t*x*z - y*s, t*y*z + x*s, t*z*z + c,   0.0],
            [0.0,         0.0,         0.0,         1.0]
        ])

    @staticmethod
    def perspective(fovy: float, aspect: float, z_near: float, z_far: float) -> "Matrix4x4":
        """Creates a right-handed perspective projection matrix."""
        f = 1.0 / math.tan(fovy / 2.0)
        nf = 1.0 / (z_near - z_far)
        return Matrix4x4([
            [f / aspect, 0.0, 0.0,                     0.0],
            [0.0,        f,   0.0,                     0.0],
            [0.0,        0.0, (z_far + z_near) * nf,   2.0 * z_far * z_near * nf],
            [0.0,        0.0, -1.0,                    0.0]
        ])

    @staticmethod
    def orthographic(left: float, right: float, bottom: float, top: float, 
                     z_near: float, z_far: float) -> "Matrix4x4":
        """Creates a right-handed orthographic projection matrix."""
        rl = 1.0 / (right - left)
        tb = 1.0 / (top - bottom)
        fn = 1.0 / (z_far - z_near)
        return Matrix4x4([
            [2.0 * rl, 0.0,      0.0,      -(right + left) * rl],
            [0.0,      2.0 * tb, 0.0,      -(top + bottom) * tb],
            [0.0,      0.0,     -2.0 * fn, -(z_far + z_near) * fn],
            [0.0,      0.0,      0.0,      1.0]
        ])

    @staticmethod
    def look_at(eye: Vector3, target: Vector3, up: Vector3) -> "Matrix4x4":
        """Creates a view matrix looking from eye to target with given up vector."""
        f = (target - eye).normalized()
        s = f.cross(up).normalized()
        u = s.cross(f)
        
        return Matrix4x4([
            [ s.x,  s.y,  s.z, -s.dot(eye)],
            [ u.x,  u.y,  u.z, -u.dot(eye)],
            [-f.x, -f.y, -f.z,  f.dot(eye)],
            [0.0,  0.0,  0.0,  1.0]
        ])

    # ------------------------------------------------------------------
    # Matrix Math Operations
    # ------------------------------------------------------------------
    def multiply(self, other: "Matrix4x4") -> "Matrix4x4":
        result = [[0.0]*4 for _ in range(4)]
        a, b = self.m, other.m
        for i in range(4):
            for j in range(4):
                s = 0.0
                for k in range(4):
                    s += a[i][k] * b[k][j]
                result[i][j] = s
        return Matrix4x4(result)

    def transpose(self) -> "Matrix4x4":
        return Matrix4x4([
            [self.m[0][0], self.m[1][0], self.m[2][0], self.m[3][0]],
            [self.m[0][1], self.m[1][1], self.m[2][1], self.m[3][1]],
            [self.m[0][2], self.m[1][2], self.m[2][2], self.m[3][2]],
            [self.m[0][3], self.m[1][3], self.m[2][3], self.m[3][3]]
        ])

    def determinant(self) -> float:
        """Computes the determinant of a 4x4 matrix using Laplace expansion."""
        m = self.m
        # Using first row expansion
        def minor3(mtrx: List[List[float]], i: int, j: int) -> float:
            sub = []
            for r in range(1, 4):
                row = []
                for c in range(4):
                    if c != j:
                        row.append(mtrx[r][c])
                sub.append(row)
            # 3x3 determinant
            a, b, c = sub[0][0], sub[0][1], sub[0][2]
            d, e, f = sub[1][0], sub[1][1], sub[1][2]
            g, h, i_ = sub[2][0], sub[2][1], sub[2][2]
            return a*(e*i_ - f*h) - b*(d*i_ - f*g) + c*(d*h - e*g)
        
        det = 0.0
        for j in range(4):
            sign = 1.0 if j % 2 == 0 else -1.0
            det += sign * m[0][j] * minor3(m, 0, j)
        return det

    def inverse(self) -> "Matrix4x4":
        """Computes the inverse matrix using Gauss-Jordan elimination."""
        # Create augmented matrix [M | I]
        aug = [self.m[i][:] + [1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]
        
        for col in range(4):
            # Pivot selection
            pivot_row = col
            max_val = abs(aug[col][col])
            for r in range(col + 1, 4):
                if abs(aug[r][col]) > max_val:
                    max_val = abs(aug[r][col])
                    pivot_row = r
            
            if max_val < EPSILON:
                raise ValueError("Matrix is singular and cannot be inverted")
                
            # Swap rows
            if pivot_row != col:
                aug[col], aug[pivot_row] = aug[pivot_row], aug[col]
                
            # Normalize pivot row
            pivot_val = aug[col][col]
            inv_pivot = 1.0 / pivot_val
            for c in range(8):
                aug[col][c] *= inv_pivot
                
            # Eliminate other rows
            for r in range(4):
                if r != col:
                    factor = aug[r][col]
                    if abs(factor) > EPSILON:
                        for c in range(8):
                            aug[r][c] -= factor * aug[col][c]
                            
        # Extract right half (the inverse)
        inv_m = [row[4:8] for row in aug]
        return Matrix4x4(inv_m)

    # ------------------------------------------------------------------
    # Transformations
    # ------------------------------------------------------------------
    def transform_point(self, v: Vector3) -> Vector3:
        """Transforms a point (implies w=1). Translation is applied."""
        m = self.m
        x = m[0][0] * v.x + m[0][1] * v.y + m[0][2] * v.z + m[0][3]
        y = m[1][0] * v.x + m[1][1] * v.y + m[1][2] * v.z + m[1][3]
        z = m[2][0] * v.x + m[2][1] * v.y + m[2][2] * v.z + m[2][3]
        # w is implicitly 1, but to be rigorous we could compute it.
        # Since standard transform preserves w=1 for affine, we return directly.
        return Vector3(x, y, z)

    def transform_vector(self, v: Vector3) -> Vector3:
        """Transforms a direction vector (implies w=0). Translation ignored."""
        m = self.m
        x = m[0][0] * v.x + m[0][1] * v.y + m[0][2] * v.z
        y = m[1][0] * v.x + m[1][1] * v.y + m[1][2] * v.z
        z = m[2][0] * v.x + m[2][1] * v.y + m[2][2] * v.z
        return Vector3(x, y, z)

    def get_translation(self) -> Vector3:
        return Vector3(self.m[0][3], self.m[1][3], self.m[2][3])

    def get_scale(self) -> Vector3:
        """Extracts approximate scale from the transformation matrix columns."""
        sx = Vector3(self.m[0][0], self.m[1][0], self.m[2][0]).length()
        sy = Vector3(self.m[0][1], self.m[1][1], self.m[2][1]).length()
        sz = Vector3(self.m[0][2], self.m[1][2], self.m[2][2]).length()
        return Vector3(sx, sy, sz)


# ===========================================================================
# SECTION 3.1 — Quaternion Class
# ===========================================================================
class Quaternion:
    """
    High-precision Quaternion for stable 3D rotations without gimbal lock.
    Stored as (w, x, y, z).
    """
    __slots__ = ("w", "x", "y", "z")

    def __init__(self, w: float = 1.0, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> None:
        self.w = float(w)
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __repr__(self) -> str:
        return f"Quaternion(w={self.w:.6f}, x={self.x:.6f}, y={self.y:.6f}, z={self.z:.6f})"

    def __mul__(self, other: "Quaternion") -> "Quaternion":
        """Quaternion multiplication (Hamilton product)."""
        w1, x1, y1, z1 = self.w, self.x, self.y, self.z
        w2, x2, y2, z2 = other.w, other.x, other.y, other.z
        return Quaternion(
            w1*w2 - x1*x2 - y1*y2 - z1*z2,
            w1*x2 + x1*w2 + y1*z2 - z1*y2,
            w1*y2 - x1*z2 + y1*w2 + z1*x2,
            w1*z2 + x1*y2 - y1*x2 + z1*w2
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Quaternion):
            return NotImplemented
        return (abs(self.w - other.w) < EPSILON and
                abs(self.x - other.x) < EPSILON and
                abs(self.y - other.y) < EPSILON and
                abs(self.z - other.z) < EPSILON)

    def length_squared(self) -> float:
        return self.w*self.w + self.x*self.x + self.y*self.y + self.z*self.z

    def length(self) -> float:
        return math.sqrt(self.length_squared())

    def normalize(self) -> "Quaternion":
        L = self.length()
        if L < EPSILON:
            return Quaternion(1.0, 0.0, 0.0, 0.0)
        inv_L = 1.0 / L
        return Quaternion(self.w*inv_L, self.x*inv_L, self.y*inv_L, self.z*inv_L)

    def conjugate(self) -> "Quaternion":
        return Quaternion(self.w, -self.x, -self.y, -self.z)

    def inverse(self) -> "Quaternion":
        """For unit quaternions, inverse is the conjugate."""
        L2 = self.length_squared()
        if L2 < EPSILON:
            return Quaternion()
        inv_L2 = 1.0 / L2
        return Quaternion(self.w*inv_L2, -self.x*inv_L2, -self.y*inv_L2, -self.z*inv_L2)

    def dot(self, other: "Quaternion") -> float:
        return self.w*other.w + self.x*other.x + self.y*other.y + self.z*other.z

    @staticmethod
    def identity() -> "Quaternion":
        return Quaternion(1.0, 0.0, 0.0, 0.0)

    @staticmethod
    def from_axis_angle(axis: Vector3, angle: float) -> "Quaternion":
        half_angle = angle * 0.5
        s = math.sin(half_angle)
        n = axis.normalized()
        return Quaternion(math.cos(half_angle), n.x * s, n.y * s, n.z * s)

    @staticmethod
    def from_euler(pitch: float, yaw: float, roll: float) -> "Quaternion":
        """Creates quaternion from euler angles (radians)."""
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        
        return Quaternion(
            cr * cp * cy + sr * sp * sy,
            sr * cp * cy - cr * sp * sy,
            cr * sp * cy + sr * cp * sy,
            cr * cp * sy - sr * sp * cy
        )

    def to_matrix4x4(self) -> Matrix4x4:
        """Converts quaternion to a 4x4 rotation matrix."""
        w, x, y, z = self.w, self.x, self.y, self.z
        x2, y2, z2 = x+x, y+y, z+z
        xx, xy, xz = x*x2, x*y2, x*z2
        yy, yz, zz = y*y2, y*z2, z*z2
        wx, wy, wz = w*x2, w*y2, w*z2
        
        return Matrix4x4([
            [1.0 - (yy + zz), xy - wz,         xz + wy,         0.0],
            [xy + wz,         1.0 - (xx + zz), yz - wx,         0.0],
            [xz - wy,         yz + wx,         1.0 - (xx + yy), 0.0],
            [0.0,             0.0,             0.0,             1.0]
        ])

    def rotate_vector(self, v: Vector3) -> Vector3:
        """Rotates a 3D vector by this quaternion. Optimized form."""
        # Extract vector part
        qv = Vector3(self.x, self.y, self.z)
        # t = 2 * cross(qv, v)
        t = qv.cross(v) * 2.0
        # v' = v + w * t + cross(qv, t)
        return v + t * self.w + qv.cross(t)

    def slerp(self, other: "Quaternion", t: float) -> "Quaternion":
        """Spherical linear interpolation between two quaternions."""
        dot = self.dot(other)
        # Ensure shortest path
        if dot < 0.0:
            other = Quaternion(-other.w, -other.x, -other.y, -other.z)
            dot = -dot
            
        if dot > 0.9995:
            # Very close, use linear interpolation
            return Quaternion(
                self.w + (other.w - self.w) * t,
                self.x + (other.x - self.x) * t,
                self.y + (other.y - self.y) * t,
                self.z + (other.z - self.z) * t
            ).normalize()
            
        theta_0 = math.acos(dot)
        sin_theta_0 = math.sin(theta_0)
        theta = theta_0 * t
        sin_theta = math.sin(theta)
        
        s0 = math.cos(theta) - dot * sin_theta / sin_theta_0
        s1 = sin_theta / sin_theta_0
        
        return Quaternion(
            s0 * self.w + s1 * other.w,
            s0 * self.x + s1 * other.x,
            s0 * self.y + s1 * other.y,
            s0 * self.z + s1 * other.z
        )


# ===========================================================================
# SECTION 4.1 — Perlin Noise Generators
# ===========================================================================
class PerlinNoise3D:
    """
    Deterministic 3D value-gradient Perlin noise with seed control.
    Includes fractal Brownian motion (fBm), ridge, and domain warping capabilities.
    """
    def __init__(self, seed: int = 42) -> None:
        rng = random.Random(seed)
        perm = list(range(256))
        rng.shuffle(perm)
        self.p = perm + perm  # Extended permutation table
        
        self.gradients: List[Tuple[float, float, float]] = []
        g_rng = random.Random(seed + 1)
        for _ in range(256):
            # Uniformly distributed points on a unit sphere
            ang1 = g_rng.uniform(0.0, 2.0 * math.pi)
            ang2 = g_rng.uniform(0.0, math.pi)
            gx = math.sin(ang2) * math.cos(ang1)
            gy = math.sin(ang2) * math.sin(ang1)
            gz = math.cos(ang2)
            self.gradients.append((gx, gy, gz))

    def _fade(self, t: float) -> float:
        """Ken Perlin's fade function: 6t^5 - 15t^4 + 10t^3"""
        return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)

    def _lerp(self, a: float, b: float, t: float) -> float:
        return a + t * (b - a)

    def _grad_dot(self, hash_val: int, x: float, y: float, z: float) -> float:
        g = self.gradients[hash_val % 256]
        return g[0] * x + g[1] * y + g[2] * z

    def noise(self, x: float, y: float, z: float) -> float:
        """Raw 3D Perlin noise. Output approximately [-1, 1]."""
        X = int(math.floor(x)) & 255
        Y = int(math.floor(y)) & 255
        Z = int(math.floor(z)) & 255
        
        xf = x - math.floor(x)
        yf = y - math.floor(y)
        zf = z - math.floor(z)
        
        u = self._fade(xf)
        v = self._fade(yf)
        w = self._fade(zf)
        
        p = self.p
        A = p[X] + Y
        AA = p[A] + Z
        AB = p[A + 1] + Z
        B = p[X + 1] + Y
        BA = p[B] + Z
        BB = p[B + 1] + Z

        x0 = self._lerp(
            self._grad_dot(p[AA], xf, yf, zf),
            self._grad_dot(p[BA], xf - 1.0, yf, zf),
            u
        )
        x1 = self._lerp(
            self._grad_dot(p[AB], xf, yf - 1.0, zf),
            self._grad_dot(p[BB], xf - 1.0, yf - 1.0, zf),
            u
        )
        x2 = self._lerp(
            self._grad_dot(p[AA + 1], xf, yf, zf - 1.0),
            self._grad_dot(p[BA + 1], xf - 1.0, yf, zf - 1.0),
            u
        )
        x3 = self._lerp(
            self._grad_dot(p[AB + 1], xf, yf - 1.0, zf - 1.0),
            self._grad_dot(p[BB + 1], xf - 1.0, yf - 1.0, zf - 1.0),
            u
        )
        y0 = self._lerp(x0, x1, v)
        y1 = self._lerp(x2, x3, v)
        return self._lerp(y0, y1, w)

    def fbm(self, x: float, y: float, z: float,
            octaves: int = 5, persistence: float = 0.5,
            lacunarity: float = 2.0) -> float:
        """Fractal Brownian Motion. Accumulates octaves of noise.
        Output normalized to approximately [-1, 1]."""
        total = 0.0
        amplitude = 1.0
        frequency = 1.0
        max_amp = 0.0
        
        for _ in range(octaves):
            total += self.noise(x * frequency, y * frequency, z * frequency) * amplitude
            max_amp += amplitude
            amplitude *= persistence
            frequency *= lacunarity
            
        if max_amp < EPSILON:
            return 0.0
        return total / max_amp

    def ridge(self, x: float, y: float, z: float,
              octaves: int = 5, persistence: float = 0.5,
              lacunarity: float = 2.0) -> float:
        """Ridged multifractal noise. Creates sharp ridges like mountains."""
        total = 0.0
        amplitude = 1.0
        frequency = 1.0
        max_amp = 0.0
        
        for _ in range(octaves):
            n = 1.0 - abs(self.noise(x * frequency, y * frequency, z * frequency))
            n = n * n
            total += n * amplitude
            max_amp += amplitude
            amplitude *= persistence
            frequency *= lacunarity
            
        if max_amp < EPSILON:
            return 0.0
        return total / max_amp

    def domain_warp(self, x: float, y: float, z: float, 
                    warp_strength: float = 1.0, frequency: float = 1.0) -> float:
        """Applies domain warping to create swirling, organic patterns."""
        wx = x + self.noise(x, y, z) * warp_strength
        wy = y + self.noise(y, z, x) * warp_strength
        wz = z + self.noise(z, x, y) * warp_strength
        return self.fbm(wx * frequency, wy * frequency, wz * frequency)


# ===========================================================================
# SECTION 5.1 — Spline & Interpolation Math
# ===========================================================================

def catmull_rom(p0: Tuple[float, float], p1: Tuple[float, float],
                p2: Tuple[float, float], p3: Tuple[float, float],
                t: float) -> Tuple[float, float]:
    """Catmull-Rom spline interpolation for 2D points. t in [0,1]."""
    t2 = t * t
    t3 = t2 * t
    x = 0.5 * (
        (2.0 * p1[0]) +
        (-p0[0] + p2[0]) * t +
        (2.0 * p0[0] - 5.0 * p1[0] + 4.0 * p2[0] - p3[0]) * t2 +
        (-p0[0] + 3.0 * p1[0] - 3.0 * p2[0] + p3[0]) * t3
    )
    y = 0.5 * (
        (2.0 * p1[1]) +
        (-p0[1] + p2[1]) * t +
        (2.0 * p0[1] - 5.0 * p1[1] + 4.0 * p2[1] - p3[1]) * t2 +
        (-p0[1] + 3.0 * p1[1] - 3.0 * p2[1] + p3[1]) * t3
    )
    return (x, y)

def catmull_rom_3d(p0: Vector3, p1: Vector3, p2: Vector3, p3: Vector3, t: float) -> Vector3:
    """Catmull-Rom spline interpolation for 3D points. t in [0,1]."""
    t2 = t * t
    t3 = t2 * t
    x = 0.5 * (
        (2.0 * p1.x) +
        (-p0.x + p2.x) * t +
        (2.0 * p0.x - 5.0 * p1.x + 4.0 * p2.x - p3.x) * t2 +
        (-p0.x + 3.0 * p1.x - 3.0 * p2.x + p3.x) * t3
    )
    y = 0.5 * (
        (2.0 * p1.y) +
        (-p0.y + p2.y) * t +
        (2.0 * p0.y - 5.0 * p1.y + 4.0 * p2.y - p3.y) * t2 +
        (-p0.y + 3.0 * p1.y - 3.0 * p2.y + p3.y) * t3
    )
    z = 0.5 * (
        (2.0 * p1.z) +
        (-p0.z + p2.z) * t +
        (2.0 * p0.z - 5.0 * p1.z + 4.0 * p2.z - p3.z) * t2 +
        (-p0.z + 3.0 * p1.z - 3.0 * p2.z + p3.z) * t3
    )
    return Vector3(x, y, z)

def cubic_bezier(p0: Tuple[float, float], p1: Tuple[float, float],
                 p2: Tuple[float, float], p3: Tuple[float, float],
                 t: float) -> Tuple[float, float]:
    """Cubic Bezier curve interpolation. t in [0,1]."""
    u = 1.0 - t
    tt = t * t
    uu = u * u
    uuu = uu * u
    ttt = tt * t
    
    x = uuu * p0[0] + 3.0 * uu * t * p1[0] + 3.0 * u * tt * p2[0] + ttt * p3[0]
    y = uuu * p0[1] + 3.0 * uu * t * p1[1] + 3.0 * u * tt * p2[1] + ttt * p3[1]
    return (x, y)

def quadratic_bezier(p0: Tuple[float, float], p1: Tuple[float, float],
                     p2: Tuple[float, float], t: float) -> Tuple[float, float]:
    """Quadratic Bezier curve interpolation. t in [0,1]."""
    u = 1.0 - t
    tt = t * t
    uu = u * u
    
    x = uu * p0[0] + 2.0 * u * t * p1[0] + tt * p2[0]
    y = uu * p0[1] + 2.0 * u * t * p1[1] + tt * p2[1]
    return (x, y)

def hermite_interpolation(p0: float, p1: float, m0: float, m1: float, t: float) -> float:
    """Cubic Hermite spline interpolation for scalar values. t in [0,1]."""
    t2 = t * t
    t3 = t2 * t
    h00 = 2.0 * t3 - 3.0 * t2 + 1.0
    h10 = t3 - 2.0 * t2 + t
    h01 = -2.0 * t3 + 3.0 * t2
    h11 = t3 - t2
    return h00 * p0 + h10 * m0 + h01 * p1 + h11 * m1

# ===========================================================================
# SECTION 6.1 — Computational Geometry Intersections
# ===========================================================================

def ray_sphere_intersect(ray_origin: Vector3, ray_dir: Vector3, 
                         sphere_center: Vector3, sphere_radius: float) -> Optional[float]:
    """
    Ray-Sphere intersection using geometric solution.
    Returns the distance t to the nearest intersection point, or None if no hit.
    """
    oc = ray_origin - sphere_center
    a = ray_dir.dot(ray_dir)
    b = 2.0 * oc.dot(ray_dir)
    c = oc.dot(oc) - sphere_radius * sphere_radius
    
    discriminant = b*b - 4.0*a*c
    if discriminant < 0.0:
        return None
        
    sqrt_disc = math.sqrt(discriminant)
    t0 = (-b - sqrt_disc) / (2.0 * a)
    t1 = (-b + sqrt_disc) / (2.0 * a)
    
    if t0 > t1:
        t0, t1 = t1, t0
        
    if t1 < EPSILON:
        return None  # Both intersections behind ray
        
    if t0 < EPSILON:
        return t1  # Ray origin inside sphere
        
    return t0

def ray_aabb_intersect(ray_origin: Vector3, ray_dir: Vector3, 
                       box_min: Vector3, box_max: Vector3) -> Optional[Tuple[float, float]]:
    """
    Ray-Axis-Aligned-Bounding-Box intersection using the Slab method.
    Returns a tuple (t_min, t_max) of intersection distances, or None.
    """
    t_min = -math.inf
    t_max = math.inf
    
    for i in range(3):
        d = ray_dir[i]
        o = ray_origin[i]
        min_b = box_min[i]
        max_b = box_max[i]
        
        if abs(d) < EPSILON:
            # Ray is parallel to slab. No hit if origin not inside slab
            if o < min_b or o > max_b:
                return None
        else:
            inv_d = 1.0 / d
            t1 = (min_b - o) * inv_d
            t2 = (max_b - o) * inv_d
            
            if t1 > t2:
                t1, t2 = t2, t1
                
            t_min = max(t_min, t1)
            t_max = min(t_max, t2)
            
            if t_min > t_max:
                return None
                
    if t_max < EPSILON:
        return None  # Box behind ray
        
    return (t_min, t_max)

def ray_triangle_intersect(ray_origin: Vector3, ray_dir: Vector3,
                           v0: Vector3, v1: Vector3, v2: Vector3,
                           cull_backfaces: bool = False) -> Optional[float]:
    """
    Ray-Triangle intersection using the Möller–Trumbore algorithm.
    Returns distance t to intersection, or None.
    """
    edge1 = v1 - v0
    edge2 = v2 - v0
    h = ray_dir.cross(edge2)
    a = edge1.dot(h)
    
    if cull_backfaces:
        if a < EPSILON:
            return None
    else:
        if abs(a) < EPSILON:
            return None  # Ray parallel to triangle
            
    f = 1.0 / a
    s = ray_origin - v0
    u = f * s.dot(h)
    
    if u < 0.0 or u > 1.0:
        return None
        
    q = s.cross(edge1)
    v = f * ray_dir.dot(q)
    
    if v < 0.0 or (u + v) > 1.0:
        return None
        
    t = f * edge2.dot(q)
    if t > EPSILON:
        return t
        
    return None

def point_in_triangle(p: Vector3, v0: Vector3, v1: Vector3, v2: Vector3) -> bool:
    """Checks if a coplanar point lies inside a triangle using barycentric coordinates."""
    v0v1 = v1 - v0
    v0v2 = v2 - v0
    v0p = p - v0
    
    dot00 = v0v2.dot(v0v2)
    dot01 = v0v2.dot(v0v1)
    dot02 = v0v2.dot(v0p)
    dot11 = v0v1.dot(v0v1)
    dot12 = v0v1.dot(v0p)
    
    inv_denom = 1.0 / (dot00 * dot11 - dot01 * dot01)
    u = (dot11 * dot02 - dot01 * dot12) * inv_denom
    v = (dot00 * dot12 - dot01 * dot02) * inv_denom
    
    return (u >= 0.0) and (v >= 0.0) and (u + v < 1.0)

def closest_point_on_line_segment(p: Vector3, a: Vector3, b: Vector3) -> Vector3:
    """Finds the closest point on a line segment AB to point P."""
    ab = b - a
    t = p.distance_to(a) / ab.length() if ab.length() > EPSILON else 0.0
    # Actually, let's project correctly:
    ap = p - a
    t = ap.dot(ab) / ab.length_squared()
    t = clamp(t, 0.0, 1.0)
    return a + ab * t

def sphere_sphere_intersect(c1: Vector3, r1: float, c2: Vector3, r2: float) -> bool:
    """Checks if two spheres intersect."""
    dist_sq = c1.distance_squared_to(c2)
    rad_sum = r1 + r2
    return dist_sq <= (rad_sum * rad_sum)

def aabb_aabb_intersect(min1: Vector3, max1: Vector3, min2: Vector3, max2: Vector3) -> bool:
    """Checks if two Axis-Aligned Bounding Boxes intersect."""
    return (min1.x <= max2.x and max1.x >= min2.x and
            min1.y <= max2.y and max1.y >= min2.y and
            min1.z <= max2.z and max1.z >= min2.z)

# ===========================================================================
# SECTION 7.1 — Trigonometry & Angle Utilities
# ===========================================================================

def fast_sin(x: float) -> float:
    """A fast approximation of sine using a parabola. Input in radians.
    Accurate within ~0.0015. Highly optimized for tight loops."""
    # Always wrap input angle to -PI..PI
    if x < -PI or x > PI:
        x = x - (TAU * math.floor((x + PI) / TAU))
    
    if x < 0:
        return 1.27323954 * x + 0.405284735 * x * x
    else:
        return 1.27323954 * x - 0.405284735 * x * x

def fast_cos(x: float) -> float:
    """A fast approximation of cosine. Input in radians."""
    # cos(x) = sin(x + PI/2)
    x += HALF_PI
    if x > PI:
        x -= TAU
    return fast_sin(x)

def atan2_approx(y: float, x: float) -> float:
    """Fast approximation of atan2. Error < 0.005 radians."""
    if x == 0.0:
        if y > 0.0: return HALF_PI
        if y < 0.0: return -HALF_PI
        return 0.0
        
    z = abs(y) / abs(x)
    if z < 1.0:
        atan = z / (1.0 + 0.28 * z * z)
        if x < 0.0:
            atan = PI - atan if y >= 0.0 else -PI - atan
        else:
            atan = -atan if y < 0.0 else atan
        return atan
    else:
        atan = HALF_PI - z / (z * z + 0.28)
        if x < 0.0:
            atan = PI - atan if y >= 0.0 else -PI - atan
        else:
            atan = -atan if y < 0.0 else atan
        return atan

def normalize_angle(angle: float) -> float:
    """Normalizes an angle to the range [-PI, PI]."""
    return angle - (TAU * math.floor((angle + PI) / TAU))

def angle_difference(a: float, b: float) -> float:
    """Finds the shortest signed angle difference between two angles."""
    diff = normalize_angle(b - a)
    return diff

def shortest_angular_path(current: float, target: float, max_step: float) -> float:
    """Moves `current` towards `target` by at most `max_step`, taking shortest path."""
    diff = angle_difference(current, target)
    if abs(diff) <= max_step:
        return target
    return current + math.copysign(max_step, diff)