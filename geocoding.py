from geopy.geocoders import Nominatim


def parse_address_string(addy):
    try:
        locator = Nominatim(user_agent="my_rd_app")
    except:
        locator = Nominatim(user_agent='application')
    location = locator.geocode(addy)

    try:
        return {'lat': location.latitude, 'long': location.longitude}
    except Exception as e:
        # print(f"{e=}")
        return None
