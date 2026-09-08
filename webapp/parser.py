import re
from pathlib import Path
from typing import List, Optional
from openpyxl import load_workbook
from .models import ContractData, Condition, RoomBlock
from .rules import normalize_spaces, parse_people, parse_age_values, ROOM_BLACKLIST


MEAL_KEYWORDS = [
    "ULTRA ALL INCLUSIVE", "ALL INCLUSIVE", "BED AND BREAKFAST",
    "HALF BOARD", "FULL BOARD", "ROOM ONLY"
]


def _string(v):
    return normalize_spaces(v) if v is not None else ""


def _numeric_prices(row_values):
    prices = []
    for v in row_values[2:16]:
        if isinstance(v, (int, float)):
            prices.append(float(v))
    return prices


def _looks_like_meal_currency(text: str):
    up = text.upper()
    return any(k in up for k in MEAL_KEYWORDS) and "/" in up


def _extract_meal_currency(text: str):
    parts = [normalize_spaces(x) for x in text.split("/") if normalize_spaces(x)]
    currency = ""
    meals = []
    for p in parts:
        up = p.upper()
        if up in {"EUR", "USD", "GBP", "TRY"}:
            currency = up
        elif any(k == up for k in MEAL_KEYWORDS):
            meals.append(up)
    return meals, currency


def _looks_like_room_name(text: str):
    up = text.upper()
    if not up or up in ROOM_BLACKLIST:
        return False
    if _looks_like_meal_currency(text):
        return False
    if "P.P.P.D" in up:
        return False
    if parse_people(text) != (None, None):
        return False
    if "CHD" in up:
        return False
    if any(k in up for k in ["EARLY BOOK", "RELEASE", "ALLOTMENT", "MINIMUM STAY"]):
        return False
    return any(k in up for k in [
        "ROOM", "SUITE", "BUNGALOW", "VILLA", "HOUSE", "DUPLEX", "DUBLEX"
    ])


def parse_contract(path: str) -> ContractData:
    wb = load_workbook(path, data_only=True)

    # Prefer the first non-Index/non-x sheet.
    candidates = [s for s in wb.sheetnames if s.lower() not in {"index", "x"}]
    ws = wb[candidates[0] if candidates else wb.sheetnames[0]]

    hotel_name = ""
    category = None
    city = ""
    adult_only = False

    for r in range(1, min(ws.max_row, 15) + 1):
        text = _string(ws.cell(r, 2).value)
        if not text:
            continue
        up = text.upper()
        if "/" in text and ("*" in text or "ADULT ONLY" in up or "FETHIYE" in up or "MARMARIS" in up or "ANTALYA" in up):
            parts = [normalize_spaces(x) for x in text.split("/")]
            hotel_name = parts[0]
            if "ADULT ONLY" in up:
                adult_only = True
            m = re.search(r"(\d)\s*\*", text)
            if m:
                category = int(m.group(1))
            if len(parts) >= 3:
                city = parts[-1].title()
            break

    if not hotel_name and "Index" in wb.sheetnames:
        idx = wb["Index"]
        hotel_name = _string(idx["B4"].value)
        adult_only = "ADULT ONLY" in hotel_name.upper()

    meal_plans = []
    currency = ""

    rooms: List[RoomBlock] = []
    current: Optional[RoomBlock] = None
    max_age = None
    baby_age = None

    for r in range(1, ws.max_row + 1):
        label = _string(ws.cell(r, 2).value)
        if not label:
            continue

        if _looks_like_meal_currency(label):
            meals, cur = _extract_meal_currency(label)
            for meal in meals:
                if meal not in meal_plans:
                    meal_plans.append(meal)
            if cur:
                currency = cur
            continue

        if _looks_like_room_name(label):
            current = RoomBlock(name=label, pricing_type="TOTAL", conditions=[])
            rooms.append(current)
            continue

        if current is None:
            continue

        if "P.P.P.D" in label.upper():
            current.pricing_type = "PP"
            continue

        adults, children = parse_people(label)
        if adults is not None:
            prices = _numeric_prices([ws.cell(r, c).value for c in range(1, ws.max_column + 1)])
            current.conditions.append(
                Condition(label=label, adults=adults, children=children or 0, prices=prices)
            )

            for age in parse_age_values(label):
                try:
                    n = float(age.replace(",", "."))
                    if max_age is None or n > max_age:
                        max_age = n
                    # Infant/baby threshold inferred from the smallest upper-bound <= 2.99.
                    if n <= 2.99 and (baby_age is None or n > baby_age):
                        baby_age = n
                except Exception:
                    pass

    # Deduplicate accidental repeated room blocks with no conditions.
    rooms = [r for r in rooms if r.conditions]

    def fmt_age(n):
        if n is None:
            return ""
        text = f"{n:.2f}".rstrip("0").rstrip(".")
        return text.replace(".", ",")

    return ContractData(
        hotel_name=hotel_name or ws.title,
        city=city,
        category=category,
        adult_only=adult_only,
        currency=currency,
        meal_plans=meal_plans,
        baby_age="" if adult_only else fmt_age(baby_age),
        child1_age="" if adult_only else fmt_age(max_age),
        child2_age="" if adult_only else fmt_age(max_age),
        rooms=rooms,
    )
