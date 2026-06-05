# *********************************************************
# Copyright (C) 2026 Mariana Moreira - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT License.

# You should have received a copy of the MIT License with
# this file. If not, please write to:
# mtrocadomoreira@gmail.com
# *********************************************************

# TODO: poetry add pint -> may need to increase python version req. to 3.11


from importlib import resources

from pint import UnitRegistry

custom_units_file = resources.files("ozzy").joinpath("physunits/unit_defs.txt")

ureg = UnitRegistry()

# Get file path if required by external library
with resources.as_file(custom_units_file) as path:
    ureg.load_definitions(path)
