"""Adapted from https://github.com/OSU-NLP-Group/TravelPlanner/blob/main/evaluation/hard_constraint.py"""

import math
import os
import re

from collaborative_gym.envs.travel_planner.tools import (
    Accommodations,
    Attractions,
    Flights,
    GoogleDistanceMatrix,
    Restaurants,
)
from collaborative_gym.envs.travel_planner.utils.func import get_valid_name_city


class HardConstraintEvaluator:
    def __init__(self, database_dir: str):
        self.database_dir = database_dir
        self.flight_search = Flights(
            path=os.path.join(self.database_dir, "flights/clean_Flights_2022.csv")
        )
        self.accommodation_search = Accommodations(
            path=os.path.join(
                self.database_dir, "accommodations/clean_accommodations_2022.csv"
            )
        )
        self.restaurant_search = Restaurants(
            path=os.path.join(
                self.database_dir, "restaurants/clean_restaurant_2022.csv"
            )
        )
        self.google_distance_matrix = GoogleDistanceMatrix(
            path=os.path.join(self.database_dir, "googleDistanceMatrix/distance.csv")
        )
        self.attraction_search = Attractions(
            path=os.path.join(self.database_dir, "attractions/attractions.csv")
        )

    @staticmethod
    def extract_from_to(text: str):
        """
        Extracts 'A' and 'B' from the format "from A to B" in the given text, with B ending at a comma or the end of the string.

        Args:
        - text (str): The input string.

        Returns:
        - tuple: A tuple containing 'A' and 'B'. If no match is found, returns (None, None).
        """
        pattern = r"from\s+(.+?)\s+to\s+([^,]+)(?=[,\s]|$)"
        matches = re.search(pattern, text)
        return matches.groups() if matches else (None, None)

    def get_total_cost(self, question, tested_data):
        total_cost = 0
        for i in range(min(question["days"], len(tested_data))):
            unit = tested_data[i]
            # transportation
            if unit["transportation"] and unit["transportation"] != "-":
                value = unit["transportation"]
                org_city, dest_city = self.extract_from_to(value)
                if org_city is None or dest_city is None:
                    org_city, dest_city = self.extract_from_to(unit["current_city"])

                if org_city is None or dest_city is None:
                    pass
                else:
                    if "flight number" in value.lower():
                        res = self.flight_search.data[
                            self.flight_search.data["Flight Number"]
                            == value.split("Flight Number: ")[1].split(",")[0]
                        ]
                        if len(res) > 0:
                            total_cost += (
                                res["Price"].values[0] * question["people_number"]
                            )

                    elif "self-driving" in value.lower() or "taxi" in value.lower():
                        if "self-driving" in value.lower():
                            # print(org_city,dest_city)
                            cost = self.google_distance_matrix.run_for_evaluation(
                                org_city, dest_city, "self-driving"
                            )["cost"]
                            total_cost += cost * math.ceil(
                                question["people_number"] * 1.0 / 5
                            )
                        else:
                            cost = self.google_distance_matrix.run_for_evaluation(
                                org_city, dest_city, "taxi"
                            )["cost"]
                            total_cost += cost * math.ceil(
                                question["people_number"] * 1.0 / 4
                            )

            # breakfast
            if unit["breakfast"] and unit["breakfast"] != "-":
                name, city = get_valid_name_city(unit["breakfast"])
                res = self.restaurant_search.data[
                    (
                        self.restaurant_search.data["Name"]
                        .astype(str)
                        .str.contains(re.escape(name))
                    )
                    & (self.restaurant_search.data["City"] == city)
                ]
                if len(res) > 0:
                    total_cost += (
                        res["Average Cost"].values[0] * question["people_number"]
                    )

            # lunch
            if unit["lunch"] and unit["lunch"] != "-":
                name, city = get_valid_name_city(unit["lunch"])
                res = self.restaurant_search.data[
                    (
                        self.restaurant_search.data["Name"]
                        .astype(str)
                        .str.contains(re.escape(name))
                    )
                    & (self.restaurant_search.data["City"] == city)
                ]
                if len(res) > 0:
                    total_cost += (
                        res["Average Cost"].values[0] * question["people_number"]
                    )

            # dinner
            if unit["dinner"] and unit["dinner"] != "-":
                name, city = get_valid_name_city(unit["dinner"])
                res = self.restaurant_search.data[
                    (
                        self.restaurant_search.data["Name"]
                        .astype(str)
                        .str.contains(re.escape(name))
                    )
                    & (self.restaurant_search.data["City"] == city)
                ]
                if len(res) > 0:
                    total_cost += (
                        res["Average Cost"].values[0] * question["people_number"]
                    )

            # accommodation
            if unit["accommodation"] and unit["accommodation"] != "-":
                name, city = get_valid_name_city(unit["accommodation"])
                res = self.accommodation_search.data[
                    (
                        self.accommodation_search.data["NAME"]
                        .astype(str)
                        .str.contains(re.escape(name))
                    )
                    & (self.accommodation_search.data["city"] == city)
                ]
                if len(res) > 0:
                    total_cost += res["price"].values[0] * math.ceil(
                        question["people_number"]
                        * 1.0
                        / res["maximum occupancy"].values[0]
                    )
        # print(total_cost)
        return total_cost

    def is_valid_room_rule(self, question, tested_data):
        if question["local_constraint"]["house rule"] is None:
            return None, None

        for i in range(min(question["days"], len(tested_data))):
            unit = tested_data[i]
            if unit["accommodation"] and unit["accommodation"] != "-":
                name, city = get_valid_name_city(unit["accommodation"])
                res = self.accommodation_search.data[
                    (
                        self.accommodation_search.data["NAME"]
                        .astype(str)
                        .str.contains(re.escape(name))
                    )
                    & (self.accommodation_search.data["city"] == city)
                ]
                if len(res) > 0:
                    if question["local_constraint"][
                        "house rule"
                    ] == "smoking" and "No smoking" in str(
                        res["house_rules"].values[0]
                    ):
                        return (
                            False,
                            f"The house rule should be {question['local_constraint']['house rule']}.",
                        )
                    if question["local_constraint"][
                        "house rule"
                    ] == "parties" and "No parties" in str(
                        res["house_rules"].values[0]
                    ):
                        return (
                            False,
                            f"The house rule should be {question['local_constraint']['house rule']}.",
                        )
                    if question["local_constraint"][
                        "house rule"
                    ] == "children under 10" and "No children under 10" in str(
                        res["house_rules"].values[0]
                    ):
                        return (
                            False,
                            f"The house rule should be {question['local_constraint']['house rule']}.",
                        )
                    if question["local_constraint"][
                        "house rule"
                    ] == "visitors" and "No visitors" in str(
                        res["house_rules"].values[0]
                    ):
                        return (
                            False,
                            f"The house rule should be {question['local_constraint']['house rule']}.",
                        )
                    if question["local_constraint"][
                        "house rule"
                    ] == "pets" and "No pets" in str(res["house_rules"].values[0]):
                        return (
                            False,
                            f"The house rule should be {question['local_constraint']['house rule']}.",
                        )

        return True, None

    def is_valid_cuisine(self, question, tested_data):
        cuisine_set = set()
        if question["local_constraint"]["cuisine"]:
            for i in range(min(question["days"], len(tested_data))):
                unit = tested_data[i]

                if unit["breakfast"] and unit["breakfast"] != "-":
                    name, city = get_valid_name_city(unit["breakfast"])
                    if city == question["org"]:
                        continue
                    res = self.restaurant_search.data[
                        (
                            self.restaurant_search.data["Name"]
                            .astype(str)
                            .str.contains(re.escape(name))
                        )
                        & (self.restaurant_search.data["City"] == city)
                    ]
                    if len(res) > 0:
                        for cuisine in question["local_constraint"]["cuisine"]:
                            if cuisine in res.iloc[0]["Cuisines"]:
                                cuisine_set.add(cuisine)

                if unit["lunch"] and unit["lunch"] != "-":
                    name, city = get_valid_name_city(unit["lunch"])
                    if city == question["org"]:
                        continue
                    res = self.restaurant_search.data[
                        (
                            self.restaurant_search.data["Name"]
                            .astype(str)
                            .str.contains(re.escape(name))
                        )
                        & (self.restaurant_search.data["City"] == city)
                    ]
                    if len(res) > 0:
                        for cuisine in question["local_constraint"]["cuisine"]:
                            if cuisine in res.iloc[0]["Cuisines"]:
                                cuisine_set.add(cuisine)

                if unit["dinner"] and unit["dinner"] != "-":
                    name, city = get_valid_name_city(unit["dinner"])
                    if city == question["org"]:
                        continue
                    res = self.restaurant_search.data[
                        (
                            self.restaurant_search.data["Name"]
                            .astype(str)
                            .str.contains(re.escape(name))
                        )
                        & (self.restaurant_search.data["City"] == city)
                    ]
                    if len(res) > 0:
                        for cuisine in question["local_constraint"]["cuisine"]:
                            if cuisine in res.iloc[0]["Cuisines"]:
                                cuisine_set.add(cuisine)

            if len(cuisine_set) == len(question["local_constraint"]["cuisine"]):
                return True, None
            else:
                # judge which cuisine is not satisfied
                for cuisine in question["local_constraint"]["cuisine"]:
                    if cuisine not in cuisine_set:
                        return False, f"The cuisine {cuisine} is not satisfied."
                # return False, f"The cuisine should be {question['local_constraint']['cuisine']}."
        else:
            return None, None

    @staticmethod
    def is_valid_transportation(question, tested_data):
        if question["local_constraint"]["transportation"] is None:
            return None, None
        for i in range(min(question["days"], len(tested_data))):
            unit = tested_data[i]
            if unit["transportation"] and unit["transportation"] != "-":
                value = unit["transportation"]
                if (
                    question["local_constraint"]["transportation"] == "no flight"
                    and "Flight" in value
                ):
                    return (
                        False,
                        f"The transportation should not be {question['local_constraint']['transportation']}.",
                    )
                elif (
                    question["local_constraint"]["transportation"] == "no self-driving"
                    and "Self-driving" in value
                ):
                    return (
                        False,
                        f"The transportation should not be {question['local_constraint']['transportation']}.",
                    )

        return True, None

    def is_valid_room_type(self, question, tested_data):
        if question["local_constraint"]["room type"] is None:
            return None, None
        for i in range(min(question["days"], len(tested_data))):
            unit = tested_data[i]
            if unit["accommodation"] and unit["accommodation"] != "-":
                name, city = get_valid_name_city(unit["accommodation"])
                res = self.accommodation_search.data[
                    (
                        self.accommodation_search.data["NAME"]
                        .astype(str)
                        .str.contains(re.escape(name))
                    )
                    & (self.accommodation_search.data["city"] == city)
                ]
                if len(res) > 0:
                    if (
                        question["local_constraint"]["room type"] == "not shared room"
                        and res["room type"].values[0] == "Shared room"
                    ):
                        return (
                            False,
                            f"The room type should be {question['local_constraint']['room type']}.",
                        )
                    # "shared room", "not shared room", "private room", "entire room"
                    elif (
                        question["local_constraint"]["room type"] == "shared room"
                        and res["room type"].values[0] != "Shared room"
                    ):
                        return (
                            False,
                            f"The room type should be {question['local_constraint']['room type']}.",
                        )

                    elif (
                        question["local_constraint"]["room type"] == "private room"
                        and res["room type"].values[0] != "Private room"
                    ):
                        return (
                            False,
                            f"The room type should be {question['local_constraint']['room type']}.",
                        )

                    elif (
                        question["local_constraint"]["room type"] == "entire room"
                        and res["room type"].values[0] != "Entire home/apt"
                    ):
                        return (
                            False,
                            f"The room type should be {question['local_constraint']['room type']}.",
                        )

        return True, None

    def run(self, query_data, tested_data):
        return_info = {}
        return_info["valid_cuisine"] = self.is_valid_cuisine(query_data, tested_data)
        return_info["valid_room_rule"] = self.is_valid_room_rule(
            query_data, tested_data
        )
        return_info["valid_transportation"] = self.is_valid_transportation(
            query_data, tested_data
        )
        return_info["valid_room_type"] = self.is_valid_room_type(
            query_data, tested_data
        )
        return_info["valid_cost"] = (
            bool(self.get_total_cost(query_data, tested_data) <= query_data["budget"]),
            None,
        )

        return return_info
