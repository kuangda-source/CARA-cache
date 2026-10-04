"""Explicit complete sampling interventions for the two-CAL fair comparison."""
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class Workpoint:
    name: str
    mode: str
    requested_steps: int
    threshold: object = None

    def to_dict(self):
        return asdict(self)


FAIR_WORKPOINTS = (
    Workpoint('native35', 'native', 35),
    Workpoint('native23', 'native', 23),
    Workpoint('wc004', 'worldcache', 35, .04),
    Workpoint('wc006', 'worldcache', 35, .06),
    Workpoint('wc008', 'worldcache', 35, .08),
    Workpoint('stage_every1', 'stage', 35, .06),
)


def validate_workpoints(points):
    if (type(points) is not tuple or len(points) != 6
            or any(type(p) is not Workpoint or type(p.requested_steps) is not int
                   for p in points)
            or any(p.threshold is not None and type(p.threshold) is not float for p in points)
            or points != FAIR_WORKPOINTS):
        raise ValueError('Six explicit Native35/23, WC004/006/008, stage workpoints required')
    return points
