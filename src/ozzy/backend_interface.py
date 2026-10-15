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
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import xarray as xr

from .new_dataobj import new_dataset
from .utils import recursive_search_for_file


def _list_avail_backends():
    return ["osiris", "lcode", "ozzy", "openpmd"]


# -----------------------------------------------------------------------
# ReadJob class
# -----------------------------------------------------------------------


class ReadMode(str, Enum):
    """
    Specify how discovered files are grouped into read jobs.

    Attributes
    ----------
    SERIES : str
        Group an openPMD diagnostic and all requested records into one job.
        Its value is `"series"`.
    COMPARE : str
        Create a separate openPMD job for every diagnostic-record pair.
        Its value is `"compare"`.

    """

    SERIES = "series"
    COMPARE = "compare"


@dataclass(frozen=True)
class ReadJob:
    """
    Describe a group of files to be passed to a backend reader.

    Parameters
    ----------
    run : str
        Name of the run containing the files.
    label : str
        Label assigned to the discovered quantity, diagnostic, or
        diagnostic-record pair.
    files : tuple[str, ...]
        File paths belonging to the job.
    reader_kwargs : collections.abc.Mapping[str, typing.Any], optional
        Additional keyword arguments for the backend reader. The default is an
        empty mapping.

    Attributes
    ----------
    run : str
        Name of the run containing the files.
    label : str
        Label assigned to the job.
    files : tuple[str, ...]
        File paths belonging to the job.
    reader_kwargs : collections.abc.Mapping[str, typing.Any]
        Additional keyword arguments for the backend reader.
    """

    run: str
    label: str
    files: tuple[str, ...]
    reader_kwargs: Mapping[str, Any] = field(default_factory=dict)


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
        Mixin class that makes methods available to the data object depending on the file backend/data origin (`'openpmd'`, `'osiris'`, `'ozzy'`, `'lcode'`).
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
            case "openpmd":
                from .backends import openpmd_backend as backend_mod
            case _:
                raise ValueError(
                    'Invalid input for "file_type" keyword. Available options are "openpmd", "osiris", "lcode", or "ozzy".'
                )

        self.parse = backend_mod.read
        self.mixin = backend_mod.Methods

        self._quant_files = None
        self._regex_pattern = backend_mod.general_regex_pattern
        self._file_endings = backend_mod.general_file_endings
        self._quants_ignore = backend_mod.quants_ignore

    def plan_reads(
        self,
        path: str,
        dirs_runs: dict[str, str],
        quants: str | list[str] | None = None,
        records: str | list[str] | None = None,
        mode: ReadMode = ReadMode.SERIES,
        **kwargs,
    ) -> list[ReadJob]:
        """
        Plan backend reads for the supplied run directories.

        For openPMD data, jobs are grouped by diagnostic and, in `"compare"` mode, by record. For the other backends, one job is produced for every discovered run-quantity combination.

        Parameters
        ----------
        path : str
            Base path associated with the run directories. The directories in
            `dirs_runs` have already been resolved by the caller.
        dirs_runs : dict[str, str]
            Mapping from run names to resolved run-directory paths.
        quants : str, list[str], or None, optional
            Quantity or diagnostic search pattern, or a list of patterns. `None`
            searches for all endings supported by the selected backend.
        records : str, list[str], or None, optional
            openPMD records to associate with each diagnostic. This parameter is used
            only by the `"openpmd"` backend.
        mode : ReadMode, optional
            Read-grouping mode. Available values are `ReadMode.SERIES` and
            `ReadMode.COMPARE`. The default is `ReadMode.SERIES`.
        **kwargs
            Additional keyword arguments accepted by the planning interface.

        Returns
        -------
        list[ReadJob]
            Planned read jobs.
        """
        del path  # Run directories are already resolved by the caller.

        if self.name == "openpmd":
            return self._plan_openpmd_reads(
                dirs_runs=dirs_runs,
                quants=quants,
                records=records,
                mode=mode,
            )

        return self._plan_filename_reads(
            dirs_runs=dirs_runs,
            quants=quants,
        )

    def _plan_filename_reads(
        self,
        dirs_runs: dict[str, str],
        quants: str | list[str] | None,
    ) -> list[ReadJob]:
        pattern = re.compile(self._regex_pattern)
        search_terms = self._make_search_terms(quants)
        files_by_run: dict[str, dict[str, list[str]]] = {}
        labels = []

        for run, run_dir in dirs_runs.items():
            files_by_label: dict[str, list[str]] = collections.defaultdict(list)

            for term in search_terms:
                for relative_path in recursive_search_for_file(term, run_dir):
                    filename = os.path.basename(relative_path)
                    match = pattern.fullmatch(filename)
                    if match is None:
                        continue

                    label = (
                        match.group("name").strip("_-")
                        if match.group("name") != ""
                        else match.group("file_ending").strip("_-")
                    )
                    if self._quants_ignore is not None and label in self._quants_ignore:
                        continue

                    filepath = os.path.join(run_dir, relative_path)
                    if filepath not in files_by_label[label]:
                        files_by_label[label].append(filepath)
                    if label not in labels:
                        labels.append(label)

            files_by_run[run] = files_by_label

        return [
            ReadJob(
                run=run,
                label=label,
                files=tuple(files_by_run[run].get(label, [])),
            )
            for run in dirs_runs
            for label in labels
        ]

    def _plan_openpmd_reads(
        self,
        dirs_runs: dict[str, str],
        quants: str | list[str] | None,
        records: str | list[str] | None,
        mode: ReadMode,
    ) -> list[ReadJob]:
        search_terms = self._make_search_terms(quants, diagnostic_dirs=True)
        diagnostics_by_run: dict[str, dict[str, list[str]]] = {}

        for run, run_dir in dirs_runs.items():
            files_by_diagnostic: dict[str, list[str]] = collections.defaultdict(list)

            for term in search_terms:
                for relative_path in recursive_search_for_file(term, run_dir):
                    diagnostic = os.path.dirname(relative_path)
                    filepath = os.path.join(run_dir, relative_path)
                    if filepath not in files_by_diagnostic[diagnostic]:
                        files_by_diagnostic[diagnostic].append(filepath)

            diagnostics_by_run[run] = files_by_diagnostic

        if mode is ReadMode.SERIES:
            return [
                ReadJob(
                    run=run,
                    label=diagnostic,
                    files=tuple(files),
                    reader_kwargs={"records": records},
                )
                for run, diagnostics in diagnostics_by_run.items()
                for diagnostic, files in diagnostics.items()
            ]

        record_list = [records] if isinstance(records, str) else records
        if record_list is None:
            record_list = [None]

        return [
            ReadJob(
                run=run,
                label=f"{diagnostic}|{record}",
                files=tuple(files),
                reader_kwargs={"records": record},
            )
            for run, diagnostics in diagnostics_by_run.items()
            for diagnostic, files in diagnostics.items()
            for record in record_list
        ]

    def _make_search_terms(
        self,
        quants: str | list[str] | None,
        diagnostic_dirs: bool = False,
    ) -> list[str]:
        if quants is None:
            quants = [""]
        elif isinstance(quants, str):
            quants = [quants]

        search_terms = []
        for quant in quants:
            if "." in quant:
                search_terms.append(quant)
                continue

            prefix = f"{quant}/" if diagnostic_dirs else quant
            search_terms.extend(
                f"{prefix}*.{file_ending}" for file_ending in self._file_endings
            )

        return search_terms

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
            * [openPMD][ozzy.backends.openpmd_backend.read]
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
