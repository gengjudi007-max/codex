from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional


@dataclass
class StandardLandRecord:
    city: str
    title: str
    district: Optional[str] = None
    land_use: Optional[str] = None
    buyer: Optional[str] = None
    date: Optional[str] = None

    land_area: Optional[float] = None
    planned_gfa: Optional[float] = None
    land_amount: Optional[float] = None
    floor_price: Optional[float] = None
    premium_rate: Optional[float] = None

    source: Optional[str] = None
    source_level: Optional[str] = None
    url: Optional[str] = None

    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


METRIC_FIELD_ALIASES = {
    "land_area": ["tdmj", "ydmj", "landArea", "area"],
    "planned_gfa": ["jzmj", "ghjzmj", "buildingArea", "gfa"],
    "land_amount": ["cjj", "cjje", "price", "amount", "dealPrice"],
    "floor_price": ["floorPrice", "loudijia", "cjlmj"],
    "premium_rate": ["premiumRate", "yjl", "premium"],
}
