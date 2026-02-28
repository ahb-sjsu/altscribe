"""Color vision deficiency simulation — Vienot 1999 matrices, pure Python."""

from __future__ import annotations

from enum import Enum

from altscribe.color.contrast import _linearize


class CVDType(Enum):
    """Color vision deficiency types."""

    PROTANOPIA = "protanopia"
    DEUTERANOPIA = "deuteranopia"
    TRITANOPIA = "tritanopia"


# Vienot 1999 simulation matrices (operate on linearized sRGB).
# Each is a 3x3 matrix stored as tuple of 3 rows.
_CVD_MATRICES: dict[CVDType, tuple[tuple[float, ...], ...]] = {
    CVDType.PROTANOPIA: (
        (0.56667, 0.43333, 0.0),
        (0.55833, 0.44167, 0.0),
        (0.0, 0.24167, 0.75833),
    ),
    CVDType.DEUTERANOPIA: (
        (0.62500, 0.37500, 0.0),
        (0.70000, 0.30000, 0.0),
        (0.0, 0.30000, 0.70000),
    ),
    CVDType.TRITANOPIA: (
        (0.95000, 0.05000, 0.0),
        (0.0, 0.43333, 0.56667),
        (0.0, 0.47500, 0.52500),
    ),
}


def _to_linear(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    return (_linearize(rgb[0]), _linearize(rgb[1]), _linearize(rgb[2]))


def _to_srgb(val: float) -> int:
    """Convert linear RGB channel back to sRGB 0-255."""
    val = max(0.0, min(1.0, val))
    s = val * 12.92 if val <= 0.0031308 else 1.055 * (val ** (1.0 / 2.4)) - 0.055
    return max(0, min(255, round(s * 255)))


def _mat_mul(
    matrix: tuple[tuple[float, ...], ...],
    vec: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Multiply 3x3 matrix by 3-vector."""
    return (
        matrix[0][0] * vec[0] + matrix[0][1] * vec[1] + matrix[0][2] * vec[2],
        matrix[1][0] * vec[0] + matrix[1][1] * vec[1] + matrix[1][2] * vec[2],
        matrix[2][0] * vec[0] + matrix[2][1] * vec[1] + matrix[2][2] * vec[2],
    )


def simulate_cvd(rgb: tuple[int, int, int], cvd_type: CVDType) -> tuple[int, int, int]:
    """Simulate how a color appears under a given color vision deficiency.

    Parameters
    ----------
    rgb : (R, G, B) with values 0-255
    cvd_type : which deficiency to simulate

    Returns
    -------
    Simulated (R, G, B) as seen by a person with the given CVD.
    """
    linear = _to_linear(rgb)
    matrix = _CVD_MATRICES[cvd_type]
    sim = _mat_mul(matrix, linear)
    return (_to_srgb(sim[0]), _to_srgb(sim[1]), _to_srgb(sim[2]))


def colors_distinguishable(
    color1: tuple[int, int, int],
    color2: tuple[int, int, int],
    cvd_type: CVDType,
    min_ratio: float = 1.5,
) -> bool:
    """Check if two colors remain distinguishable under CVD simulation."""
    from altscribe.color.contrast import contrast_ratio

    sim1 = simulate_cvd(color1, cvd_type)
    sim2 = simulate_cvd(color2, cvd_type)
    return contrast_ratio(sim1, sim2) >= min_ratio
