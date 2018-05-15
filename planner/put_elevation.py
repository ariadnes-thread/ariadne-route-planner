import heapq
import itertools
import logging
import statistics
import random
from http import client
from typing import *

__all__ = ['OrienteeringRouter']

logger = logging.getLogger(__name__)

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

# Assuming that the elevation column already exists
# (I ran the following in DataGrip before running this python script)
# -- ALTER TABLE public.ways_vertices_pgr
# --     ADD elevation numeric(11,3)

def add_elevation_sql(conn):ß
    with conn.cursor() as cur:
        # Get the elevation data for each point in our database.
        # (This probably isn't the most efficient way to do this,
        # but it only has to be done once.)
        cur.execute(
            '''
            SELECT
              id, lat, lon, elevation
            FROM ways_vertices_pgr
            '''
        )
        data = cur.fetchall()
        for location in data:
            loc_id = location[0]
            lat = location[1]
            lon = location[2]
            elevation = getElevation(lat, lon)
            cur.execute(
                '''
                UPDATE ways_vertices_pgr
                    SET elevation = %s
                    WHERE id = %s
                ''', (elevation, loc_id)
            )
        print("finished")
        # This takes a while to run, so it prints out something when it is done
        conn.commit()
        cur.close()
        conn.close()
        return 0

def main():

    conn = db_conn.connPool.getconn()
    print(add_elevation_sql(conn))


if __name__ == '__main__':
    import db_conn

    main()
