from dotenv import load_dotenv
load_dotenv()

import base64
import json
import os
import requests
import zlib

from functools import lru_cache
from typing import Any

USDA_API_KEY = os.getenv('UDSA_API_KEY')
SEARCH_API_URL = 'https://api.nal.usda.gov/fdc/v1/foods/search'
TOP_N_NUTRIENTS = 10

NUTRIENT_NAME_KEY = 'nutrientName'
VALUE_KEY = 'value'
UNIT_NAME_KEY = 'unitName'

UTF8_ENCODING = 'utf-8'

def get_nutrient_data(food: str) -> dict[str, list[dict[str, str | int | float]]] | None:
    """
    Gets the top 10 nutrients for a food by weight.

    Args:
        food (str): The name of the food.

    Returns:
        dict[str, list[dict[str, str | int | float]]] | None:
            A dictionary with key 'food' (str) and value set to a list of dictionaries, each representing a nutrient
                                                   with the following keys:
                                                   - 'nutrientName' (str)
                                                   - 'value' (int or float)
                                                   - 'unitName' (str)
                                                   Returns `None` if the food is not found.
    """
    compressed_data_base64 = _get_nutrient_data_compressed(food)
    if compressed_data_base64 is None:
        return None
    compressed_data = base64.b64decode(compressed_data_base64)
    food_nutrients = json.loads(zlib.decompress(compressed_data).decode(UTF8_ENCODING))
    return food_nutrients

@lru_cache(maxsize=None)
def _get_nutrient_data_compressed(food: str) -> str:
    """
    See the documentation for `get_nutrient_data`. This function simply compresses the nutrient data for caching in memory.

    Args:
        food (str): The name of the food.

    Returns:
        (str) The compressed nutrient data for the food, base64-encoded.
    """

    params = {
        'query': food,
        'dataType': 'Foundation,SR Legacy',
        'sortBy': 'dataType.keyword',
        'sortOrder': 'asc',
        'pageSize': 200, # max
        'pageNumber': 0, # first page
        'api_key': USDA_API_KEY
    }

    response = requests.get(SEARCH_API_URL, params=params, headers={'accept': 'application/json'})

    if response.status_code != 200:
        print(f'Error getting nutrient data for [{food}]: {response.status_code} {response.text}')
        return None

    data: dict[str, Any] = response.json()

    # get best food match by "score"
    best_match: dict[str, Any] | None = max(data['foods'], key=lambda food: food['score'], default=None)
    if best_match is None:
        print(f'Food [{food}] not found')
        return None

    # get top N nutrients by weight
    top_nutrients = sorted(best_match['foodNutrients'], key=lambda n: _get_nutrient_weight(n), reverse=True)[:TOP_N_NUTRIENTS]

    # keep only nutrient name, value, and unit
    top_nutrients = [{k: n[k] if k != UNIT_NAME_KEY else n[k].lower() for k in (NUTRIENT_NAME_KEY, VALUE_KEY, UNIT_NAME_KEY)} for n in top_nutrients]

    # nutrients may be duplicated for different weight representations (e.g. 408 KCAL vs. 1710.0 kJ), so dedupe by using lowest value
    unique_nutrients: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for nutrient in top_nutrients:
        name = nutrient[NUTRIENT_NAME_KEY]
        if name not in seen_names:
            unique_nutrients.append(nutrient)
            seen_names.add(name)
        else:
            # find existing nutrient with same name
            existing_index = [i for i, n in enumerate(unique_nutrients) if n[NUTRIENT_NAME_KEY] == name][0]
            # replace if current nutrient has a lower value
            if nutrient[VALUE_KEY] < unique_nutrients[existing_index][VALUE_KEY]:
                unique_nutrients[existing_index] = nutrient

    print(f'[{food}] top {TOP_N_NUTRIENTS} nutrients: {unique_nutrients}')
    food_nutrients = {'food': food, 'nutrients': unique_nutrients}

    compressed_data = zlib.compress(bytes(json.dumps(food_nutrients), UTF8_ENCODING))
    return base64.b64encode(compressed_data).decode(UTF8_ENCODING)

def _get_nutrient_weight(nutrient: dict[str, Any]) -> float:
    if not VALUE_KEY in nutrient:
        return 0.0
    unit_prefix: str = nutrient[UNIT_NAME_KEY][0]
    match unit_prefix.lower():
        case 'm':
            return nutrient[VALUE_KEY] * 1e-3
        case 'u':
            return nutrient[VALUE_KEY] * 1e-6
        case 'k':
            return nutrient[VALUE_KEY] * 1e3
        case _:
            return nutrient[VALUE_KEY]
