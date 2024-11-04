# CHANGELOG

<!--start-docs-->


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

### Breaking

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



### Bug Fixes

* [`0e0f1f2`](https://github.com/mtrocadomoreira/ozzy/commit/0e0f1f25cb8e1ba203995b2b7c8cc007ecbbf1b9): Fix attribute assignment in `bin_into_grid` and reorder dimensions after binning (for chunking and performance)






* [`9674d63`](https://github.com/mtrocadomoreira/ozzy/commit/9674d638d8c98b7cfbefe4af021ec28ae9c5adff): Fix bug where `open_compare` was printing out &#34;reading files&#34; even when it had found no files






### Documentation

* [`28e05c2`](https://github.com/mtrocadomoreira/ozzy/commit/28e05c22f5e153482030258ba265b7c7649b7993): Change template for automatic changelog generation






* [`d91795b`](https://github.com/mtrocadomoreira/ozzy/commit/d91795b8a0eb531013abf7fd842ac04ae88b3eb2): Add `plot_func` argument to `movie` docstring






* [`2a97bb6`](https://github.com/mtrocadomoreira/ozzy/commit/2a97bb6cacbee5adad178347ebac69ca47d721ff): Add release notes to website, create custom changelog template






### Features

* [`10abc79`](https://github.com/mtrocadomoreira/ozzy/commit/10abc79ae06d6bba0b78f1fa48b02868943897ef): Publish package on pypi with as `ozzy-pic`






* [`361f9c0`](https://github.com/mtrocadomoreira/ozzy/commit/361f9c04e4160bda67784bee430f9f067fdf45fe): Add function to get beam emittance






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






