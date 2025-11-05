from mathutils import Vector
def canonicalize_normal(n: Vector) -> Vector:
    """
    Return a unit-length Vector with a canonical orientation.

    This function normalizes the input vector and flips its sign when necessary so
    that the component with the largest absolute value is non-negative. The result
    is a deterministic, unit-length vector useful for comparing or hashing normals
    and for producing a unique orientation for colinear vectors.

    Parameters
    ----------
    n : Vector
        Input vector. Expected to expose numeric attributes x, y, z and a
        normalized() method that returns a unit-length Vector (or otherwise
        supports normalization). The function assumes normalized() will raise an
        error for the zero vector if it cannot be normalized.

    Returns
    -------
    Vector
        A unit-length Vector with the same direction as `n` (up to sign) but with
        the dominant component (largest absolute value) non-negative.

    Raises
    ------
    ValueError
        If `n` is the zero vector and cannot be normalized (behavior depends on
        the Vector.normalized() implementation).

    Notes
    -----
    - If two or more components tie for largest absolute value, the tie is broken
      by the order (x, then y, then z) because max chooses the first occurrence.
    - The original vector is not modified if normalized() returns a new instance;
      behavior depends on the Vector implementation.
    - Intended for canonicalizing face normals in geometric algorithms.
    """
    n = n.normalized() #
    abs_vals = [abs(n.x), abs(n.y), abs(n.z)]
    idx = abs_vals.index(max(abs_vals))
    if (idx == 0 and n.x < 0) or (idx == 1 and n.y < 0) or (idx == 2 and n.z < 0):
        return -n
    return n