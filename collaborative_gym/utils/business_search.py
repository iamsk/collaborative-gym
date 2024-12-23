import googlemaps


class YelpSearch:
    def __init__(self, yelp_api_key):
        try:
            from yelpapi import YelpAPI
        except ImportError:
            raise ImportError("Please install yelpapi using 'pip install yelpapi'")
        self.api_key = yelp_api_key

    def search(self, term: str, location: str, limit: int):
        """https://docs.developer.yelp.com/reference/v3_business_search

        Simplify the query and the returned data to only include key information.
        """
        with YelpAPI(self.api_key) as yelp_api:
            response = yelp_api.search_query(term=term, location=location, limit=limit)

        trimmed_response = []
        for business in response["businesses"]:
            trimmed_response.append(
                {
                    "name": business["name"],
                    "url": business["url"],
                    "rating": business["rating"],
                    "price": business.get("price", "No information"),
                    "address": ", ".join(business["location"]["display_address"]),
                    "phone": business["phone"],
                }
            )

        return trimmed_response


class GooglePlace:
    def __init__(self, google_map_api_key):
        self.api_key = google_map_api_key
        self.gmaps = googlemaps.Client(key=self.api_key)

    def search(self, term: str, location: str, limit: int):
        """Search businesses using Google Places API.

        https://github.com/googlemaps/google-maps-services-python/blob/master/googlemaps/places.py
        """
        response = self.gmaps.places(query=f"{term} in {location}")
        trimmed_response = []
        for r in response["results"][:limit]:
            try:
                s = r["photos"][0]["html_attributions"][0]
                url = s[s.find("https://") :]
                url = url[: url.find('"')]
            except KeyError:
                url = ""
            trimmed_response.append(
                {
                    "name": r["name"],
                    "url": url,
                    "rating": r.get("rating", "No information"),
                    "price": r.get("price_level", "No information"),
                    "address": r["formatted_address"],
                }
            )

        return trimmed_response
