
# Getting started

Below are a few simple examples of what you can do with ozzy.

## Grid data

??? example "Subtract two field components"

	We load two sample OSIRIS files corresponding to the $E_r$ and $B_\theta$ components of the electromagnetic fields in a 2D cylindrical simulation. 

	```python
	import ozzy as oz
	e2_ds = oz.open('osiris', e2_file)
	b3_ds = oz.open('osiris', b3_file)
	e2_ds
	#
	``` 
	Right now we have two datasets (one for each field component). But since each dataset may contain several variables, and since these fields share the same coordinates, we can easily merge both datasets.

	```python
	import xarray as xr
	fields = xr.merge([e2_ds,b3_ds])
	fields
	#
	```	
	In this example we want to obtain the radial force associated with the electromagnetic fields of an axisymmetric plasma wave. In OSIRIS normalized units, the radial force (on a positive particle) is defined simply as $W_r = E_r - B_\theta$. We can perform the subtraction and store the result as a new variable in the same dataset.

	```python
	fields['wr'] = fields['e2'] - fields['b3']
	fields['wr']
	#
	```

	Afterwards, we can save the result as an HDF5 file.


	```python
	# we're leaving e2 and b3 aside
	fields['wr'].ozzy.save('wr.h5')
	```

	<!-- TODO: check this -->
	!!! info

		Note that the structure of the saved HDF5 file does not match the OSIRIS file structure. It instead follows xarray's NetCDF logic.






??? example "Get maximum of fields along time"


## Particle data

??? example "Plot histograms of particle data"

??? example "Get phase space from particle data"

??? example "Get charge density from particle data"


<!-- Hello blabla

<figure markdown="span">
	![Image title](https://dummyimage.com/600x400/){ width="300" }
	<figcaption>Image caption</figcaption>
</figure> -->