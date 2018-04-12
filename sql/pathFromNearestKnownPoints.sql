-- Define function that finds shortest path between 2 points given in EPSG:4326 coordinate reference.
CREATE OR REPLACE FUNCTION pathFromNearestKnownPoints(
    IN x1 numeric, IN y1 numeric,
    IN x2 numeric, IN y2 numeric,
    OUT geojson TEXT,
    OUT length FLOAT
)
RETURNS SETOF record AS
$BODY$
DECLARE
    final_query TEXT;
BEGIN
    final_query :=
        FORMAT( $$
            WITH
            dijkstra AS (
                SELECT *
                FROM pgr_dijkstra(
                    'SELECT gid AS id, source, target, cost FROM ways',
                    -- known source closest to actual source
                    (SELECT id FROM ways_vertices_pgr 
                        ORDER BY the_geom <-> ST_SetSRID(ST_Point(%1$s, %2$s), 4326) LIMIT 1),
                    -- known target closest to actual target
                    (SELECT id FROM ways_vertices_pgr
                        ORDER BY the_geom <-> ST_SetSRID(ST_Point(%3$s, %4$s), 4326) LIMIT 1))
            )
            SELECT
                ST_AsGeoJSON(ST_LineMerge(ST_Union(the_geom))) as geojson, SUM(length_m) as length
            FROM dijkstra JOIN ways ON dijkstra.edge = ways.gid;$$,
        x1,y1,x2,y2);
    RAISE notice '%', final_query;
    RETURN QUERY EXECUTE final_query;
END;
$BODY$
LANGUAGE 'plpgsql';

