# *********************************************************
# Copyright (C) 2024 Mariana Moreira - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT License.

# You should have received a copy of the MIT License with
# this file. If not, please write to:
# mtrocadomoreira@gmail.com
# *********************************************************

import collections
import os
import re

import xarray as xr  # noqa

from .new_dataobj import new_dataset
from .utils import recursive_search_for_file


def _list_avail_backends():
    return ["osiris", "lcode", "ozzy"]


# -----------------------------------------------------------------------
# Backend class
# -----------------------------------------------------------------------

# TODO: make longitudinal consistent for all different backends (x1, xi, zeta, etc)
# TODO: make sure that unit labels are also consistent across different backends
# HACK: maybe have option to have configuration file to read files (to include info about geometry, axis limits, etc.)


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

    def __init__(self, file_type, *args, **kwargs):
        self.name = file_type

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

    def find_quants(
        self,
        path: str,
        dirs_runs: dict[str, str],
        quants: str | list[str] | None = None,
    ) -> dict[str, list[str]]:
        """
        Searches `path` for files matching `quants` in the run directories specified by `dirs_runs`. All arguments may contain [glob](https://en.wikipedia.org/wiki/Glob_(programming)) patterns.

        Parameters
        ----------
        path : str
            The base path to search for files.
        dirs_runs : dict[str, str]
            A dictionary mapping run names to directory paths relative to `path`.

            !!! tip

                The `dirs_runs` parameter can be obtained by running [`ozzy.find_runs(path, runs_pattern)`][ozzy.utils.find_runs]. For example:

                ```python
                import ozzy as oz
                dirs_runs = oz.find_runs(path='sim_dir', runs_pattern='param_scan_*')
                ```
        quants : str, or list[str], optional
            A quantity name or list of quantity names to search for. The search term may contain the full filename (`'e1-000001.h5'`), only the quantity name (`'e1'`) or any combination with a [glob](https://en.wikipedia.org/wiki/Glob_(programming)) pattern (`'e1-*'`, `'e1-*.h5'`).
            If not provided, any files with the file endings associated with this `Backend` are searched for.




        Returns
        -------
        dict[str, list[str]]
            A dictionary mapping quantity names to lists of matching file names.

        Examples
        --------
        ???+ example "Search for files with a specific quantity"
            ```python
            import ozzy.backend_interface as obi
            backend = obi.Backend('lcode')
            dirs_runs = {'run1': 'path/to/run1', 'run2': 'path/to/run2'}
            quants_dict = backend.find_quants('/base/path', dirs_runs, 'xi_Ez')
            # quants_dict = {'xi_Ez': ['xi_Ez_0001.swp', 'xi_Ez_0002.swp', ...]}
            ```

        ???+ example "Search for files with any quantity"
            ```python
            import ozzy.backend_interface as obi
            backend = obi.Backend('lcode')
            dirs_runs = {'run1': 'path/to/run1', 'run2': 'path/to/run2'}
            quants_dict = backend.find_quants('/base/path', dirs_runs)
            # quants_dict = {'xi_Ez': [...], 'xi_Er': [...], ...}
            ```
        """

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
                    term.append(q + "*." + fend)
            else:
                term = [q]
            searchterms = searchterms + term

        # Search files matching mattern
        filenames = []
        for run, run_dir in dirs_runs.items():
            searchdir = run_dir
            for term in searchterms:
                query = recursive_search_for_file(term, searchdir)
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

    def _load_quant_files(self, *args, **kwargs):
        self._quant_files = self.find_quants(*args, **kwargs)
        return self._quant_files

    def parse_data(self, files: list[str], *args, **kwargs) -> xr.Dataset:
        """Read data from files and attach metadata according to the selected [`Backend`][ozzy.backend_interface.Backend].

        Parameters
        ----------
        files : list[str]
            File paths to read data from.
        *args
            Positional arguments to be passed to the `read` function of the backend specification.
        **kwargs
            Keyword arguments to be passed to the `read` function of the backend specification.

            See available keyword arguments for each backend:

            * [LCODE][ozzy.backends.lcode_backend.read]
            * [OSIRIS][ozzy.backends.osiris_backend.read]
            * [ozzy][ozzy.backends.ozzy_backend.read]

        Returns
        -------
        xarray.Dataset
            Parsed data. Includes the following Dataset attributes: `'file_backend'`, `'source'`, `'file_prefix'`, `'pic_data_type'` and `'data_origin'`.

        Examples
        --------

        ???+ example "Parse a single file"

            ```python
            from ozzy.backend_interface import Backend

            backend = Backend('lcode')
            ds = backend.parse_data(['path/to/file.swp'])
            ```

        ???+ example "Parse multiple files"

            ```python
            from ozzy.backend_interface import Backend

            backend = Backend('osiris')
            ds = backend.parse_data(['path/to/file1.h5', 'path/to/file2.h5'])
            ```

        """

        if len(files) > 0:
            print("\nReading the following files:")
            files.sort()
            ods = self.parse(files, *args, **kwargs)

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
        else:
            ods = new_dataset()

        return ods
