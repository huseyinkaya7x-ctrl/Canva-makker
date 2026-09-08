import re
from collections import defaultdict
from typing import List, Tuple
from .models import Condition, RoomBlock


ROOM_BLACKLIST = {
    "RELEASE DAYS", "MINIMUM STAY", "ALLOTMENT", "EARLY BOOKINGS",
    "DAY OF WEEK", "DAY", "BEGIN DATE", "END DATE", "ROOM TYPE"
}


def normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def parse_people(label: str):
    text = normalize_spaces(label).upper()

    if "P.P.P.D" in text or "P.P." in text:
        return None, None

    if "DOUBLE ROOM+EXTRA BED" in text or "DOUBLE ROOM + EXTRA BED" in text:
        return 3, 0
    if text == "DOUBLE ROOM":
        return 2, 0
    if text == "SINGLE ROOM":
        return 1, 0

    m = re.match(r"^(\d+)\s+ADULTS?$", text)
    if m:
        return int(m.group(1)), 0

    m = re.match(r"^(\d+)\s*\+\s*(\d+)\s*CHD", text)
    if m:
        return int(m.group(1)), int(m.group(2))

    return None, None


def parse_age_values(label: str) -> List[str]:
    # Extract upper bounds from patterns such as (0-11,99), (3-11,99), (0-2,99)
    values = re.findall(r"\(\s*\d+(?:[,.]\d+)?\s*-\s*(\d+(?:[,.]\d+)?)\s*\)", str(label or ""))
    return [v.replace(".", ",") for v in values]


def max_occupancy(conditions: List[Condition]) -> int:
    vals = []
    for c in conditions:
        if c.adults is not None and c.children is not None:
            vals.append(c.adults + c.children)
    return max(vals) if vals else 0


def max_children(conditions: List[Condition], adult_filter=None) -> int:
    vals = []
    for c in conditions:
        if c.children is None:
            continue
        if adult_filter is None or c.adults in adult_filter:
            vals.append(c.children)
    return max(vals) if vals else 0


def adult_values(conditions: List[Condition]) -> List[int]:
    return sorted({c.adults for c in conditions if c.adults is not None})


def has_single_condition(room: RoomBlock) -> bool:
    return any(normalize_spaces(c.label).upper() == "SINGLE ROOM" for c in room.conditions)


def _price_signature(cond: Condition):
    # Round floats so insignificant Excel floating-point noise does not create splits.
    return tuple(round(float(x), 4) for x in cond.prices if isinstance(x, (int, float)))


def split_total_room_by_price(room: RoomBlock):
    """
    Split TOTAL-price rooms only when base adult prices differ.
    Example:
      1/2/3 AD = same price
      4 AD = different price
    -> 1-3 ADU and 4 ADU.
    Child-only price differences do NOT drive this grouping.
    """
    adult_base = {}
    for c in room.conditions:
        if c.adults is None or c.children != 0:
            continue
        sig = _price_signature(c)
        if sig:
            adult_base[c.adults] = sig

    if len(adult_base) <= 1:
        return [room]

    groups = []
    current = []
    last_sig = None
    for adu in sorted(adult_base):
        sig = adult_base[adu]
        if last_sig is None or sig == last_sig:
            current.append(adu)
        else:
            groups.append(current)
            current = [adu]
        last_sig = sig
    if current:
        groups.append(current)

    if len(groups) == 1:
        return [room]

    out = []
    for group in groups:
        cloned = RoomBlock(name=room.name, pricing_type=room.pricing_type, conditions=[])
        allowed = set(group)
        # Keep child conditions that belong to the adult counts represented in this group.
        cloned.conditions = [
            c for c in room.conditions
            if c.adults in allowed
        ]
        lo, hi = min(group), max(group)
        cloned.name = f"{room.name} {lo} ADU" if lo == hi else f"{room.name} {lo}-{hi} ADU"
        out.append(cloned)
    return out


def canvas_rows(room: RoomBlock, adult_only: bool):
    """
    Returns dict rows:
    name, min_adults, max_adults, min_children, max_children, max_occupancy
    """
    if adult_only:
        adults = adult_values(room.conditions)
        if not adults:
            adults = [1, 2]
        return [{
            "name": room.name,
            "min_adults": min(adults),
            "max_adults": max(adults),
            "min_children": 0,
            "max_children": 0,
            "max_occupancy": max(adults),
        }]

    if room.pricing_type == "PP" and has_single_condition(room):
        single_conds = [c for c in room.conditions if c.adults == 1]
        multi_conds = [c for c in room.conditions if c.adults is not None and c.adults >= 2]

        result = []
        if single_conds:
            result.append({
                "name": f"SINGLE {room.name}",
                "min_adults": 1,
                "max_adults": 1,
                "min_children": 0,
                "max_children": max_children(single_conds),
                "max_occupancy": max_occupancy(single_conds),
            })
        if multi_conds:
            ads = adult_values(multi_conds)
            result.append({
                "name": room.name,
                "min_adults": min(ads),
                "max_adults": max(ads),
                "min_children": 0,
                "max_children": max_children(multi_conds),
                "max_occupancy": max_occupancy(multi_conds),
            })
        return result

    result = []
    for split_room in split_total_room_by_price(room) if room.pricing_type == "TOTAL" else [room]:
        ads = adult_values(split_room.conditions)
        if not ads:
            continue
        result.append({
            "name": split_room.name,
            "min_adults": min(ads),
            "max_adults": max(ads),
            "min_children": 0,
            "max_children": max_children(split_room.conditions),
            "max_occupancy": max_occupancy(split_room.conditions),
        })
    return result
