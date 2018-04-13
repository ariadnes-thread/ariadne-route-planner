import osmapi
import matplotlib
matplotlib.use('TkAgg')
import smopy


def pull_image_tile(lat_lng):
	map = smopy.Map(lat_lng, z=4)
	#map.show_ipython()

	x, y = map.to_pixels(48.86151, 2.33474)
	ax = map.show_mpl(figsize=(8, 6))
	ax.plot(x, y, 'or', ms=10, mew=2);


pull_image_tile([42., -1., 55., 3.])
