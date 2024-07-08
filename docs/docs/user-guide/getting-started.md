
# Getting started


Below are a few simple examples of what you can do with ozzy:


:material-arrow-right: [Subtract two field components]()

:material-arrow-right: [Get maximum of fields along time]()

:material-arrow-right: [Plot histograms of particle data]()

:material-arrow-right: [Get phase space from particle data]()

:material-arrow-right: [Get charge density from particle data]()



## Subtract two field components

Let's assume we have the data for two components of the electromagnetic fields, $E_r$ and $B_\theta$, in a 2D cylindrical simulation.

=== "OSIRIS"
	```python
	import ozzy as oz
	e2_ds = oz.open('osiris', 'path/to/file/MS/FLD/e2/e2-000010.h5')
	b3_ds = oz.open('osiris', 'path/to/file/MS/FLD/b3/b3-000010.h5')
	print(e2_ds)
	``` 

=== "LCODE"

	```python
	import ozzy as oz
	e2_ds = oz.open('lcode', 'path/to/file/er00200.swp')
	b3_ds = oz.open('lcode', 'path/to/file/bf00200.swp')
	print(e2_ds)
	``` 

=== "Dummy data"

	```python
	import ozzy as oz
	import numpy as np

	# Create some dummy data
	x1 = np.linspace(0, 10, 100)
	x2 = np.linspace(-5, 5, 50)
	e2_data = np.random.rand(50, 100)
	b3_data = np.random.rand(50, 100)

	# Create the Datasets
	e2_ds = oz.Dataset({'e2': (['x2','x1'],e2_data)}, coords={'x1': x1, 'x2': x2}, pic_data_type='grid', data_origin='ozzy')
	b3_ds = oz.Dataset({'b3': (['x2','x1'],b3_data)}, coords={'x1': x1, 'x2': x2}, pic_data_type='grid', data_origin='ozzy')

	print(e2_ds)
	``` 
Right now we have two datasets (one for each field component). Since these data variables share the same axes ("coordinates" in xarray nomenclature), we can easily merge both datasets.

```python
import xarray as xr
fields = xr.merge([e2_ds,b3_ds])
print(fields)
```	

In this example we want to obtain the radial force associated with the electromagnetic fields of an axisymmetric plasma wave. In the normalized units used in most PIC codes, the radial force (on a positive particle) is defined simply as $W_r = E_r - B_\theta$. We can perform the subtraction and store the result as a new variable in the same dataset.

```python
fields['wr'] = fields['e2'] - fields['b3']
print(fields['wr'])
```

Afterwards, we can save the result as an HDF5 file.


```python
# We're leaving e2 and b3 aside
fields['wr'].ozzy.save('wr.h5')
```

## Get maximum of fields along time

Let's say we have a set of 2D data files for the $E_z$ field component spanning multiple simulation time steps.


=== "OSIRIS"
	```python
	import ozzy as oz
	ds = oz.open_series('osiris', 'path/to/file/MS/FLD/e1/e1-*.h5')
	print(ds)
	``` 

=== "LCODE"

	```python
	import ozzy as oz
	ds = oz.open_series('lcode', 'path/to/file/ez*.swp')
	print(ds)
	``` 

=== "Dummy data"

	```python
	import ozzy as oz
	import numpy as np

	# Create some dummy data
	x1 = np.linspace(0, 10, 100)
	x2 = np.linspace(-5, 5, 50)
	t = np.linspace(0, 1000, 20)
	data = np.random.rand(50, 100, 20)

	# Create a DataArray
	da = oz.DataArray(data, coords={'t': t, 'x1': x1, 'x2': x2}, dims=['x2','x1','t'], name='e1', pic_data_type='grid', data_origin='ozzy')

	print(da)
	``` 

Now we use [xarray.DataArray.max][] to get the maximum of the field component along both spacial dimensions, as a function of time.

=== "OSIRIS"
	```python
	max_t = ds['e1'].max(dim=['x1','x2'])
	print(max_t)
	``` 

=== "LCODE"

	```python
	max_t = ds['ez'].max(dim=['x1','x2'])
	print(max_t)
	``` 

=== "Dummy data"

	```python
	max_t = da.max(dim=['x1','x2'])
	print(max_t)
	``` 

Note how the output DataArray keeps the information about the time axis.


## Plot histograms of particle data

## Get phase space from particle data

## Get charge density from particle data


<!-- Hello blabla

<figure markdown="span">
	![Image title](https://dummyimage.com/600x400/){ width="300" }
	<figcaption>Image caption</figcaption>
</figure> -->