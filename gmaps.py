import pandas as pd
import numpy as np
import folium
import json
import requests
import googlemaps
import geopy.distance
import streamlit as st

API_KEY = st.secrets['GMAPS_KEY']

def make_request(lat, long, pagetoken=None, search='self storage', key=API_KEY, radius='8000'):

    if radius == 'max':
        radius = '50000'

    if pagetoken is not None:
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{long}&radius={radius}&keyword={search}&key={key}&pagetoken={pagetoken}"
    else:
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{long}&radius={radius}&keyword={search}&key={key}"

    payload={}
    headers = {}

    out = {
        'data': json.loads(requests.get(url, headers=headers, data=payload).content),
        'url': url
    }

    return out

def parse_results(data):

    business_status = []
    lat_location = []
    long_location = []
    sw_corner_lat = []
    sw_corner_long = []
    ne_corner_lat = []
    ne_corner_long = []
    icon = []
    name = []
    place_id = []
    rating = []
    num_ratings = []
    google_types = []
    address = []

    for d in data['results']:
        business_status.append(d.get('business_status'))
        lat_location.append(d['geometry']['location']['lat'])
        long_location.append(d['geometry']['location']['lng'])
        sw_corner_lat.append(d['geometry']['viewport']['southwest']['lat'])
        sw_corner_long.append(d['geometry']['viewport']['southwest']['lng'])
        ne_corner_lat.append(d['geometry']['viewport']['northeast']['lat'])
        ne_corner_long.append(d['geometry']['viewport']['northeast']['lng'])
        icon.append(d.get('icon'))
        name.append(d.get('name'))
        place_id.append(d.get('place_id'))
        rating.append(d.get('rating'))
        num_ratings.append(d.get('user_ratings_total'))
        google_types.append(d.get('types'))
        address.append(d.get('vicinity'))

    return pd.DataFrame({
        'business_status': business_status,
        'lat_location': lat_location,
        'long_location': long_location,
        'sw_corner_lat': sw_corner_lat,
        'sw_corner_long': sw_corner_long,
        'ne_corner_lat': ne_corner_lat,
        'ne_corner_long': ne_corner_long,
        'icon': icon,
        'name': name,
        'place_id': place_id,
        'rating': rating,
        'num_ratings': num_ratings,
        'google_types': google_types,
        'address': address
    })

def get_competitors(lat, long, key=API_KEY):

    request_output = make_request(lat=lat, long=long, key=key)
    data, url = request_output['data'], request_output['url']

    output = []
    next_page = data
    new_url = ''
    if 'next_page_token' in data:

        # dump first page results into outut
        output.append(parse_results(data=data))

        # iterate through subsequent pages changing the url every time
        while 'next_page_token' in next_page:

            # make call with new pagetoken
            request_output = make_request(lat=lat, long=long, pagetoken=next_page['next_page_token'])
            next_page, new_url = request_output['data'], request_output['url']
            output.append(parse_results(data=data))
    else:
        output.append(parse_results(data=data))


    df = pd.concat(output).reset_index(drop=True)

    # TODO : drop duplicates!!

    return df

def get_competitor_meta(lat, long, name='red dot', key=API_KEY):
    """
    params
    ----
    name: name of facility who's lat long coord we're looking at ; going to exclude it from competitor set

    return
    ----

    total number of competitors
    dist to closest competitor
    avg comp distance away
    comp 1 mi
    comp 1-2 mi
    comp 2-3 mi
    comp 3-5 mi
    comp 5-10 mi
    comp 10-20 mi
    comp 20-30 mi
    avg comp rating
    avg comp number of ratings
    estimated facility size

    """

    df = get_competitors(lat=lat, long=long, key=key)

    # --- filter out target store ---

    # all store names to lowercase
    df['name'] = df['name'].apply(lambda x: x.lower())

    # create mask and take slice
    mask = [name not in store_name for store_name in df['name'].values]
    df = df[mask].reset_index(drop=True)

    # --- get fields ---

    # all comp
    total_competitors = df.shape[0]

    # - all dist metrics -
    distances = np.array(list(map(lambda x: geopy.distance.distance((lat, long), (x[0], x[1])).miles,
             df[['lat_location', 'long_location']].values)))


    # closest store
    closest = distances.min()

    # average comp distance away
    mean_dist, median_dist = distances.mean(), np.median(distances)

    # < 1 mile
    under_one_mile = len([x for x in distances if x < 1])

    # 1-2 mile
    one_two_mile = len([x for x in distances if x >= 1 and x < 2])

    # 2-3 mile
    two_three_mile = len([x for x in distances if x >= 2 and x < 3])

    # 3-5 mile
    three_five_mile = len([x for x in distances if x >= 3 and x < 5])

    # 5-10 mile
    five_ten_mile = len([x for x in distances if x >= 5 and x < 10])

    # 10-20 mile
    ten_twenty_mile = len([x for x in distances if x >= 10 and x < 20])

    # over 20 mile
    over_20_mile = len([x for x in distances if x >= 20])

    # avg rating
    mean_rating, median_rating = df['rating'].mean(), np.median(df['rating'].values)

    # avg num ratings
    mean_num_ratings, median_num_ratings = df['num_ratings'].mean(), np.median(df['num_ratings'].values)

    # TODO - est facility size


    metadata = {
        'total_comp': total_competitors,
        'closest_comp_dist': closest,
        'comp_less_1_mi': under_one_mile,
        'comp_1_to_2_mi': one_two_mile,
        'comp_2_to_3_mi': two_three_mile,
        'comp_3_to_5_mi': three_five_mile,
        'comp_5_to_10_mi': five_ten_mile,
        'comp_10_to_20_mi': ten_twenty_mile,
        'comp_over_20_mi': over_20_mile,
        'mean_rating': mean_rating,
        'median_rating': median_rating,
        'mean_num_reviews': mean_num_ratings,
        'median_num_reviews': median_num_ratings
    }

    return {
        'full': df,
        'meta': metadata

    }
