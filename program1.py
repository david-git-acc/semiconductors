from bs4 import BeautifulSoup as BS
import requests
from mpl_toolkits.basemap import Basemap
import urllib

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
    
    # Get the actual URL for export online
    url = 'https://nominatim.openstreetmap.org/search/' + urllib.parse.quote(address) +'?format=json'

    response = requests.get(url).json()
    
    try:
        # The data itself
        latitude = float(response[0]["lat"])
        longitude = float(response[0]["lon"])
        
        return (latitude, longitude )
    
    except:
        # Not guaranteed to get a response - lots of possible invalid names on totaljobs or just too obscure to find
        return None
    
locations = []
wafersizes = []


for fab in opensemifabs:
    fields = fab.find_all("td")
    
    try:
        location_data = fields[2].text.split(",")[-1]
        process_technology_data = fields[6].text
        

        
        # location = get_coords(location_data)
        smallest_wafer_size = get_numbers_only(process_technology_data)
        print(location_data, smallest_wafer_size)
        
        
        # locations.append(location)
        wafersizes.append(smallest_wafer_size)
    except:
        print("failed here: " , fields)
        print(fields[2].text)
        break
    

    

