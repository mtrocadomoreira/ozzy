# Virtual environment setup

There are several resources out there to guide you through virtual environments and package management with Python. These are our personal recommendations for you to start.

## with conda <small>(recommended)</small>

#### Step 1 - Follow online guide

Follow this great online guide for installing miniforge (a smaller version of conda) and creating virtual environments:

[Miniforge setup](https://kirenz.github.io/codelabs/codelabs/miniforge-setup/#0)

!!! tip

    After you've completed the tutorial, you may want to delete the `'sklearn-env'` environment you created as an example. You can check the list of environments with
    ```bash
    conda env list
    ```
    The asterisk shows you which environment is currently active. Make sure to deactivate the `'sklearn-env'` environment first (with `conda deactivate`), and then run
    ```bash
    conda env remove -n sklearn-env
    ```

#### Step 2 - Create a virtual environment for ozzy

In your terminal, create a new environment with
```bash
conda create -n ozzy-env
```

Make sure to activate this environment before you install or use ozzy:
```bash
conda activate ozzy-env
```


## with venv

#### Step 1 - Install Python

Make sure you have [Python](https://www.python.org/downloads/) installed on your system. Ozzy requires the version of Python to be 3.10 or higher.

#### Step 2 - Follow online guide

Follow the instructions in the guide for venv, which is a virtual environment tool built into Python:

[Create and use virtual environments](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#create-and-use-virtual-environments)

#### Step 3 - Create a virtual environment for ozzy

In your terminal, create a new environment with
```bash
python3 -m venv .ozzy-env
```

Make sure to activate this environment before you install or use ozzy:
```bash
source .ozzy-env/bin/activate
```
