from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Condition:
    label: str
    adults: Optional[int] = None
    children: Optional[int] = None
    prices: List[float] = field(default_factory=list)


@dataclass
class RoomBlock:
    name: str
    pricing_type: str = "TOTAL"  # PP or TOTAL
    conditions: List[Condition] = field(default_factory=list)


@dataclass
class ContractData:
    hotel_name: str
    city: str = ""
    country: str = "Turkey"
    address: str = ""
    website: str = ""
    latitude: str = ""
    longitude: str = ""
    category: Optional[int] = None
    adult_only: bool = False
    currency: str = ""
    meal_plans: List[str] = field(default_factory=list)
    baby_age: str = ""
    child1_age: str = ""
    child2_age: str = ""
    rooms: List[RoomBlock] = field(default_factory=list)
