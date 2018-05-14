from http import client
import math

metersPerFoot = 0.3048
radiansPerDegree = math.pi / 180
earthRadius = 6371000

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

# Calculate the elevation change between two latitude / longitude coordinates
def elevationChange(startLat, startLon, endLat, endLon):
	return getElevation(endLat, endLon) - getElevation(startLat, startLon)

# Calculate the distance in feet between two latitude / longitude coordinates
# uses the haversine formula as discussed here: https://www.movable-type.co.uk/scripts/latlong.html
def distanceBetween(startLat, startLon, endLat, endLon):
	radStartLat = degreesToRadians(startLat)
	radStartLon = degreesToRadians(startLon)
	radEndLat = degreesToRadians(endLat)
	radEndLon = degreesToRadians(endLon)
	a = math.pow(math.sin((radEndLat - radStartLat) / 2), 2) + math.cos(radStartLat) * math.cos(radEndLat) * math.pow(math.sin((radEndLon - radStartLon) / 2) , 2)
	c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
	distance = earthRadius * c
	return metersToFeet(distance)
# note: I tested this for small distances around Caltech.  For the same coordinates, google says 499 feet,
# and our calculation gives 508 feet, so it's a very small difference

# Calculate the slope (elevation change / distance) between two latitude / longitude coordinates
# This assumes a simple line between the two points
def slopeBetweenSimple(startLat, startLon, endLat, endLon):
	return elevationChange(startLat, startLon, endLat, endLon) / distanceBetween(startLat, startLon, endLat, endLon)

# Sample the elevations between two coordinates, and return as an array (for use in a visual of the elevation changes along the route)
def sampleElevations(startLat, startLon, endLat, endLon, numPoints = 10):
	elevations = []
	dlat = (endLat - startLat) / (numPoints - 1)
	dlon = (endLon - startLon) / (numPoints - 1)
	lat = startLat
	lon = startLon

	for i in range(numPoints):
		elevations += [getElevation(lat, lon)]
		lat += dlat
		lon += dlon

	return elevations


# Conversion utility functions:
def feetToMeters(feet):
	return feet * metersPerFoot;

def metersToFeet(meters):
	return meters / metersPerFoot;

def degreesToRadians(degrees):
	return degrees * radiansPerDegree

def radiansToDegrees(degrees):
	return degrees / radiansPerDegree

# # Test of functionality, in the area around Caltech
# print(getElevation(34.1377, -118.1253)) # should be about 765
# print(degreesToRadians(180)) # should be pi
# print(feetToMeters(1)) # should be 0.3048
# print(distanceBetween(34.141365, -118.122908, 34.140965, -118.124518)) # should be about 500ft
# print(elevationChange(34.141365, -118.122908, 34.140965, -118.124518)) # should be about 1ft
# print(slopeBetweenSimple(34.141365, -118.122908, 34.140965, -118.124518)) # should be about 0.001

# # should be a list of 10 increasing elevations, from about 790 to about 1800 ft (9 intervals)
# print(sampleElevations(34.140374, -118.132294, 34.204025, -118.130679)) 
# # should be a list of 19 increasing elevations, from about 790 to about 1800 ft, that are the same as the above values but with twice the resolution (18 intervals)
# print(sampleElevations(34.140374, -118.132294, 34.204025, -118.130679, 19)) 


