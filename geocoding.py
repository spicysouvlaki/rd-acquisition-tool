from geopy.geocoders import Nominatim


def parse_address_string(addy):
    locator = Nominatim(user_agent="myGeocoder")
    location = locator.geocode(addy)

    try:
        return {'lat': location.latitude, 'long': location.longitude}
    except Exception as e:
        # print(f"{e=}")
        return None
