from typing import Literal

import googlemaps


class GoogleMap:
    def __init__(self, google_map_api_key):
        self.api_key = google_map_api_key
        self.gmaps = googlemaps.Client(key=self.api_key)

    def distance_matrix(
        self,
        origins,
        destinations,
        mode: Literal["driving", "walking", "bicycling", "transit"],
        transit_mode=None,
    ):
        """https://github.com/googlemaps/google-maps-services-python/blob/master/googlemaps/distance_matrix.py

        Simplify the query and the returned data to only include key information.
        :param origins: One or more addresses, Place IDs, and/or latitude/longitude
            values, from which to calculate distance and time. Each Place ID string
            must be prepended with 'place_id:'. If you pass an address as a string,
            the service will geocode the string and convert it to a
            latitude/longitude coordinate to calculate directions.
        :type origins: a single location, or a list of locations, where a
            location is a string, dict, list, or tuple

        :param destinations: One or more addresses, Place IDs, and/or lat/lng values
            , to which to calculate distance and time. Each Place ID string must be
            prepended with 'place_id:'. If you pass an address as a string, the
            service will geocode the string and convert it to a latitude/longitude
            coordinate to calculate directions.
        :type destinations: a single location, or a list of locations, where a
            location is a string, dict, list, or tuple

        :param mode: Specifies the mode of transport to use when calculating
            directions. Valid values are "driving", "walking", "transit" or
            "bicycling".
        :type mode: string

        :param transit_mode: Specifies one or more preferred modes of transit.
            This parameter may only be specified for requests where the mode is
            transit. Valid values are "bus", "subway", "train", "tram", "rail".
            "rail" is equivalent to ["train", "tram", "subway"].
        :type transit_mode: string or list of strings
        """
        response = self.gmaps.distance_matrix(
            origins, destinations, mode=mode, transit_mode=transit_mode
        )

        if response["status"] != "OK":
            raise Exception(f"Google Map API error: {response['status']}")

        matrix = []
        for row in response["rows"]:
            matrix.append(
                [
                    {
                        "distance": element["distance"]["text"],
                        "duration": element["duration"]["text"],
                    }
                    for element in row["elements"]
                ]
            )

        trimmed_response = {
            "origin_addresses": response["origin_addresses"],
            "destination_addresses": response["destination_addresses"],
            "matrix": matrix,
        }

        return trimmed_response
