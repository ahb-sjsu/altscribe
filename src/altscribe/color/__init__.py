"""Color analysis subsystem — contrast, CVD simulation, palette suggestions."""

from altscribe.color.colorblind import CVDType, simulate_cvd
from altscribe.color.contrast import ContrastResult, check_contrast, contrast_ratio

__all__ = [
    "CVDType",
    "ContrastResult",
    "check_contrast",
    "contrast_ratio",
    "simulate_cvd",
]
