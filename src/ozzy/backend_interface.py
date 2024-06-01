# *********************************************************
# Copyright (C) 2024 Mariana Moreira - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT License.

# You should have received a copy of the MIT License with
# this file. If not, please write to:
# mtrocadomoreira@gmail.com
# *********************************************************

import collections
import glob
import os
import re

# TODO: write docstrings


def _list_avail_backends():
    return ["osiris", "lcode", "ozzy"]


# -----------------------------------------------------------------------
# Backend class
# -----------------------------------------------------------------------


class Backend:
    """Interface class for reading simulation data. Upon initialization, the Backend instance imports a specific submodule for a given data format and defines its data-parsing methods accordingly.

    Attributes
    ----------
    name : str
        Name of the backend (e.g. `'osiris'`).
    parse : function
        Function for parsing data from files.
    mixin : class
        Mixin class that makes methods available to the data object depending on the file backend/data origin (`'osiris'`, `'ozzy'`, `'lcode'`).

    Methods
    -------
    find_quants(path, dirs_runs, quants=None)
        Find matching files for quantities.
    _load_quant_files(*args, **kwargs)
        Load quantity files (calls `find_quants()`).
    parse_data(files, *args, **kwargs)
        Read data from files and attach metadata.

    Examples
    --------

    ??? example "Create a new Backend instance and read files"

        ```python
        backend = Backend('osiris')
        files = backend.find_quants(path='sim_dir', dirs_runs={'run1': 'run1_dir'}, quants=['e2', 'b3'])
        data = backend.parse_data(files)
        ```

    """

    def __init__(self, file_type, *args, **kwargs):  # axes_lims=None
        self.name = file_type
        # self.axes_lims = axes_lims

        match file_type:
            case "osiris":
                from .backends import osiris_backend as backend_mod
            case "lcode":
                from .backends import lcode_backend as backend_mod
            case "ozzy":
                from .backends import ozzy_backend as backend_mod
            case _:
                raise ValueError(
                    'Invalid input for "file_type" keyword. Available options are "osiris", "lcode", or "ozzy".'
                )

        self.parse = backend_mod.read
        self.mixin = backend_mod.Methods

        self._quant_files = None
        self._regex_pattern = backend_mod.general_regex_pattern
        self._file_endings = backend_mod.general_file_endings
        self._quants_ignore = backend_mod.quants_ignore

    def find_quants(self, path, dirs_runs, quants):
        """Find files matching quantities in simulation output.

        Searches `path` for files matching `quants` in the run directories specified by `dirs_runs`.

        Parameters
        ----------
        path : str
            Base path to search in.
        dirs_runs : dict
            Mapping of run names to their directories (see info below).

        quants : list of str, optional
            Quantities to search for. Looks for all quantities (`'*'`) if not given.

        Tip
        ----

        The `dirs_runs` parameter can be obtained by running [`ozzy.find_runs(path, runs_pattern)`][ozzy.utils.find_runs]. For example:

        ```python
        path_sim = 'sim_dir'
        rundirs = ozzy.find_runs(path=path_sim, runs_pattern='param_scan_*')
        quant_files = ozzy.find_quants(path=path_sim, dirs_runs=rundirs, quants='ez')
        ```

        Returns
        -------
        dict
            Mapping of found quantities to lists of matching files.

        Examples
        --------

        ???+ example "Find quantity files in a directory"

            ```python
            dirs_runs = {'run1': 'output'}
            files = backend.find_quants('sim_dir', dirs_runs, ['e_field'])
            print(files)
            # {'e_field': ['e_field_0000.h5', 'e_field_0001.h5']}
            ```

        """
        # TODO: check whether this is really the output in the above example - maybe returns full file paths

        if quants is None:
            quants = [""]
        if isinstance(quants, str):
            quants = [quants]

        # Define search strings for glob
        searchterms = []
        for q in quants:
            if "." not in q:
                term = []
                for fend in self._file_endings:
                    term.append("**/" + q + "*." + fend)
            else:
                term = ["**/" + q]
            searchterms = searchterms + term

        # Search files matching mattern
        filenames = []
        for run, run_dir in dirs_runs.items():
            searchdir = os.path.join(path, run_dir)
            for term in searchterms:
                query = sorted(glob.glob(term, recursive=True, root_dir=searchdir))
                filenames = filenames + [os.path.basename(f) for f in query]

        # Look for clusters of files matching pattern
        pattern = re.compile(self._regex_pattern)
        matches = (
            (pattern.fullmatch(f), f)
            for f in filenames
            if pattern.fullmatch(f) is not None
        )

        # Build output dictionary
        quants_dict = collections.defaultdict(list)
        for m, f in matches:
            label = (
                m.group(1).strip("_-") if m.group(1) != "" else m.group(3).strip("_-")
            )
            if f not in quants_dict[label]:
                quants_dict[label].append(f)

        # Drop quantities that should be ignored
        if self._quants_ignore is not None:
            for q in self._quants_ignore:
                if q in quants_dict:
                    del quants_dict[q]

        return quants_dict

    # TODO: make this function show up in documentation
    def _load_quant_files(self, *args, **kwargs):
        """Load quantity files by calling `find_quants() and storing them in the `_quant_files` attribute.

        Examples
        --------

        ??? example "Find quantity files in a directory"

            ```python
            >>> dirs_runs = {'run1': 'output'}
            >>> backend._load_quant_files('sim_dir', dirs_runs, ['e_field'])
            >>> print(backend._quant_files)
            {'e_field': ['e_field_0000.h5', 'e_field_0001.h5']}
            ```

        """
        # TODO: check whether this is really the output in the above example - maybe returns full file paths
        self._quant_files = self.find_quants(*args, **kwargs)
        return self._quant_files

    def parse_data(self, files, *args, **kwargs) -> xr.Dataset:
        """Read data from files and attach metadata.

        Parameters
        ----------
        files : list[str]
            File paths to read data from.

        Returns
        -------
        xarray.Dataset
            Parsed data. Includes the following Dataset attributes: `'file_backend'`, `'source'`, `'file_prefix'`, `'pic_data_type'` and `'data_origin'`.

        Examples
        --------
        >>> files = ['file1.h5', 'file2.h5']
        >>> data = backend.parse_data(files)
        >>> print(data.attrs)
        ...

        """
        # TODO: improve the example above
        print("\nReading the following files:")
        ods = self.parse(files, *args, **kwargs)

        if len(files) > 0:
            # Set metadata
            ods = ods.assign_attrs(
                {
                    "file_backend": self.name,
                    "source": os.path.commonpath(files),
                    "file_prefix": os.path.commonprefix(
                        [os.path.basename(f) for f in files]
                    ),
                    "data_origin": self.name,
                }
            )

        return ods
