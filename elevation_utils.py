from http import client

# This function will get the elevation at any point in the US (though not all of Alaska)
def getElevation(latitude, longitude): 
	return USGS10mElev(latitude, longitude)

# I found this code to query the USGS elevation data at:
# https://gist.github.com/pyRobShrk/8df3a3c422fb1c88882a5e41b284349f
def USGS10mElev(lat,lon):
    usgs = client.HTTPConnection('ned.usgs.gov')
    usgs.request('GET','/epqs/pqs.php?x=%.6f&y=%.6f&units=FEET&output=xml'% (lon, lat))
    result = usgs.getresponse()
    if result.status == 200:
        xml = result.read()
        return float(xml[xml.find(b'<Elevation>')+11:xml.find(b'</Elevation>')-1])
    else: return xml

   