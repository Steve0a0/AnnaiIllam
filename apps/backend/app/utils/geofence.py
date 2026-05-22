"""Geofence utilities — pure-Python, no external dependencies."""

import math


def haversine_distance_meters(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Return the great-circle distance in metres between two GPS coordinates.

    Uses the Haversine formula. Accurate to within ~0.5% for distances up to
    a few hundred kilometres — more than sufficient for job-site geofencing.

    Args:
        lat1, lon1: Job-site latitude/longitude in decimal degrees.
        lat2, lon2: Worker latitude/longitude in decimal degrees.

    Returns:
        Distance in metres (float).
    """
    earth_radius_m = 6_371_000.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return earth_radius_m * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
