import os
import json
import psycopg2
import networkx as nx

# Import app config
config = json.load(open('config.json'))

# Setup `psycopg` connection, http://initd.org/psycopg/docs/usage.html
conn = psycopg2.connect(
    host=config.get('dbHost'),
    dbname=config.get('dbName'),
    user=config.get('dbUser'),
    password=config.get('dbPass'),
    port=config.get('dbPort')
)
cur = conn.cursor()

print('Testing GIS DB connection...')
cur.execute('SELECT 1')
cur.fetchone()
print('Test successful!')

G = nx.Graph()

print('\nFetching nodes...')
cur.execute('SELECT osm_id, lat, lon FROM ways_vertices_pgr;')
nodes = cur.fetchall()
pos = []
for node in nodes:
    node_id = node[0]
    node_lat = float(node[1])
    node_lng = float(node[2])
    G.add_node(node_id, lat=node_lat, lng=node_lng)
print('Done! Processed {} node(s).'.format(len(nodes)))

print('\nFetching edges...')
cur.execute('SELECT source_osm, target_osm FROM ways;')
edges = cur.fetchall()
for edge in edges:
    edge_source = edge[0]
    edge_target = edge[1]
    G.add_edge(edge_source, edge_target)
print('Done! Processed {} edge(s).'.format(len(edges)))

output_file = os.path.join(os.path.dirname(__file__), 'network.graphml')
nx.write_graphml(G, output_file)

# Commit changes to the database (if any) and close connection
conn.commit()
cur.close()
conn.close()
