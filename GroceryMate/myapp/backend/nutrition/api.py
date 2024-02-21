import json

import requests

BASE_URL = 'https://api.calorieninjas.com/v1'
HEADERS = {'X-Api-Key': 'FAKEKEY'}

"""
This is the real API key, so set it in above headers when you want to actually test API
we get free 10000 calls per month. So only use when we want to test this

FUydMH9rJLk2BumSCVxeaw==UIgSFFeVg0DnOgxr
"""


class NutritionApi:
    """
    API Wrapper to get nutrition info from
    https://calorieninjas.com/api
    """

    def get_nutrition(self, food_item: str) -> dict:
        """
        Takes a food item name as argument and returns its nutrition info.
        If the request is not successful, an exception is raised

        :params food_item: the food item to get nutrition information for
        """
        url = f"{BASE_URL}/nutrition?query={food_item}"

        response = requests.get(url, headers=HEADERS)

        if response.status_code == requests.codes.ok:
            nutrition_infos = json.loads(response.text)["items"]

            if len(nutrition_infos) == 0:
                raise Exception(f"Zero items found. Cannot retrieve nutrition for {food_item}")

            # we just return the first item found
            return nutrition_infos[0]

        raise Exception(f"Cannot retrieve nutrition for {food_item}")
