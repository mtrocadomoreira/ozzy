
# Installation

Ozzy is a Python package. We recommend installing ozzy in its own virtual environment, since it depends on several other packages. If you're not familiar with Python or virtual environments, see our [guide to setting things up](virtual-environments.md).

Ozzy is available both on [PyPI](https://pypi.org/) (via `pip`) and on [conda-forge](https://conda-forge.org/) (via `conda` or `mamba`).

## Requirements

- Python >= 3.10

## with conda <small>(recommended)</small>

!!! note "Note about mamba"

    Feel free to replace the `conda` command with `mamba`. [Mamba](https://mamba.readthedocs.io/en/latest/index.html) is a faster version of the conda package manager, and is installed by default with [miniforge](https://github.com/conda-forge/miniforge).


After you have activated a new virtual environment, run:

```bash
conda install ozzy
```

## with pip

After you have activated a new virtual environment, run:

```bash
python3 -m pip install ozzy
```

## with git

If you want to have access to the latest version of ozzy before it has been released as a new package version, you can install it in "development mode".

First, go to a directory of your choice and clone the repository:
```bash
git clone https://github.com/mtrocadomoreira/ozzy.git
```

Then install the cloned repository with `pip` (the flag `-e` means that the package will be installed directly from the files):
```bash
python3 -m pip install -e ozzy
```

!!! note "Updating to the latest commit"
    Please bear in mind that you will have to update your local copy of ozzy yourself, for example with `git pull` (run from your local `'ozzy'` folder). 
    
    You don't have to install the new version with `pip`, since the `-e` flag makes it monitor the local directory for changes.