# %%
import pandas as pd
import numpy as np
import sys
# %%
crimedata=pd.read_csv("Crime_Data.csv")
crimedata.head()

# %%
fraction_block_nums=crimedata[crimedata["BlockNumber"] % 1 !=0]
len(crimedata["BlockNumber"]), len(fraction_block_nums["BlockNumber"])
1924/25512
# %%
# Create a new column "Street_Address" that combines Block Number & Street Name
crimedata["BlockNum_STR"] = crimedata["BlockNumber"].apply(
    lambda x: str(int(x)) if pd.notna(x) else ""
)

crimedata["Street_Address"] = np.where(
    crimedata["BlockNum_STR"] != "",
    crimedata["BlockNum_STR"] + " " + crimedata["StreetName"],
    crimedata["StreetName"]
)

crimedata.head()
# %%
crimedata["Street_Address"].unique().tolist()
# %%
len(crimedata["Street_Address"].unique().tolist()
)
# %%

# Searching the new Street_Address column for any values that don't contain a number 
counter=0
for address in crimedata["Street_Address"]:
    if address[0] not in ("0","1","2","3","4","5","6","7","8","9"):
        counter+=1
    else:
        counter+=0
counter

# Above code returned 1536, indicating that 1536 of the 25512 rows don't have a house number
# %%

crime_addresses=crimedata[["BlockNumber", "StreetName", "Street_Address"]]
crime_addresses.drop_duplicates(inplace=True)

# make a helper column to determine invalid addresses to drop

crime_addresses["helper"]=np.where(
    crime_addresses["BlockNumber"].isna() | crime_addresses["StreetName"].isna(),
    "drop",
    "keep"
)
crime_addresses["helper"].value_counts()

# %%
# Create additional columns for geocoding points for each address

crime_addresses["State"]="Virginia"
crime_addresses["City"]="Charlottesville"
crime_addresses.head()

# %%
crime_addresses["helper"].value_counts()

# %%
# Attempt Geocoding the addresses within Python

import geopandas as gpd
from geopandas.tools import geocode
from shapely.geometry import Point, Polygon
import geopy
import matplotlib as plt
import seaborn as sns
import pandas as pd
import contextily as cx
import numpy as np
# %%

crime_geo=pd.read_csv("CrimeAddresses.csv")
crime_geo.head()


# %%

gdf=geocode(crime_geo["Full_St_Address"], provider="arcgis", user_agent="python-requests/2.32.5")
gdf.to_file("CrimeGeocoded.shp", index=False)
# %%

gdf.head()

# %%
crime_geo.info()
# %%
gdf["match_address"]=gdf["address"].str.split(",", n=1).str[0]
gdf["match_address"]=gdf["match_address"].str.upper()
gdf.head()

# %%
crime_geo["BlockNumber"]=crime_geo["BlockNumber"].astype(str)
crime_geo["StreetName"]=crime_geo["StreetName"].astype(str)
crime_geo["match_address"]=crime_geo["BlockNumber"]+" "+crime_geo["StreetName"]
crime_geo=crime_geo.drop(columns="match_address")
crime_geo.head()
# %%
crime_geo.to_csv("CrimeAddresses2.csv", index=False)


# %%
merged=pd.merge(gdf_uniq, crime_geo, left_on="match_address", right_on="Full_St_Address", how="outer", validate="one_to_many", indicator="matched")
merged["matched"].value_counts()

# %%

gdf["match_address"]=gdf["match_address"]+", CHARLOTTESVILLE, VA"
gdf.head()
# %%

gdf_uniq=gdf
gdf_uniq["match_address"]=gdf_uniq["match_address"].drop_duplicates()
gdf_uniq["match_address"].is_unique
# %%
dupes = gdf_uniq[gdf_uniq['match_address'].duplicated(keep=False)]
dupes

# %%
gdf_uniq.head()
# %%
type(gdf_uniq)
# %%
gdf_uniq=gdf_uniq.dropna()
gdf_uniq["match_address"].is_unique
gdf_uniq.head()
# %%
gdf_uniq.to_file("gdf_uniq.shp")
# %%
gdf_uniq_nogeo=gdf_uniq[["address", "match_address"]]
gdf_uniq_nogeo.to_csv("gdf_uniq.csv")
# %%
