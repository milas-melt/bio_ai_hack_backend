import operator
import json
import enum
import math
from typing import Optional, Iterable
import config


with open("bio_ai_hack_backend/faers_ozempic_24Q3.json", "r") as file:
    _DATA = json.load(file)


class Sex(enum.StrEnum):
    MALE = "M"
    FEMALE = "F"


def select_age_bucket(age: int) -> tuple[int, int]:
    increment = 10
    for start_age in range(0, 500, 10):
        end_age = start_age + increment
        if start_age <= age < end_age:
            return (start_age, end_age)
    raise RuntimeError("what")


def select_weight_bucket(weight: float) -> tuple[float, float]:
    increment = 10
    for start_weight in range(0, 1000, 10):
        end_weight = start_weight + increment
        if start_weight <= weight < end_weight:
            return (start_weight, end_weight)
    raise RuntimeError("what")


def select_on_age(
    min_age: int, max_age_exclusive: int, cases: Optional[Iterable] = None
):
    if cases is None:
        cases = _DATA["cases"]
    matches = []
    for case in cases:
        demographic_info = case["demographic_info"]
        got_age_in_units = demographic_info["age"]
        if isinstance(got_age_in_units, float):
            pass
        elif isinstance(got_age_in_units, str):
            got_age_in_units = int(demographic_info["age"])
        else:
            raise ValueError("todo")
        got_age_unit = demographic_info["age_cod"]
        if math.isnan(got_age_in_units) or (
            not isinstance(got_age_unit, str) and math.isnan(got_age_unit)
        ):
            continue
        elif got_age_unit == "DEC":
            got_age = got_age_in_units * 10
        elif got_age_unit == "YR":
            got_age = got_age_in_units
        elif got_age_unit == "MON":
            got_age = got_age_in_units / 12
        elif got_age_unit == "WK":
            got_age = got_age_in_units / 52
        elif got_age_unit == "DY":
            got_age = got_age_in_units / 365
        elif got_age_unit == "HR":
            got_age = got_age_in_units / 24
        else:
            raise NotImplementedError("!!!")
        if min_age <= got_age < max_age_exclusive:
            matches.append(case)
    return matches


def select_on_sex(sex: str, cases: Optional[Iterable] = None):
    sex = sex.upper()
    if cases is None:
        cases = _DATA["cases"]
    matches = []
    for case in cases:
        demographic_info = case["demographic_info"]
        got_sex = demographic_info["sex"]
        if got_sex == sex:
            matches.append(case)
    return matches


def select_on_weight(
    min_weight: float, max_weight_exclusive: float, cases: Optional[Iterable] = None
):
    if cases is None:
        cases = _DATA["cases"]
    matches = []
    for case in cases:
        demographic_info = case["demographic_info"]
        got_weight_in_units = demographic_info["wt"]
        weight_code = demographic_info["wt_cod"]
        if (
            isinstance(got_weight_in_units, float) and math.isnan(got_weight_in_units)
        ) or (isinstance(weight_code, float) and math.isnan(weight_code)):
            continue
        elif weight_code == "KG":
            got_weight_in_kg = float(got_weight_in_units)
        elif weight_code == "LBS":
            got_weight_in_kg = float(got_weight_in_units) * 0.453592
        elif weight_code == "GMS":
            got_weight_in_kg = float(got_weight_in_units) * 100.0
        else:
            raise ValueError("Unknown bro")
        if min_weight <= int(got_weight_in_kg) < max_weight_exclusive:
            matches.append(case)
    return matches


def extract_reactions(cases: Iterable[dict]) -> dict[str, int]:
    reactions: dict[str, int] = {}
    for case in cases:
        for reaction in case["reactions"]:
            reaction_description = reaction["pt"]
            if reaction_description in reactions:
                reactions[reaction_description] += 1
            else:
                reactions[reaction_description] = 1
    return reactions


def proportionalize(counter: dict[str, float]) -> dict[str, float]:
    denominator = sum(counter.values())
    return {key: value / denominator for key, value in counter.items()}


def top_k(
    counter: dict[str, float], k: Optional[int] = None
) -> list[tuple[str, float]]:
    if k is None:
        k = config.N_REACTIONS
    sorted_items = sorted(counter.items(), reverse=True, key=operator.itemgetter(1))
    top_items = sorted_items[:k]
    return top_items


if __name__ == "__main__":
    select_on_age(60, 70)
    select_on_sex(Sex.MALE)
    select_on_weight(10)
