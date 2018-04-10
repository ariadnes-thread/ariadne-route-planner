from yelpapi import YelpAPI


class YelpScraper:
    """
    Right now it's basically a wrapper for YelpAPI object.

    Example
    y = YelpScraper('API KEY')
    res = y.get_pois(34.140940, -118.127974, 5000)  # Search near Pasadena
    biz_id = res['businesses'][0]['id']
    y.get_poi_features(biz_id)
    """

    def __init__(self, api_key):
        self.yelp = YelpAPI(api_key)

    def get_pois(self, latitude, longitude, radius):
        """
        Search Yelp for points of interest near the given latitude and
        longitude.
        https://www.yelp.com/developers/documentation/v3/business_search
        :param latitude: Decimal latitude.
        :param longitude: Decimal latitude.
        :param radius: Search radius in *meters*.
        """
        return self.yelp.search_query(latitude=latitude, longitude=longitude,
                                      radius=radius)

    def get_poi_features(self, yelpid):
        """
        Get details about a specific point of interest, given its Yelp ID.
        """
        return self.yelp.business_query(yelpid)
