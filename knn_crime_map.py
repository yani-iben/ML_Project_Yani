# %%
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier

# %%
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV

# %%
arrests=pd.read_csv('arrests.csv')
arrests.head()

# %%
arrests.columns

# %%
crime_addresses=pd.read_csv('CrimeAddresses2.csv')
crime_addresses.head()

# %%
gdf_uniq=pd.read_csv("gdf_uniq.csv")

# %%
gdf_uniq.head()

# %%
gdf_uniq.columns

# %%
crime_data=pd.read_csv("Crime_Data.csv")
crime_data.head()

# %%
crime_data.columns

# %%
crime_data["Offense_cat"].unique()

# %%
import geopandas as gpd

# %%
gdf = gpd.read_file("CrimeGeocoded.shp")

# %%
print(type(gdf))

# %%
gdf.head()

# %%

gdf['Join_Key'] = (
    gdf["address"].str.split(",", n=1).str[0].str.upper().str.strip()
)

crime_addresses['Join_Key'] = crime_addresses['Street_Address'].str.upper().str.strip()

# %%
crime_data.columns

# %%

geocoded_unique_addresses = pd.merge(
    crime_addresses,
    gdf[['Join_Key', 'geometry']], # Only need the key and the geometry
    how='left',
    on='Join_Key'
)

# %%

crime_data["BlockNum_STR"] = crime_data["BlockNumber"].apply(
    lambda x: str(int(x)) if pd.notna(x) else ""
)

crime_data['Join_Key'] = (
    crime_data["BlockNum_STR"] + " " + crime_data["StreetName"].astype(str)
).str.upper().str.strip()


crime_addresses['Join_Key'] = crime_addresses['Street_Address'].str.upper().str.strip()



gdf['Join_Key'] = (
    gdf["address"].str.split(",", n=1).str[0].str.upper().str.strip()
)


# %%

address_cols_to_merge = ['Street_Address', 'geometry']

gdf_with_offense = pd.merge(
    crime_data,
    geocoded_unique_addresses[address_cols_to_merge + ['Join_Key']],
    how='left',
    on='Join_Key'
)

import geopandas as gpd
if 'geometry' in gdf_with_offense.columns:
    gdf_with_offense = gpd.GeoDataFrame(
        gdf_with_offense,
        geometry='geometry',
        crs='EPSG:4326'
    )
else:
    print("Error: 'geometry' column is missing after merge.")

# %%
gdf_for_map = gdf_with_offense.dropna(subset=['geometry']).to_crs(epsg=4326).copy()

# Reduce sample size (Try 2% or 1% if 5% is still slow)
sample_fraction = 0.02 # <-- Reduced to 2% for maximum speed
gdf_sampled = gdf_for_map.sample(frac=sample_fraction, random_state=42)
print(f"Plotting {len(gdf_sampled)} incidents (2% sample).")

# %%
gdf_sampled['longitude'] = gdf_sampled.geometry.x
gdf_sampled['latitude'] = gdf_sampled.geometry.y

# %%
# The style function returns a dictionary of style properties
def style_function_simple(feature):
    offense = feature['properties']['Offense_cat']
    color = COLOR_MAP.get(offense, COLOR_MAP['Other'])
    
    return {
        'fillColor': color,
        'color': 'black',  # Border color
        'weight': 0.5,
        'fillOpacity': 0.8,
        # Note: radius cannot be set here, it must be handled by point_to_layer or marker=CircleMarker()
    }

# %%
import folium
import geopandas as gpd
from folium import Element
import pandas as pd
import numpy as np # Ensure numpy is imported if used elsewhere

# --- 1. DEFINE COLOR MAP AND STYLE HELPERS ---

COLOR_MAP = {
    'Larceny': '#E6194B',       # Red
    'Assault': '#F58231',       # Orange
    'Vandalism': '#FFE119',     # Yellow
    'Drug Offense': '#3CB44B',  # Green
    'Burglary': '#4363D8',      # Blue
    'Auto Theft': '#911EB4',    # Purple
    'Other': '#AAAAAA'          # Gray for all others
}

# Helper to look up color
def get_color(offense):
    return COLOR_MAP.get(offense, COLOR_MAP['Other'])

# The function that tells folium how to draw each point
def point_to_circle_layer(feature, latlng):
    offense = feature['properties']['Offense_cat']
    color = get_color(offense)
    
    return folium.CircleMarker(
        location=latlng,
        radius=4,
        color='black',
        weight=0.5,
        fill=True,
        fill_color=color,
        fill_opacity=0.8,
        popup=f"Offense: {offense}"
    )

# --- 2. DEFINE LEGEND HTML ---

# Ensure the legend_html variable is defined here or imported
legend_html = '''
     <div style="position: fixed; 
                 bottom: 50px; left: 50px; width: 150px; height: auto; 
                 border:2px solid grey; z-index:9999; font-size:14px;
                 background-color:white; opacity:0.9;">
       &nbsp; <b>Crime Category</b> <br>
       '''
for category, color in COLOR_MAP.items():
    legend_html += f'&nbsp; <span style="color:{color};">&#9632;</span> &nbsp; {category}<br>'

legend_html += '</div>'


# --- 3. EXECUTE YOUR MAP GENERATION CODE ---

# NOTE: Assuming gdf_sampled is available from the cleaning/sampling step

# 1. Create a Minimal GeoDataFrame for GeoJSON serialization
MINIMAL_COLUMNS = ['Offense_cat', 'geometry', 'longitude', 'latitude']

# Create a clean, minimal copy of the sampled data
gdf_minimal = gdf_sampled[MINIMAL_COLUMNS].copy()

# Ensure the minimal DataFrame is explicitly set as a GeoDataFrame
gdf_minimal = gpd.GeoDataFrame(gdf_minimal, geometry='geometry', crs='EPSG:4326')

# Generate the GeoJSON string only from the minimal data
geojson_string = gdf_minimal.to_json()


# 2. Map Instance Creation
center_lat = gdf_minimal['latitude'].mean()
center_lon = gdf_minimal['longitude'].mean()
m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

folium.GeoJson(
    geojson_string,
    name='Crime Categories',
    style_function=style_function_simple, # Use the simpler style function
    tooltip=folium.GeoJsonTooltip(fields=['Offense_cat'], aliases=['Offense:']),
    marker=folium.CircleMarker(radius=4), # <-- Explicitly defines circle size
    show=True
).add_to(m)
# 4. Add Legend
m.get_root().html.add_child(Element(legend_html))


# 5. Final Save Attempt
try:
    m.save("interactive_crime_map_final_fix.html")
    print("Map saved successfully! Check the HTML file in your browser.")
except TypeError as e:
    print(f"Final error during save: {e}")
    print("FATAL: A non-serializable object is still contaminating the map structure.")

# Display in notebook environment
m


