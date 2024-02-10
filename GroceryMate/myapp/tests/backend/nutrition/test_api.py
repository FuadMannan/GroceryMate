import unittest
from unittest.mock import patch
import json

import GroceryMate.myapp.backend.nutrition.api as file_name


class FakeResponseObject:
    status_code: int
    text: str


class TestNutritionApi(unittest.TestCase):

    @patch(f'{file_name.__name__}.requests.get')
    def test_get_nutrition_400_status_code(self, mock_requests_get):
        fake = FakeResponseObject()
        fake.status_code = 400

        mock_requests_get.return_value = fake

        with self.assertRaises(Exception):
            file_name.NutritionApi().get_nutrition("bread")

    @patch(f'{file_name.__name__}.requests.get')
    def test_get_nutrition_gets_first_item(self, mock_requests_get):
        fake_text = """
            {"items": [{"name": "bread", "calories": 261.6, 
            "serving_size_g": 100.0, "fat_total_g": 3.4, 
            "fat_saturated_g": 0.7, "protein_g": 8.8, "sodium_mg": 495, 
            "potassium_mg": 98, "cholesterol_mg": 0, 
            "carbohydrates_total_g": 50.2, "fiber_g": 2.7, "sugar_g": 5.7},
            {"name": "bread", "calories": 261.6, 
            "serving_size_g": 100.0, "fat_total_g": 3.4, 
            "fat_saturated_g": 0.7, "protein_g": 8.8, "sodium_mg": 495, 
            "potassium_mg": 98, "cholesterol_mg": 0, 
            "carbohydrates_total_g": 50.2, "fiber_g": 2.9, "sugar_g": 5.7}]}
        """

        fake = FakeResponseObject()
        fake.status_code = 200
        fake.text = fake_text

        mock_requests_get.return_value = fake

        response = file_name.NutritionApi().get_nutrition("bread")

        self.assertEquals(
            json.loads(fake_text)["items"][0],
            response
        )

    @patch(f'{file_name.__name__}.requests.get')
    def test_get_nutrition_zero_items_returned(self, mock_requests_get):
        fake_text = """{"items": []}"""

        fake = FakeResponseObject()
        fake.status_code = 200
        fake.text = fake_text

        mock_requests_get.return_value = fake

        with self.assertRaises(Exception):
            response = file_name.NutritionApi().get_nutrition("bread")
