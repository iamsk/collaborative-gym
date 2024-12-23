"""Adapted from https://github.com/OSU-NLP-Group/TravelPlanner/blob/main/tools/accommodations/apis.py"""

import pandas as pd
from pandas import DataFrame

from collaborative_gym.envs.travel_planner.utils.func import extract_before_parenthesis


class Accommodations:
    def __init__(self, path="../database/accommodations/clean_accommodations_2022.csv"):
        self.path = path
        self.data = pd.read_csv(self.path).dropna()[
            [
                "NAME",
                "price",
                "room type",
                "house_rules",
                "minimum nights",
                "maximum occupancy",
                "review rate number",
                "city",
            ]
        ]

    def load_db(self):
        self.data = pd.read_csv(self.path).dropna()

    def run(
        self,
        city: str,
    ) -> DataFrame:
        """Search for accommodations by city."""
        results = self.data[self.data["city"] == city]
        if len(results) == 0:
            # return "There is no attraction in this city."
            return "Cannot find accomodations information for this city."

        return results

    def run_for_annotation(
        self,
        city: str,
    ) -> DataFrame:
        """Search for accommodations by city."""
        results = self.data[self.data["city"] == extract_before_parenthesis(city)]
        return results
