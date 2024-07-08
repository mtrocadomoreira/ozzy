
# Get maximum of fields along time

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
