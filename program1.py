from bs4 import BeautifulSoup as BS
import requests
from collections import Counter


# Import the required library
from geopy.geocoders import Nominatim

# Initialize Nominatim API
geolocator = Nominatim(user_agent="MyApp")



# Headers to convince wikipedia you're not a robot
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0'
}

# See above, copied from stackoverflow
params = {
    'sort': 'dd',
    'filter': 'reviews-dd',
    'res_id': 18439027
}

url = "https://en.wikipedia.org/wiki/List_of_semiconductor_fabrication_plants"

text = requests.get(url=url, headers=headers,params=params).text

page = BS(text, "html.parser")

opensemifabs_table = page.find("table" , {"id" : "opensemifabs"})
closedsemifabs_table = page.find("table" , {"id" : "closedsemifabs"})

opensemifabs =  opensemifabs_table.find_all("tr")[1:]
closedsemifabs =  closedsemifabs_table.find_all("tr")[1:]

def get_numbers_only(string):
    allowed = ["0","1","2","3","4","5","6","7","8","9"]
    
    numlist = []
    
    current_str = ""
    
    for char in string:
        
        if char in allowed:
            current_str += char
            
        else:
            if current_str:
                numlist.append(int( current_str ) )
                current_str = ""
                
    if current_str:
        numlist.append(current_str)
    
    return numlist
      
# Function which given a name, uses nominatim, a very generous service to find its coordinates automatically and returns latitude-longitude pairs
def get_coords(address): 
    
    try:
        loc = geolocator.geocode(address)
        return (loc.latitude, loc.longitude)
    except:
        return None
    
    

def removeleadingspaces(string):
    i=0

    for char in string:
        
        if char == " ":
            i+=1
        else:
            break
        
    return string[i:]

def removefollowingrefs(string):
    
    i=0
    
    for char in string:
        if char != "[":
            i+=1
        else:
            break
        
    return string[0:i]
    
def sanitisestring(string,num):
    return removefollowingrefs(
        
        removeleadingspaces( 
                            
                            string.replace("\n","").split(",")[num] ))
    
    
country_counter = Counter({})
locations = []
specified_node_sizes = []
unspecified_node_locations = []
closed_locations = []

for fab in opensemifabs:
    fields = fab.find_all("td")
    

    location_data = sanitisestring( fields[2].text, -1 )
    process_technology_data = fields[6].text


    location = get_coords(location_data)
    
    country_data = sanitisestring(fields[2].text, 0)
    country_counter.update({country_data : 1})
    
    node_sizes = get_numbers_only(process_technology_data)
    
    smallest_wafer_size = min(node_sizes) if node_sizes else None

    if location and smallest_wafer_size:
        locations.append(location)
        specified_node_sizes.append(smallest_wafer_size)
    elif location:
        unspecified_node_locations.append(location)
    
        
for fab in closedsemifabs:
    fields = fab.find_all("td")
    

    location_data = sanitisestring( fields[2].text, -1 )
    
    country_data = sanitisestring(fields[2].text, 0)
    country_counter.update({country_data : 1})
    
    location = get_coords(location_data)
    
    print("closed fab:" , location)
    
    if location:
        closed_locations.append(location)
        


minimum = min(specified_node_sizes)

from mpl_toolkits.basemap import Basemap
from matplotlib import pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

# I borrowed this palette from the development mapmode on EU4 
my_cmap=mcolors.LinearSegmentedColormap.from_list('rg',["darkred", "yellow", "lime"], N=256).reversed()

latitudes_specified = np.asarray([x[0] for x in locations])
longitudes_specified = np.asarray( [x[1] for x in locations] )
specified_node_sizes = np.log( np.asarray(specified_node_sizes) * np.e / minimum )

latitudes_unspecified = np.asarray([x[0] for x in unspecified_node_locations])
longitudes_unspecified = np.asarray([x[1] for x in unspecified_node_locations])

latitudes_closed = np.asarray([x[0] for x in closed_locations])
longitudes_closed = np.asarray([x[1] for x in closed_locations])

lat_min = -60
lat_max = 85
lon_min = -180
lon_max = 180

px=1/96


the_map = Basemap(llcrnrlon=lon_min, 
                  llcrnrlat=lat_min,
                  urcrnrlon=lon_max, 
                  urcrnrlat=lat_max, 
                  resolution="l", 
                  projection="merc")



the_map.drawcoastlines()
the_map.fillcontinents(color="white", lake_color="#7FCDFF")

longitudes_specified, latitudes_specified = the_map(longitudes_specified, latitudes_specified)
longitudes_unspecified, latitudes_unspecified = the_map(longitudes_unspecified, latitudes_unspecified)
longitudes_closed, latitudes_closed = the_map(longitudes_closed, latitudes_closed)

the_map.drawcountries()
the_map.drawmapboundary(fill_color="#7FCDFF")

figure = plt.gcf()
ax = plt.gca()

the_scattering = the_map.scatter(longitudes_specified,latitudes_specified, s=32, edgecolor="black", marker="o", c=specified_node_sizes, cmap = my_cmap, label = "Specified size")
unspecified_scattering = the_map.scatter(longitudes_unspecified, latitudes_unspecified, edgecolor="black", marker="s", s=16, c="blue", label = "Unspecified")
closed_scattering = the_map.scatter(longitudes_closed, latitudes_closed, s=32, marker="x", c = "red", label = "Closed Fab")

bar = plt.colorbar(mappable=the_scattering, extend="both", label="Smallest FAB node size (nm) (coded: f(x) = ln( x * e / min ) )")

plt.title("Locations of semiconductor FABs and their node sizes")

plt.legend()
plt.show()