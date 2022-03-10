from sklearn.neighbors import BallTree
import numpy as np
import pandas as pd
from shapely import wkt
import geopandas as gpd
import pyproj
from assets.dem_col_names import DEM_COL_NAMES
import streamlit as st
import smart_open


class TractMapper:

    def __init__(self):

        # cpreds = pd.read_csv('data/clust_preds.csv')
        # mygeo = gpd.read_file('data/tracts.json')
        #
        # self.data = pd.merge(mygeo, cpreds.drop(['city', 'geom_col'], axis=1), on='zoneid')
        # self.data.to_crs(pyproj.CRS.from_epsg(4326), inplace=True)

        BUCKET = 'neighborhoodscout'
        DEM_FILE = 'all_tracts_and_demographics.csv'
        GEO_FILE = 'full_new.geojson'
        RD_DEM_FILE = 'rd_demographics.csv'

        aws_key = st.secrets['AWS_ACCESS_KEY_ID']
        aws_secret = st.secrets['AWS_SECRET_ACCESS_KEY'] 

        dem_path = 's3://{}:{}@{}/{}'.format(aws_key, aws_secret, BUCKET, DEM_FILE)
        geo_path = 's3://{}:{}@{}/{}'.format(aws_key, aws_secret, BUCKET, GEO_FILE)
        rd_dem_path = 's3://{}:{}@{}/{}'.format(aws_key, aws_secret, BUCKET, RD_DEM_FILE)

        self.data = gpd.read_file(smart_open.smart_open(geo_path))
        self.data = self.data.drop_duplicates()
        self.data.to_crs(pyproj.CRS.from_epsg(4326), inplace=True)

        # self.dem_data = pd.read_csv('data/all_tracts_and_demographics.csv').drop('Unnamed: 0', axis=1).rename(columns={'request': 'zoneid'})
        self.dem_data = pd.read_csv(smart_open.smart_open(dem_path)).drop('Unnamed: 0', axis=1).rename(columns={'request': 'zoneid'})
        self.composite_df = pd.read_csv('composite_variables1.csv')
        self.rd_dem_data = pd.read_csv(smart_open.smart_open(rd_dem_path)).drop('Unnamed: 0', axis=1)

        self.btree = BallTree(np.deg2rad(self.data[['latitude', 'longitude']]))

    def get_n_nearest(self, lat, long, n=10):
        """
        use ball tree
        """
        point = np.deg2rad(np.array([lat, long]).reshape(1, -1))

        nnearest = self.btree.query(point, n, return_distance=False)[0]
        nnearest = self.data.iloc[nnearest, :]
        self.nearest = nnearest
        self.nearest = pd.merge(self.composite_df, self.nearest, on='zoneid')

        return self.nearest

    def compare_demographics(self, sort='max'):
        mask = self.dem_data['zoneid'].isin(self.nearest['zoneid']).values
        merged = self.dem_data[mask]
        other = self.dem_data[~mask]

        data = pd.DataFrame({
            'current neighborhoods': merged.mean().values,
            'RD neighborhood avg': self.rd_dem_data.mean().values,
            'national avg': other.mean().values,
        })

        data.index = DEM_COL_NAMES
        f = {k:'{:.2f}' for k in data.columns}

        if sort == 'max':
            return data.round(2).style.highlight_max(axis=1, color='#CCCCFF').format(f)
        else:
            return data.round(2).style.highlight_min(axis=1, color='#CCCCFF').format(f)
