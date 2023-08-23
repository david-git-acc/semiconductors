from bs4 import BeautifulSoup as BS
import requests
from collections import Counter

# This program is designed to locate all the fabs from the site: https://en.wikipedia.org/wiki/List_of_semiconductor_fabrication_plants
# and display them on a map with their minimum node sizes (in nm) as the colour dimension

# Import the required library - need to use this to convert names into coordinates
from geopy.geocoders import Nominatim

# Initialise Nominatim API
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

# Parses the page so we can find the important info we need
page = BS(text, "html.parser")

opensemifabs_table = page.find("table" , {"id" : "opensemifabs"})
closedsemifabs_table = page.find("table" , {"id" : "closedsemifabs"})

# Gets all the individual rows of the table, with each row being a fab
opensemifabs =  opensemifabs_table.find_all("tr")[1:][0:10]
closedsemifabs = [] # closedsemifabs_table.find_all("tr")[1:]

# This function filters out all the numbers of a string and returns the list containing these numbers
# Needed so we can get the list of node sizes for each fab (and then use min() to select the minimum node size)
def get_numbers_only(string):
    allowed = ["0","1","2","3","4","5","6","7","8","9"]
    
    # This is where we'll store the numbers
    numlist = []
    
    # We build a string from each character that is a digit, add to the string and then add to the list
    # When a non-digit is detected, we add the number to numlist and clear this 
    current_str = ""
    
    for char in string:
        
        # Building the number, digit by digit (or char by char)  
        if char in allowed:
            current_str += char
            
        else:
            # When we find a non-digit, do above
            if current_str:
                numlist.append(int( current_str ) )
                current_str = ""
                
    # Don't forget to add the last string because otherwise you may forget to add the last number
    if current_str:
        numlist.append(current_str)
    
    return numlist
      
# Function which given a name, uses nominatim, a very generous service to find its coordinates automatically and returns latitude-longitude pairs
def get_coords(address): 
    
    # Using nominatim to get the latitude,longitude
    try:
        loc = geolocator.geocode(address)
        return (loc.latitude, loc.longitude)
    except:
        return None
    
    
# Sanitisation to kill all leading spaces of a string
def removeleadingspaces(string):
    # Keeps track of the indices 
    i=0

    for char in string:
        
        if char == " ":
            # This counts the number of leading spaces so we know from which point in the string to cut it at
            i+=1
        else:
            break
        
    return string[i:]

# Same as above but removes all the wikipedia references (e.g Haikou, China[3] <- removes the [3])
# These are always located at the end of the string, so we cut at the end
def removefollowingrefs(string):
    
    i=0

    for char in string:
        if char != "[":
            i+=1
        else:
            break
        
    return string[0:i]
    
# Combines the above 2 functions together
# Used on place names so that when we input the data into Nominatim to get the coordinates it doesn't get confused by the formatting, since we've removed it
def sanitisestring(string,num):
    return removefollowingrefs(
        
        removeleadingspaces( 
                                                            # The wikipedia place names are in the form [Country, Region, Place] so we need to select which one
                                                            # Do this with the num argument
                            string.replace("\n","").split(",")[num] ))
    
# This counter counts the number of fabs that each country has
country_counter = Counter({})

# These 2 lists are IMPLICITLY linked - for some index i, then locations[i], specified_node_sizes[i] refer to the same entry
# Need to preserve the order
# The locations list is used to locate them on the map, the node size gives each location its colour
locations = []
specified_node_sizes = []

# Since there's no node size data for some locations I have put them separately
unspecified_node_locations = []

# There is node data for closed locations but I thought that'd be overcomplicating it, so just locations would suffice for these, only 46 of them anyway
closed_locations = []

for fab in opensemifabs:
    # Get all of the properties of this specific fab
    fields = fab.find_all("td")
    
    # Get the location name - the third column in the wikipedia table is the location, so apply the sanitise function to get the location
    # This location name will then be passed to nominatim so we can get its coordinates to put on the map
    location_name = sanitisestring( fields[2].text, -1 )
    
    # The process technology node data is the 7th column, so get it by fields[6]
    process_technology_data = fields[6].text

    # Use the nominatim function to get the coordinates
    location = get_coords(location_name)
    
    # Get the country name - the country name will always be the first part of the "location" column (it's always Country, Region, City)
    country_data = sanitisestring(fields[2].text, 0)
    
    # Check that it actually says what the country is - some fields will have no location data whatsoever
    if country_data:
        country_counter.update({country_data : 1})
    
    # Get the list of node sizes as a list of numbers, then pick the smallest
    node_sizes = get_numbers_only(process_technology_data)
    
    # Some fabs will not have any node sizes listed, so if this is the case then just make it None, 
    # otherwise select the MINIMUM node size for the sake of comparison
    smallest_wafer_size = min(node_sizes) if node_sizes else None

    # Selecting which list to add the location to depending on if we have both attributes listed or not
    if location and smallest_wafer_size:
        locations.append(location)
        specified_node_sizes.append(smallest_wafer_size)
    elif location:
        unspecified_node_locations.append(location)
    
# Identical to above but without checking for node sizes, go and see the above for explanation   
for fab in closedsemifabs:
    fields = fab.find_all("td")
    

    location_name = sanitisestring( fields[2].text, -1 )
    
    country_data = fields[2].text.split(",")[0]
    if country_data:
        country_counter.update({country_data : 1})
    
    location = get_coords(location_name)
    
    if location:
        closed_locations.append(location)
        

# It's plotting time (rubs hands together)

from mpl_toolkits.basemap import Basemap
from matplotlib import pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

# This minimum will be used in the coding process
# Since there's such huge variation in node sizes, from 5000nm to 11nm, need to use a logarithmic code
minimum = min(specified_node_sizes)


    

# I borrowed this palette from the development mapmode on EU4 
my_cmap=mcolors.LinearSegmentedColormap.from_list('rg',["darkred", "yellow", "lime"], N=256).reversed()

# Turn into an np array so it's hopefully faster to load on the map and turn into map x-y coordinates
latitudes_specified = np.asarray([x[0] for x in locations])
longitudes_specified = np.asarray( [x[1] for x in locations] )
# Need to code the data, apply logarithmic scale (such that the minimum = 1)
specified_node_sizes = np.log( np.asarray(specified_node_sizes) * np.e / minimum )

# Again get the latitudes and longitudes into aan np array
latitudes_unspecified = np.asarray([x[0] for x in unspecified_node_locations])
longitudes_unspecified = np.asarray([x[1] for x in unspecified_node_locations])

# Ditto but for closed fabs
latitudes_closed = np.asarray([x[0] for x in closed_locations])
longitudes_closed = np.asarray([x[1] for x in closed_locations])

# If I tried to use -90,90 on latitude, it gave me some strange dimensions, so I had to manually adjust them
lat_min = -60
lat_max = 85
lon_min = -180
lon_max = 180

# 1 pixel = 1/96 of an inch
px=1/96

the_map = Basemap(llcrnrlon=lon_min, 
                  llcrnrlat=lat_min,
                  urcrnrlon=lon_max, 
                  urcrnrlat=lat_max, 
                  resolution="l", projection="mill")

# I only drew the borders, the rest would be dealt with by calling bluemarble()
the_map.drawcountries(color="#D3D3D3")

# Converting the lists of latitudes and longitudes into x-y coordinates on the map
longitudes_specified, latitudes_specified = the_map(longitudes_specified, latitudes_specified)
longitudes_unspecified, latitudes_unspecified = the_map(longitudes_unspecified, latitudes_unspecified)
longitudes_closed, latitudes_closed = the_map(longitudes_closed, latitudes_closed)

# Get the current figure and axes - these are only implicitly generated by a Basemap instance, 
# so need to call them explicitly
fig = plt.gcf()
ax = plt.gca()

# Again, this has to be done separately since most of the figure info is dealt with implicitly
fig.set_figheight(1080*px)
fig.set_figwidth(1920*px)

the_scattering = the_map.scatter(longitudes_specified,latitudes_specified, s=32, edgecolor="black", marker="o", c=specified_node_sizes, cmap = my_cmap, label = "Specified size")
unspecified_scattering = the_map.scatter(longitudes_unspecified, latitudes_unspecified, edgecolor="black", marker="s", s=16, c="blue", label = "Unspecified")
closed_scattering = the_map.scatter(longitudes_closed, latitudes_closed, s=32, marker="x", c = "red", label = "Closed fab")

bar = plt.colorbar(mappable=the_scattering, extend="both", label="Smallest FAB node size (nm) (coded: f(x) = ln( x * e / min ) )")

plt.title("Locations of semiconductor fabs and their node sizes")

# I wasn't sure how many "top #" countries I wanted, so I made it variable
n = 10
# Once sorted (this long code just sorts the dict by its values rather than its items), only keep the top n 
# values, discard everything after this point
top_n = sorted(country_counter.items(), key=lambda x:x[1], reverse= True  )[0:n]

# Magic numbers but I didn't know how to analytically determine the best separation distance between the
# text and the axes, so manual adjustment / trial and error
events_text = plt.text(-0.18,0.975, 
                       f"Top {n} countries (by\nnumber of fabs)", 
                       fontsize = 15,
                       transform=ax.transAxes )
                        # transAxes makes the coordinates given relative to the axes, such that
                        # 0 = the far left/bottom, and 1 = the far right/top

# Sanity printing
print("TOP N:" , top_n )

# Recording all top n countries on the figure
i = 1
for country, number in top_n:
    # Sanity checking print
    print(country, number)
    # THis is the string that will show on the figure, 
    # e.g 3. Taiwan (79)
    string = f"{i}. {country} ({number})"
    text = plt.text(-0.18,0.95 - i / 32, 
                       string,  
                       transform=ax.transAxes )
    i += 1
    

plt.legend()

the_map.bluemarble()


plt.savefig("test.png")



plt.show()