from setuptools import find_packages, setup

requirements = [
    "pandas",
    "seaborn",
    "flox",
    "xarray",
    "h5py",
    "h5netcdf",
    "dask",
    "matplotlib",
]  # This could be retrieved from requirements.txt
# Package (minimal) configuration
setup(
    name="ozzy",
    version="0.0.0",
    description="PIC simulation data analysis for the lazy and impatient",
    url="https://github.com/mtrocadomoreira/ozzy",
    author="Mariana Moreira",
    package_dir={"": "src"},
    packages=find_packages(),  # __init__.py folders search
    install_requires=requirements,
    include_package_data=True,
)
