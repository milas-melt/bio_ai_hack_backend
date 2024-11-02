import json
import enum
import math
from typing import Optional, Iterable

with open("bio_ai_hack_backend/faers_ozempic_24Q3.json", "r") as file:
    _DATA = json.load(file)


class Sex(enum.StrEnum):
    MALE = "M"
    FEMALE = "F"


def select_on_age(age: int, cases: Optional[Iterable] = None):
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
        if got_age == age:
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


def select_on_weight(weight: int, cases: Optional[Iterable] = None):
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
        if weight == int(got_weight_in_kg):
            matches.append(case)
    return matches


if __name__ == "__main__":
    select_on_age(83)
    select_on_sex(Sex.MALE)
    select_on_weight(10)
