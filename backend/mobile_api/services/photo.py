from dataclasses import dataclass


@dataclass
class PhotoSummary:
    quality_score: float
    color_index: float
    notes: str


def run_photo_analysis(field_image) -> PhotoSummary:
    """MVP example: keep as field verification layer, not replacement for Sentinel-2."""
    quality_score = 0.8
    color_index = 0.55
    return PhotoSummary(
        quality_score=quality_score,
        color_index=color_index,
        notes='Field verification metrics only. Satellite indices remain the primary analytic source.',
    )
