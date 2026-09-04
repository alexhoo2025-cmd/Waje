"""Synthetic cohort fixture; contains no production data."""

def retention(numerator, denominator):
    if denominator is None or denominator == 0:
        return None
    if numerator < 0 or denominator < 0:
        raise ValueError("numerator and denominator must be non-negative")
    if numerator > denominator:
        raise ValueError("numerator cannot exceed denominator")
    return numerator / denominator
