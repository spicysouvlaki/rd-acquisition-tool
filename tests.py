import streamlit as st
import pandas as pd
import geopandas as gpd
from geocoding import parse_address_string

#Import folium and related plugins
import folium
from folium import Marker
from folium.plugins import MarkerCluster
import json
from geomapping import TractMapper

# use this: https://jingwen-z.github.io/how-to-draw-a-variety-of-maps-with-folium-in-python/


@st.cache(allow_output_mutation=True)
def get_data():
    # global data
    # data = gpd.read_file('data/test.geojson')
    #
    # global jdata
    # jdata = json.load(open('data/test.geojson', 'r'))

    global tm
    tm = TractMapper()

    return tm

TILES = {
    'cartodbdark_matter': 'cartodbdark_matter',
    'cartodbpositron': 'cartodbpositron',
    'OpenStreetMap': 'OpenStreetMap',
    'Stamen Toner': 'Stamen Toner',
    'Stamen Terrain': 'Stamen Terrain',
    # 'stadia': 'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png'
}

from branca.colormap import linear, LinearColormap
from assets.colors import COLORS

nbh_count_colormap = linear.YlGnBu_09.scale(1, 5)
other_cm = LinearColormap(colors=[COLORS[x] for x in COLORS],
                        index=[1,2,3,4,5]
)

def display_map(tmapper=None, yes=False, lat=None, long=None, n=None, tile='Stamen Terrain'):
    if yes:
        nearest = tmapper.get_n_nearest(lat, long, n=n)
        # jsondata = gpd.GeoDataFrame(nearest).to_json()
        gpddata = gpd.GeoDataFrame(nearest)
        m = folium.Map([lat, long], zoom_start=11) # tiles=TILES[tile]

        style_function = lambda x : {
            'fillColor': other_cm(x['properties']['cluster prediction']),
            'color': 'gray',
            'weight': 2.5,
            'fillOpacity': 0.35
        }

        highlight_function = lambda x: {'fillColor': '#000000',
                                'color':'#000000',
                                'fillOpacity': 0.4,
                                'weight': 0.5}

        folium.GeoJson(gpddata, style_function=style_function, highlight_function=highlight_function,
            tooltip=folium.GeoJsonTooltip(
            fields=['city', 'cluster prediction',  'cluster 1 probability',
                     'cluster 2 probability',
                     'cluster 3 probability',
                     'cluster 4 probability',
                     'cluster 5 probability', 'crime index', 'wealth index'],
            localize=True
        )).add_to(m)

        for sty in TILES:
            folium.raster_layers.TileLayer(TILES[sty]).add_to(m)

        folium.LayerControl().add_to(m)

        folium.Marker(location=[lat, long], draggable=False,
        popup="""lat: {}, long: {}""".format(
                        round(lat, 3), round(long, 3)),
                      icon=folium.Icon()).add_to(m)

    else:
        pass
        # m = folium.Map([28.775537, -81.311504], tiles='OpenStreetMap', zoom_start=11)
        #
        # # Add polygon boundary to folium map
        # folium.GeoJson(jdata, style_function = lambda x: {'color': 'blue','weight': 2.5,'fillOpacity': 0.3},
        # name='Orlando').add_to(m)


    # # Add marker for Location
    # folium.Marker(location=point,
    # popup="""
    #               <i>BC Concentration: </i> <br> <b>{}</b> ug/m3 <br> <hr>
    #               <i>NO<sub>2</sub> Concentration: </i><b><br>{}</b> ppb <br>
    #               """.format(
    #                 round(df.loc[spatial.KDTree(df[['Latitude', 'Longitude']]).query(point)[1]]['BC_Predicted_XGB'],2),
    #                 round(df.loc[spatial.KDTree(df[['Latitude', 'Longitude']]).query(point)[1]]['NO2_Predicted_XGB'],2)),
    #               icon=folium.Icon()).add_to(m)

    return st.markdown(m._repr_html_(), unsafe_allow_html=True)

def main():
    st.header("Red Dot Cluster Analysis Tool")
    st.text("")
    st.markdown('<p class="big-font"> Use this to visualize and analyze clusters at a neighborhood level </p>', unsafe_allow_html=True)
    st.text("")
    st.markdown('<p class="big-font"> <b> Enter an address, city, or town name below </b> </p>', unsafe_allow_html=True)

    N = st.slider("How many neighborhoods do you want to see?", 1, 30, 15)
    address = st.text_input("Enter address or city", "Pine Bluff, Arkansas")

    # Use the convert_address function to convert address to coordinates
    coordinates = parse_address_string(address)

    tmapper = get_data()

    #Call the display_map function by passing coordinates, dataframe and geoJSON file
    st.text("")
    if 'lat' in coordinates:
        display_map(tmapper, True, coordinates['lat'], coordinates['long'], N)
    else:
        display_map()

    st.text("")
    st.markdown("Demographic Data")
    st.text("")
    df = tmapper.compare_demographics()
    st.dataframe(df)

main()
