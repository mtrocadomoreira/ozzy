# CHANGELOG

<!--start-docs-->


## Version 2.0.4 

Released 11-11-2025 

### Bug Fixes

* [`1ddd4af`](https://github.com/mtrocadomoreira/ozzy/commit/1ddd4afbcca8941bd20466339bea841290b5fc4f): Badly formulated if-statement in emittance functions







## Version 2.0.3 

Released 11-11-2025 

### Bug Fixes

* [`577afa7`](https://github.com/mtrocadomoreira/ozzy/commit/577afa71e5733a464203af5b293e8904aa7eb095): Improve handling of variable labels in ´get_emittance´






### Documentation

* [`176bc05`](https://github.com/mtrocadomoreira/ozzy/commit/176bc0579e38db9afa44a53e830f2d50088e40ad): Formatting issue in one of documentation pages






* [`928cb92`](https://github.com/mtrocadomoreira/ozzy/commit/928cb9253aba30361c5b44281b77e5bc218c69b6): Add icon to mark external links, and open these links in new tab by default






* [`6e285d2`](https://github.com/mtrocadomoreira/ozzy/commit/6e285d204c2a94fc43336a8f61af84014bbc7df0): Add information about backend-specific arguments in the `ozzy` open functions






### Refactoring

* [`3131e16`](https://github.com/mtrocadomoreira/ozzy/commit/3131e1667b60312019288965c8b80648f788190e): Change how emittance is handled for axisymmetric geometry in `get_slice_emittance`, update docstring






* [`afb8ca4`](https://github.com/mtrocadomoreira/ozzy/commit/afb8ca40509bbb916e0823dd283e29aca97e81c0): Change how emittance is handled for axisymmetric in `get_emittance`, update docstring







## Version 2.0.2 

Released 06-11-2025 

### Bug Fixes

* [`1e3d55d`](https://github.com/mtrocadomoreira/ozzy/commit/1e3d55da09fafc62f75a960f9c5cc2974657f600): Bug that was preventing lcode files like `emaxf.dat` to be read






### Documentation

* [`c966cd4`](https://github.com/mtrocadomoreira/ozzy/commit/c966cd4eabdd93aec3cee762f2b5829b1e0a6355): Correct typo in docstring of `lcode_backends.convert_q`






### Refactoring

* [`70da7e3`](https://github.com/mtrocadomoreira/ozzy/commit/70da7e3ff7dbb7e5d9a43e90640538669f5753dc): Add argument to `xarray.concat` and `xarray.merge` calls due to xarray `futurewarning`



    Add the argument `join="outer"` explicitly when call `xarray.concat` to avoid getting an error in the future, when xarray changes the default value of `join` from `"outer"` to `"exact"`.
    See warning:
    ```
    FutureWarning: In a future version of xarray the default value for join will change from join='outer' to join='exact'.
    ```



## Version 2.0.1 

Released 05-09-2025 

### Bug Fixes

* [`bcd0bf6`](https://github.com/mtrocadomoreira/ozzy/commit/bcd0bf66c0fdb4343e20d1f86a40119ede68ffe5): Bug in helper function `ozzy.utils.prep_file_input` was preventing ozzy from finding files to open, raising `filenotfounderror`







## Version 2.0.0 

Released 29-08-2025 

### Bug Fixes

* [`6404186`](https://github.com/mtrocadomoreira/ozzy/commit/6404186acba85245e711428be7e4f1d1936ca111): Fix bug in `bin_into_grid` (and `get_phase_space`, which depends on it) for axisymmetric data



    This bug was possibly producing incorrect results when `bin_into_grid` or `get_phase_space` were called on an axisymmetric particle dataset, and where **all** of these conditions were met:

    - `r_var` was provided as an argument (other than `None`)

    - for `get_phase_space`, the argument `axisym` was set to `True`

    - the radial variable `r_var` was **not** part of either the `axes_ds` (for `bin_into_grid`) or `vars` (for `get_phase_space`) argument


### Documentation

* [`4ff3d2e`](https://github.com/mtrocadomoreira/ozzy/commit/4ff3d2efcb1f3c18e20451a530b9f5b92c7a0c73): Restructure the &#34;data object methods&#34; section of the code reference and other small updates






* [`6cec2a7`](https://github.com/mtrocadomoreira/ozzy/commit/6cec2a7b1b106da15de204ae05bcbc0249747e7b): Improve example of `convert_q` method






### Features

* [`7855a10`](https://github.com/mtrocadomoreira/ozzy/commit/7855a10f8a14c1e487f834a76585503d16b4f355): Add function to get the weighted median of some variable in a particle dataset



    Particle data from PIC codes is often weighted (often in the form of an individual macroparticle "charge"), which means that the calculation of a median value is not as straightforward as for other discrete and unweighted data. This method ensures that a median value can be calculated correctly, taking the macroparticle weights into account.

    This function can be called as a particle method, e.g. `part_ds.ozzy.get_weighted_mean`, where `part_ds` is an ozzy particle Dataset object (i.e., with attribute `pic_data_type = "part"`).


### Refactoring

* [`cb5973f`](https://github.com/mtrocadomoreira/ozzy/commit/cb5973f56b946d364533968ab48a5eca18f88a9e): Make all arguments for variable names consistent



    Some functions have input arguments where the name of a certain variable can be specificied. The naming for this type of argument has been made consistent across the code. For example, the arguments `time_dim` or `tvar` have been renamed to `t_var`.

    **Breaking change:** `TypeError` may be raised when some functions are called using the old argument names

    Please make sure to update your scripts with the new arguments (e.g. `w_var` instead of `wvar`).


* [`f668c5d`](https://github.com/mtrocadomoreira/ozzy/commit/f668c5d32c3707fa1723644cb6805e6c733d8b25): Add hidden method `_contains_datavars` to ozzy dataset objects to simplify input validation in other parts of the code



    Given a list of variable names, this method checks whether each variable exists in the Dataset as a data variable and raises a `KeyError` if it doesn't. This is useful when implementing new functions that require some data variables as input (for example `get_emittance` or `get_energy_spectrum`).



## Version 1.3.4 

Released 26-08-2025 

### Bug Fixes

* [`d3403f1`](https://github.com/mtrocadomoreira/ozzy/commit/d3403f1568ecc28e245537428b0c9aea17e8a3d0): Turn off `savefig.transparent` in default `rcparams` when using the `movie` function



    Each frame was previously being saved with a transparent background, which meant that the movies produced with `ozzy.plot.movie` were superimposing all of the frames.



## Version 1.3.3 

Released 29-07-2025 

### Bug Fixes

* [`3675499`](https://github.com/mtrocadomoreira/ozzy/commit/3675499ed05628cd6c658e68dd8cad870aa05410): Correct a bug in `get_energy_spectrum`







## Version 1.3.2 

Released 29-07-2025 

### Bug Fixes

* [`6effaee`](https://github.com/mtrocadomoreira/ozzy/commit/6effaee671c8b5f773f72091b4bbd1b355330dbf): Correct a couple of bugs in the calculation of the normalized emittance







## Version 1.3.1 

Released 23-07-2025 

### Bug Fixes

* [`8a02447`](https://github.com/mtrocadomoreira/ozzy/commit/8a024471b036891ccc4113470cbe0397148ff637): Error when trying to save the output of `get_slice_emittance` or `get_energy_spectrum`



    These particle methods use a special binning and grouping function (`flox.xarray.xarray_reduce`) for increased efficiency. However, this function creates a coordinate for the binned variable with the data type `pandas.Interval`, which makes it impossible to save the data with `ds.ozzy.save`. The binned coordinate is now converted into a normal `numpy` array, using the midpoints of each interval element.


### Documentation

* [`3242468`](https://github.com/mtrocadomoreira/ozzy/commit/32424684c24559c3955fc75fdef0bf6d604bac77): Add docstring to new utility function `convert_interval_to_mid`






### Refactoring

* [`4fc223d`](https://github.com/mtrocadomoreira/ozzy/commit/4fc223d76a4fc8305f54e013ed751367a0ac1ba6): Add timing information to several particle methods



    The particle methods get_phase_space, get_emittance, get_slice_emittance, get_energy_spectrum now print the time taken to complete.


* [`ef3420f`](https://github.com/mtrocadomoreira/ozzy/commit/ef3420f2eef1db5631561ed216f2eab7be3d42ab): Add timing information to several particle methods



    The particle methods `get_phase_space`, `get_emittance`, `get_slice_emittance`, `get_energy_spectrum` now print the time taken to complete.



## Version 1.3.0 

Released 16-07-2025 

### Bug Fixes

* [`2f8993b`](https://github.com/mtrocadomoreira/ozzy/commit/2f8993b4b220753736e648e20c72fc6aa614610d): Use absolute value of weight variable for `ozzy.plot.hist` and `ozzy.plot.hist_proj`



    The weighting variable in data objects is often a charge (e.g. `do['q']`), which means that it has a charge sign. This would show up in histograms as negative counts.


* [`ade7881`](https://github.com/mtrocadomoreira/ozzy/commit/ade788157a9372e66c1a52a87ab5e5202e64aa29): Accept filenames for beamfiles (and plasma and fields files) with more flexible patterns



    Now accepts the regex filename pattern `"beamfile\w*\.bin"` instead of `"beamfile.bin"`. The same applies to `plasma.bin` and `fields.bin` files.

    _Before:_

    ✅ `beamfile.bin`

    ❌ `beamfile_changed.bin`

    ❌ `beamfile2.bin`

    _Now:_

    ✅ `beamfile.bin`

    ✅ `beamfile_changed.bin`

    ✅ `beamfile2.bin`


* [`cdf5a87`](https://github.com/mtrocadomoreira/ozzy/commit/cdf5a87941b323f6a73cd0faa10d5759936639e0): Bug in `bin_into_grid` where the time dimension was hardcoded as `&#34;t&#34;`






### Documentation

* [`411f68d`](https://github.com/mtrocadomoreira/ozzy/commit/411f68dbb44607719a3a4124618e5dfd78332d47): Hide toc sidebar in homepage of documentation while keeping the margins



    Solution adopted from this [StackOverflow answer](https://stackoverflow.com/a/79647644).


* [`8e3538f`](https://github.com/mtrocadomoreira/ozzy/commit/8e3538f11dca89b1fbb2b2c0b9ce6293a75ff1d7): Update changelog manually






### Features

* [`cfa8949`](https://github.com/mtrocadomoreira/ozzy/commit/cfa894900d356b1a5f0e037b1d0cdecd29980ba3): Add energy spectrum calculation



    Add `get_energy_spectrum` method to particle datasets, which calculates energy histograms with proper binning and attribute handling. See documentation for examples of usage.


* [`a542991`](https://github.com/mtrocadomoreira/ozzy/commit/a5429918859f4e5bb8a46e2f71771c92580ca8c6): Add method to get the slice emittance `get_slice_emittance`



    Includes some changes to the `get_emittance` method and its documentation. It is now possible to choose between the normalized and geometric emittance, for example.


### Refactoring

* [`10eef35`](https://github.com/mtrocadomoreira/ozzy/commit/10eef350fa8363496657541cb10f71bff61f5b6a): The output of `get_slice_emittance` now adopts any label and units attributes provided with `axis_ds`






* [`4d876ca`](https://github.com/mtrocadomoreira/ozzy/commit/4d876cacb76214112ea7eb3a3ae704349b50e7f1): Add utility function to insert string at a given index






* [`fb3cc12`](https://github.com/mtrocadomoreira/ozzy/commit/fb3cc12a9b03b7def8c16b7d278475267d8432a0): Add `time_dim` and `weight_var` arguments in `get_phase_space`



    The function `get_phase_space` calls `bin_into_grid`, which was setting some defaults for the `time_dim` and `weight_var` arguments. This is not the case anymore.


* [`f0e45a7`](https://github.com/mtrocadomoreira/ozzy/commit/f0e45a73401fc8a25959562c58bd9a6521938f6f): Add `time_dim` and `weight_var` arguments in `get_phase_space`



    The function `get_phase_space` calls `bin_into_grid`, which was setting some defaults for the `time_dim` and `weight_var` arguments. This is not the case anymore.



## Version 1.2.10 

Released 23-06-2025 

### Bug Fixes

* [`3953907`](https://github.com/mtrocadomoreira/ozzy/commit/3953907884a089a666ae3255f95624dbf521ee64): Use absolute value of weight variable for `ozzy.plot.hist` and `ozzy.plot.hist_proj`



    The weighting variable in data objects is often a charge (e.g. `do['q']`), which means that it has a charge sign. This would show up in histograms as negative counts.


### Documentation

* [`0e9829a`](https://github.com/mtrocadomoreira/ozzy/commit/0e9829a6296e9f82388b365770d0b29b6ef0de54): Update changelog manually







## Version 1.2.9 

Released 20-06-2025 

### Bug Fixes

* [`f25affb`](https://github.com/mtrocadomoreira/ozzy/commit/f25affb685eada6b81a775ef3f8bd26f96cab236): Accept filenames for beamfiles (and plasma and fields files) with more flexible patterns



    Now accepts the regex filename pattern `"beamfile\w*\.bin"` instead of `"beamfile.bin"`. The same applies to `plasma.bin` and `fields.bin` files.

    _Before:_

    ✅ `beamfile.bin`

    ❌ `beamfile_changed.bin`

    ❌ `beamfile2.bin`

    _Now:_

    ✅ `beamfile.bin`

    ✅ `beamfile_changed.bin`

    ✅ `beamfile2.bin`



## Version 1.2.8 

Released 20-06-2025 

### Bug Fixes

* [`4cc2da9`](https://github.com/mtrocadomoreira/ozzy/commit/4cc2da92663de208d1ae54a7d9b5e82b7f422073): Bug in `bin_into_grid` where the time dimension was hardcoded as `&#34;t&#34;`







## Version 1.2.7 

Released 23-05-2025 

### Bug Fixes

* [`741f0af`](https://github.com/mtrocadomoreira/ozzy/commit/741f0af0406b8356b9d681ea200159024683f7d0): Ability to use paul tol&#39;s reversed colormaps by appending `&#39;_r&#39;`






* [`d5bcdcb`](https://github.com/mtrocadomoreira/ozzy/commit/d5bcdcbccc4f74dbe9a0d2bcbc0ac4b0d7453d46): Assign `dtype` to concatenated data before chunking







## Version 1.2.6 

Released 08-05-2025 

### Bug Fixes

* [`d5d84f2`](https://github.com/mtrocadomoreira/ozzy/commit/d5d84f2870216cec7f8cc2696aa51fd8041b22be): Make sure that raw files containing no particles at all can still be assigned times and concatenated






* [`824cfed`](https://github.com/mtrocadomoreira/ozzy/commit/824cfed0ae8dcfbc5e86f3e5fb5ddc3e482992b2): Bug for raw files with no particle tag data







## Version 1.2.5 

Released 30-04-2025 

### Bug Fixes

* [`08ad9a6`](https://github.com/mtrocadomoreira/ozzy/commit/08ad9a60134874734f23d314bfa2ff1ee2d84e49): Fix bug that was causing an error when `hist` or `hist_proj` were called with `weight_var = none`







## Version 1.2.4 

Released 30-04-2025 

### Bug Fixes

* [`89eac7e`](https://github.com/mtrocadomoreira/ozzy/commit/89eac7e51d660fa4a36cc2c642491f11d7e1b398): Change algorithm so that spatially averaged (`savg`) grid data can be read






### Refactoring

* [`83b988e`](https://github.com/mtrocadomoreira/ozzy/commit/83b988eb439dab23a55fd69a514c54f366503b4d): Tweaked some parameters in `local_maxima_and_zero_crossings` to improve peak and zero finding






* [`0ff220f`](https://github.com/mtrocadomoreira/ozzy/commit/0ff220f75386d8b0a8bb68c7234ba7999ea7046a): Better formatting of progress bar in `vphi_from_fit`






* [`a899159`](https://github.com/mtrocadomoreira/ozzy/commit/a89915974e6dc8b2f6b4a366e1af4469fadd082d): Minor improvements to the `vphi_from_fit` function







## Version 1.2.3 

Released 14-04-2025 

### Bug Fixes

* [`92a2ed0`](https://github.com/mtrocadomoreira/ozzy/commit/92a2ed0231395c0c165cf25fae4d6015ceb89c93): Bug in `ozzy.plot.hist` and `ozzy.plot.hist_proj` for weighted data







## Version 1.2.2 

Released 09-04-2025 

### Bug Fixes

* [`1319ddf`](https://github.com/mtrocadomoreira/ozzy/commit/1319ddf50aadba601b00c5fcfa0b1c96f0d2e1c4): Typo was preventing `ozzy.statistics` from being imported







## Version 1.2.1 

Released 09-04-2025 

### Bug Fixes

* [`57daddd`](https://github.com/mtrocadomoreira/ozzy/commit/57dadddf1c8f04fe8837be727f6e6cd2494b373b): Bug in `local_maxima_and_zero_crossings`






### Documentation

* [`f4700b4`](https://github.com/mtrocadomoreira/ozzy/commit/f4700b4a183b1818e89206e5e3ea505dec92dbcd): Correct typos in docstring for `ozzy.fields.local_maxima_and_zero_crossings`







## Version 1.2.0 

Released 03-04-2025 

### Features

* [`454aeee`](https://github.com/mtrocadomoreira/ozzy/commit/454aeeeae6a40a699ae7c3dfca5e767769ef61bf): Add function to find local field maxima and zero crossings







## Version 1.1.2 

Released 17-02-2025 

### Bug Fixes

* [`46d59fc`](https://github.com/mtrocadomoreira/ozzy/commit/46d59fcc5236b4f79f0c44ccc550b28bad3f5ae2): Trigger new release to publish python-3.13-compatible update to pypi







## Version 1.1.1 

Released 17-02-2025 

### Bug Fixes

* [`6066a3f`](https://github.com/mtrocadomoreira/ozzy/commit/6066a3fc3dd7bfe8a5dac1413713bc1bce42abe7): Update package dependencies so that package works with python 3.13







## Version 1.1.0 

Released 17-02-2025 

### Documentation

* [`a156af7`](https://github.com/mtrocadomoreira/ozzy/commit/a156af7dff24e2217eb0d8afece365c811a78ecf): Instruct users to use the function `ozzy.utils.axis_from_extent` to create the axes dataset required for `bin_into_grid`






### Features

* [`7c39207`](https://github.com/mtrocadomoreira/ozzy/commit/7c392077b1f0f54e76963cfd99614b0239138c7f): Add functions to plot distributions of particle data



    Add `ozzy.plot.hist` and `ozzy.plot.hist_proj` to easily plot density distributions (histograms) of particle data, taking advantage of the seaborn functions [`seaborn.histplot`](https://seaborn.pydata.org/generated/seaborn.histplot.html) and [`seaborn.jointplot`](https://seaborn.pydata.org/generated/seaborn.jointplot.html).

    Previously it would have been necessary to bin the data first, and then plot, e.g.:
    ```python
    import ozzy as oz
    import ozzy.plot as oplt
    # A particle data Dataset
    ds = oz.Dataset(..., pic_data_type="part")
    ds_ps = ds.ozzy.get_phase_space(["p2", "x2"])
    ds_ps["rho"].plot()
    ```
    While now the following code is enough:
    ```python
    import ozzy as oz
    import ozzy.plot as oplt
    ds = oz.Dataset(..., pic_data_type='part')
    oplt.hist(ds, x="x2", y="p2")
    ```


### Refactoring

* [`703dfd3`](https://github.com/mtrocadomoreira/ozzy/commit/703dfd33f8c071a252a5525cc86323efe50dc3ca): Change `ozzy.plot` defaults to display a plot grid







## Version 1.0.9 

Released 28-01-2025 

### Bug Fixes

* [`a3cfe10`](https://github.com/mtrocadomoreira/ozzy/commit/a3cfe10f77172817294f7330690d665a7a1a71a9): One argument of `set_attr_if_exists` was missing its default value, which was throwing an error e.g. when `ds.ozzy.save` was called







## Version 1.0.8 

Released 24-01-2025 

### Bug Fixes

* [`83329ef`](https://github.com/mtrocadomoreira/ozzy/commit/83329ef6253cfcfb652229b522bc097aa45898e7): Fft method was throwing error due to data being a chunked dask array






### Documentation

* [`85a5f71`](https://github.com/mtrocadomoreira/ozzy/commit/85a5f7125310c90b245a0b624b07784123418085): Small formatting corrections







## Version 1.0.7 

Released 26-11-2024 

### Bug Fixes

* [`48d0b14`](https://github.com/mtrocadomoreira/ozzy/commit/48d0b14622414cea5005699e6511f85393558544): Fix bug that would throw error when using `open_compare` with multiple backends and with backend-specific keyword arguments






### Documentation

* [`25b11d8`](https://github.com/mtrocadomoreira/ozzy/commit/25b11d86a7b349ef9c22d58948741383dbd4b88d): Disable [instant loading](https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#instant-loading) since this causes the feedback widget to only show after reloading the page






* [`e2c93ce`](https://github.com/mtrocadomoreira/ozzy/commit/e2c93ce354c3f6b01599dfecee05c785872d218d): Update installation instructions (now available on `conda-forge`) and update package dependencies (especially `makedocs-material`)







## Version 1.0.6 

Released 13-11-2024 

### Bug Fixes

* [`65c7549`](https://github.com/mtrocadomoreira/ozzy/commit/65c7549571e5130dac7656eb055d854ea936e4b8): Expression with double quotes inside double quotes was throwing an error for python 3.10







## Version 1.0.5 

Released 13-11-2024 

### Bug Fixes

* [`2c5fa8e`](https://github.com/mtrocadomoreira/ozzy/commit/2c5fa8eb4c939c17143ad80d8c3faf22e1eb2aae): Remove obsolete argument for `backend.parse_data` that was being called from `ozzy.open_compare` and raising an error






### Documentation

* [`60afa7d`](https://github.com/mtrocadomoreira/ozzy/commit/60afa7d34ca879633c0d650242b8bd1749b41a77): Fix some broken links after update







## Version 1.0.4 

Released 12-11-2024 

### Bug Fixes

* [`5cd488c`](https://github.com/mtrocadomoreira/ozzy/commit/5cd488cbaf6819eabe91cf75e4d16c7bfd1ae3ff): Fix error thrown by `bin_into_grid` when called on a data object that didn&#39;t contain a `&#39;t&#39;` coordinate






* [`776a1a2`](https://github.com/mtrocadomoreira/ozzy/commit/776a1a2f0e6754aa4a0aaf2d7a5fda7b9bd91416): Fix missing-argument error when trying to read `beamfile.bin` files






### Documentation

* [`b43f5dc`](https://github.com/mtrocadomoreira/ozzy/commit/b43f5dcd8f169e7f13e358e4baf115b518be7044): Update documentation






* [`6c726a5`](https://github.com/mtrocadomoreira/ozzy/commit/6c726a56eba8a465246a5df1c6805e61b979edaa): Update &#34;installation&#34; and &#34;getting started&#34; page






* [`1bf9a95`](https://github.com/mtrocadomoreira/ozzy/commit/1bf9a954efc837d543557360dab6dddf7ca4db42): Change heading formatting of changelog template






### Refactoring

* [`825b7ab`](https://github.com/mtrocadomoreira/ozzy/commit/825b7abbe60d9876d6a4c260f8cb39c0882deaaf): Change how backend-specific arguments are passed from the `open` functions to each backend (easier to extend)







## Version 1.0.3 

Released 04-11-2024 

### Documentation

* [`1c50582`](https://github.com/mtrocadomoreira/ozzy/commit/1c505822c1096fb0d6bf1c3a9ff390ff84f48216): Correct changelog template







## Version 1.0.2 

Released 04-11-2024 

### Documentation

* [`2d1afe0`](https://github.com/mtrocadomoreira/ozzy/commit/2d1afe079632a6ef7188378746f55bc4f1482ddc): Update installation instructions







## Version 1.0.1 

Released 04-11-2024 

### Bug Fixes

* [`0e0f1f2`](https://github.com/mtrocadomoreira/ozzy/commit/0e0f1f25cb8e1ba203995b2b7c8cc007ecbbf1b9): Fix attribute assignment in `bin_into_grid` and reorder dimensions after binning (for chunking and performance)






* [`9674d63`](https://github.com/mtrocadomoreira/ozzy/commit/9674d638d8c98b7cfbefe4af021ec28ae9c5adff): Fix bug where `open_compare` was printing out &#34;reading files&#34; even when it had found no files






### Documentation

* [`28e05c2`](https://github.com/mtrocadomoreira/ozzy/commit/28e05c22f5e153482030258ba265b7c7649b7993): Change template for automatic changelog generation






* [`d91795b`](https://github.com/mtrocadomoreira/ozzy/commit/d91795b8a0eb531013abf7fd842ac04ae88b3eb2): Add `plot_func` argument to `movie` docstring






* [`2a97bb6`](https://github.com/mtrocadomoreira/ozzy/commit/2a97bb6cacbee5adad178347ebac69ca47d721ff): Add release notes to website, create custom changelog template






### Features

* [`10abc79`](https://github.com/mtrocadomoreira/ozzy/commit/10abc79ae06d6bba0b78f1fa48b02868943897ef): Publish package on pypi with as `ozzy-pic`






* [`0d2020a`](https://github.com/mtrocadomoreira/ozzy/commit/0d2020a3bb273ff34208dd9b3417c7e1948f2b2f): Add function to get beam emittance






* [`1ac93ae`](https://github.com/mtrocadomoreira/ozzy/commit/1ac93ae564719ec6c9c4b4af09535b32fcf81d28): Add function to create an interactive animation using `hvplot`






* [`3540a8e`](https://github.com/mtrocadomoreira/ozzy/commit/3540a8e7c60e83beb29dc9d19a484aa28e1b42ed): Make `movie` more customisable by having a function argument that can edit the plot at each frame






* [`dd58a21`](https://github.com/mtrocadomoreira/ozzy/commit/dd58a21e42fdb6730e1437a434989fff24c66992): Add co-moving variables such as `x1_box` to particle data as well






### Performance Improvements

* [`e67f696`](https://github.com/mtrocadomoreira/ozzy/commit/e67f696fa3c97af7f4837b2d3a5e569b220ac3ff): Reorder and rechunk dimensions of data after binning in `bin_into_grid`






### Refactoring

* [`0e98bbb`](https://github.com/mtrocadomoreira/ozzy/commit/0e98bbb53b826628db562691513157ee644f4571): Harmonize the metadata of lcode particle data (momentum) to standard names and units, update docs and tests



    The third momentum component in LCODE particle data corresponds to either $p_z$ in Cartesian geometry or the angular momentum $L$ in axisymmetric/cylindrical geometry. This is now taken into account via the boolean parameter `axisym` (`True` by default). In cylindrical geometry the third momentum component is renamed and a new `'p3'` variable is added to the dataset, corresponding to $p_\theta = L / r$.

    In addition, all momenta in LCODE particle data are normalised to $m_e \ c$. The units are now converted to $m_\mathrm{sp} \ c$, using the charge-to-mass ratio in the data and the new argument `abs_q` (absolute value of the normalised bunch particle charge).


* [`d7da0c8`](https://github.com/mtrocadomoreira/ozzy/commit/d7da0c893acfe8d9eb22917dd4eb07643d92aa8f): Replace `statistics.parts_into_grid` with dataset method `bin_into_grid`



    Replace `statistics.parts_into_grid` with a Dataset method called `bin_into_grid` accessible to particle data (`pic_data_type = 'part'`).

    **Breaking change:** `statistics.parts_into_grid` does not work anymore

    Please replace the function `statistics.parts_into_grid` with the `ds.ozzy.bin_into_grid` method. As an example, the following code

    ```python
    import ozzy as oz
    import ozzy.statistics as stats
    import numpy as np

    particles = oz.Dataset(
        {
            "x1": ("pid", np.random.uniform(0, 10, 10000)),
            "x2": ("pid", np.random.uniform(0, 5, 10000)),
            "q": ("pid", np.ones(10000)),
        },
        coords={"pid": np.arange(10000)},
        attrs={"pic_data_type": "part"}
    )

    axes = oz.Dataset(
        coords={
            "x1": np.linspace(0, 10, 101),
            "x2": np.linspace(0, 5, 51),
        },
        attrs={"pic_data_type": "grid"}
    )

    binned = stats.parts_into_grid(particles, axes, r_var="x2")
    grid_data_axisym = particles.ozzy.bin_into_grid(axes, r_var="x2")
    ```
    should be replaced by

    ```python
    import ozzy as oz
    import numpy as np
    ...
    binned = particles.ozzy.bin_into_grid(axes, r_var="x2")
    ```


* [`5840bc4`](https://github.com/mtrocadomoreira/ozzy/commit/5840bc44884455dbe20508715e52a1cb4321773a): Make str_exists argument of get_attr_if_exists optional






* [`5d53830`](https://github.com/mtrocadomoreira/ozzy/commit/5d53830538f88959180e5762b6d4893855d16cc1): Use helper functions to handle dataarray attributes whenever possible







## Version 0.2.1 

Released 21-10-2024 

### Bug Fixes

* [`0c2bb5f`](https://github.com/mtrocadomoreira/ozzy/commit/0c2bb5f88ca717159a0cda2139615cbff3f7b983): Error is now raised when an invalid n0 argument is passed to convert_q






### Documentation

* [`426b187`](https://github.com/mtrocadomoreira/ozzy/commit/426b187550daa689faf24f429a723d33692bf5d9): Add feedback widget across pages






* [`7877d0e`](https://github.com/mtrocadomoreira/ozzy/commit/7877d0edc04c04895f1c3298ff2ddd28f66a26f7): Try to add umami analytics in different way






* [`3e62f7b`](https://github.com/mtrocadomoreira/ozzy/commit/3e62f7b76b4f0b1ee07fe803b363a46828ff91d4): Add umami analytics for documentation website






* [`ae7b7b3`](https://github.com/mtrocadomoreira/ozzy/commit/ae7b7b379f77f7766f98d3d502ab1b331eb022ec): Add black as project dependency for better formatting of code signatures in documentation






* [`0bd401b`](https://github.com/mtrocadomoreira/ozzy/commit/0bd401bd85f93aac6873a776460dabac622f8a15): Debug and small corrections






* [`29be6fd`](https://github.com/mtrocadomoreira/ozzy/commit/29be6fd2c45944b7e59e56582351bb168dc65de0): Change main blurb, include install instructions with git and poetry






### Refactoring

* [`a2d20bc`](https://github.com/mtrocadomoreira/ozzy/commit/a2d20bc7ba723f2175275a8c3be61a023a4e71e6): Add two helper functions to set dataarray attributes depending on whether they already exist or not, + unit tests for these functions







## Version 0.2.0 

Released 15-10-2024 

### Features

* [`b4b61c7`](https://github.com/mtrocadomoreira/ozzy/commit/b4b61c794b92ad71105cc3b7b3e8ce7d6f794b77): Save movies of ozzy plots







## Version 0.1.7 

Released 07-10-2024 

### Bug Fixes

* [`6fcd37d`](https://github.com/mtrocadomoreira/ozzy/commit/6fcd37da2e497f119969eec30cea933d4f5568f0): Get_phase_space bug fixes



    - no error when limits are set automatically and all quantity values are zero
    - make sure that axisymmetric geometry is taken into account correctly when the radius variable isn't being binned directly


* [`c12f766`](https://github.com/mtrocadomoreira/ozzy/commit/c12f766205346da546da2ab6bbdde1b6420f53e2): Correct units of particle momenta







## Version 0.1.6 

Released 30-09-2024 

### Bug Fixes

* [`96a7340`](https://github.com/mtrocadomoreira/ozzy/commit/96a734016ba1ae22f78fe73e6c4aaef9f5a2305d): Units in parts_into_grid are now fetched from raw_ds argument







## Version 0.1.5 

Released 23-09-2024 

### Performance Improvements

* [`d4d08a5`](https://github.com/mtrocadomoreira/ozzy/commit/d4d08a59979fcbc1a0cd15ed60ca2202ff752fad): Improve concatenation of tb files along time






### Refactoring

* [`1816b9b`](https://github.com/mtrocadomoreira/ozzy/commit/1816b9bd834aedd568ced1a699c5c65b44cdb634): Add commented todo&#39;s







## Version 0.1.4 

Released 18-09-2024 

### Bug Fixes

* [`6e84664`](https://github.com/mtrocadomoreira/ozzy/commit/6e84664fc63914c84a51285cad7f32e5eacf8988): Change momentum units






### Features

* [`de9520c`](https://github.com/mtrocadomoreira/ozzy/commit/de9520ce033c4bb835973175f0b81cd1891068b9): Scaffolding for emittance method






### Refactoring

* [`506f060`](https://github.com/mtrocadomoreira/ozzy/commit/506f060a08e18f543557acc8edefc75ddded3a23): Replace ~ with not






* [`9ce2c8a`](https://github.com/mtrocadomoreira/ozzy/commit/9ce2c8a171e036078c535172dab3a10382dea39c): Utils function to set attributes if they exist







## Version 0.1.3 

Released 17-09-2024 

### Bug Fixes

* [`022b0c4`](https://github.com/mtrocadomoreira/ozzy/commit/022b0c465d5bcaff80658910919ade6b88a07dd9): Change momentum units







## Version 0.1.2 

Released 17-09-2024 

### Bug Fixes

* [`d48785c`](https://github.com/mtrocadomoreira/ozzy/commit/d48785cc737cb874b692002a179416d03fc7c788): Change units of density in parts_into_grid






### Refactoring

* [`0bd8cc1`](https://github.com/mtrocadomoreira/ozzy/commit/0bd8cc1bcfeba8278fab803d7321f48ec483e94b): Change norm. units of q in particle data






* [`1c5d48e`](https://github.com/mtrocadomoreira/ozzy/commit/1c5d48ed97e508b5ae165a0cf9e319a47f4206a3): Add axisym argument to get_phase_space







## Version 0.1.1 

Released 13-08-2024 

### Bug Fixes

* [`fed8f27`](https://github.com/mtrocadomoreira/ozzy/commit/fed8f276a8ddb5969732e34b7f51c82c7b019465): Automatic extent calculation for phase space even when min = max






### Documentation

* [`1ef5d22`](https://github.com/mtrocadomoreira/ozzy/commit/1ef5d22b4f0c7e172eb2d3d16bbba582001448e7): Include zenodo reference






### Refactoring

* [`2d79f50`](https://github.com/mtrocadomoreira/ozzy/commit/2d79f50853de754baf930a05bc836c76f901c8f2): Utils function to set attributes if they exist







## Version 0.1.0 

Released 16-07-2024 

### Features

* [`109e196`](https://github.com/mtrocadomoreira/ozzy/commit/109e196a553ac923cb94005d06e283d72df68bbd): Set up cd of ozzy releases







## Version 0.0.1 

Released 16-07-2024 

### Bug Fixes

* [`8e5fabd`](https://github.com/mtrocadomoreira/ozzy/commit/8e5fabdf12c0cefc23b6c171f85416b42f256126): Use correct function to register colormap







## Version 0.0.0 

Released 16-07-2024 

### Documentation

* [`62db369`](https://github.com/mtrocadomoreira/ozzy/commit/62db3698c54a1b399a380ba4e83340805a64326e): Write plotting section






* [`9fb57d8`](https://github.com/mtrocadomoreira/ozzy/commit/9fb57d8d7e0ee7fa865e380599a7c049899e20b7): Write reading-files






* [`892ed52`](https://github.com/mtrocadomoreira/ozzy/commit/892ed52d5f0231c38af1a5a7fa2d3cfab04e950c): Add file save to quick example in getting started






* [`7c1fbd0`](https://github.com/mtrocadomoreira/ozzy/commit/7c1fbd0da84d4bfbb1facfe59148a1cce4b6e48e): Finish key concepts






* [`7272683`](https://github.com/mtrocadomoreira/ozzy/commit/727268359b61d4fafb0d811ff46f8b34a892601f): Work on getting started






* [`079304f`](https://github.com/mtrocadomoreira/ozzy/commit/079304f028e9f4703e548bfc6e8f393c84b3153c): Work on getting started






* [`2d96a10`](https://github.com/mtrocadomoreira/ozzy/commit/2d96a1082ef88b516e211cd2f2f090e98930d015): Key concepts






* [`afd1953`](https://github.com/mtrocadomoreira/ozzy/commit/afd1953e3c2df1009e069dc958802d495ca166b8): Write pages for each backend






* [`db3cd72`](https://github.com/mtrocadomoreira/ozzy/commit/db3cd72b56d2199da83cb1eeb700c3b6176483eb): Work on getting started






* [`c566890`](https://github.com/mtrocadomoreira/ozzy/commit/c566890fa782868c7f725f98fb750d984a8248db): Formatting + start getting started






* [`1ce0289`](https://github.com/mtrocadomoreira/ozzy/commit/1ce02895b5ec18ac925deaefa7d99308c67064ac): Activate section permalinks






* [`eb042d1`](https://github.com/mtrocadomoreira/ozzy/commit/eb042d1516c5e330f11254652ad8d8f01985c2a7): Activate git date plugin






* [`1401ba4`](https://github.com/mtrocadomoreira/ozzy/commit/1401ba454e9fe7e9c12392657dc573bf26ba9511): Small changes






* [`df428f2`](https://github.com/mtrocadomoreira/ozzy/commit/df428f22d83ad4fb7e56b32ccad64c1ae6e54dbf): Solve bugs






* [`3481bfb`](https://github.com/mtrocadomoreira/ozzy/commit/3481bfba1190e7a066c6d5ae211d6906f7d5e92a): Try to solve snippets issue






* [`4eb3b32`](https://github.com/mtrocadomoreira/ozzy/commit/4eb3b326ea5fc017b72909158875960646bb09aa): Try to solve snippets issue






* [`8cab692`](https://github.com/mtrocadomoreira/ozzy/commit/8cab69252d21a8c1aff9d872f06dbdb02d622bd0): Try to solve snippets issue






* [`0ecd710`](https://github.com/mtrocadomoreira/ozzy/commit/0ecd7109385025f822fde66ce2800e87da2b3098): Finish license and about
