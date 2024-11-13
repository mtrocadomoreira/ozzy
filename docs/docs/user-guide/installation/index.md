
# Installation

Ozzy is a Python package. We recommend installing ozzy in its own virtual environment, since it depends on several other packages. If you're not familiar with Python or virtual environments, see our [guide to setting up a virtual environment](virtual-environments.md).

<!-- Ozzy is available both on [PyPI](https://pypi.org/) (via `pip`) and on [conda-forge](https://conda-forge.org/) (via `conda` or `mamba`). -->

## Requirements

- Python >= 3.10

## with conda <small>(recommended)</small>

!!! note "Note about mamba"

    Feel free to replace the `conda` command with `mamba`. [Mamba](https://mamba.readthedocs.io/en/latest/index.html) is a faster version of the conda package manager, and is installed by default with [miniforge](https://github.com/conda-forge/miniforge).


After you have activated a new virtual environment, run:

```bash
conda install --channel=conda-forge ozzy-pic
```

## with pip

After you have activated a new virtual environment, run:

```bash
python3 -m pip install ozzy-pic
```


## with git + Poetry

This installation method can be used as a fallback, or in case the user wants to have access to the latest commit.

#### Step 1 - Requirements

Make sure that [git](https://git-scm.com/) is installed on your system and that you have a [virtual environment manager](virtual-environments.md) for your Python projects. In these instructions we will use `mamba` as the environment manager.

#### Step 2 - Clone the ozzy repository

Navigate to a directory of your choosing where you feel comfortable installing additional software, and clone the ozzy repository from GitHub:
```bash
# for example:
cd ~/opt
```
```bash
git clone https://github.com/mtrocadomoreira/ozzy.git
```

#### Step 3 - Create a new environment

Here we use `mamba` to create a virtual environment called `ozzy-git` and then activate it:
```bash
mamba create -n ozzy-git
```
```bash
mamba activate ozzy-git
```

#### Step 4 - Install ozzy with Poetry

We will use [Poetry](https://python-poetry.org/) to install ozzy and its dependencies. Making sure that the virtual environment you created in [Step 3](#step-3-create-a-new-environment) is activated, install Poetry:
```bash
mamba install poetry
```
Enter the directory where ozzy was cloned to (e.g. `cd ozzy`). It should contain a `README.md` file and some folders called `src`, `docs`, `tests`, etc. In this directory, run:
```bash
poetry install
```

After this step, ozzy should be installed successfully. You can check this by opening a Python shell in your terminal and importing ozzy.

```bash
python3
>>> import ozzy
```

If there is no error message, ozzy is installed correctly.

!!! note

    Please remember that the virtual environment you created must be activated whenever you want to use ozzy. 
    
    If you use Jupyter Notebooks or other interactive text editors such as Visual Studio Code, you have to instruct the application to use the kernel from your virtual environment. Virtual environments are often found and managed automatically by this kind of applications, but some setting up may be required.


!!! info "Updating ozzy"

    Whenever you want to update your ozzy installation to the latest version, run the following commands from inside the ozzy source code folder (e.g. `~/opt/ozzy`) and after activating your ozzy environment:

    ```bash
    git pull
    ```
    ```bash
    poetry update
    ```
