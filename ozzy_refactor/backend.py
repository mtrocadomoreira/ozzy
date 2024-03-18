import os
import glob
import re
import collections


class Backend:
    def __init__(self, file_type, as_series=True, axes_lims=None, *args, **kwargs):
        self.name = file_type
        self.as_series = as_series
        self.axes_lims = axes_lims

        match file_type:
            case "osiris":
                from . import osiris_backend as backend_mod
            case "lcode":
                from . import lcode_backend as backend_mod
            case "ozzy":
                pass
                # ds = read_ozzy(filepaths, as_series)
            case _:
                raise ValueError(
                    'Invalid input for "file_type" keyword. Available options are "osiris", "lcode", or "ozzy".'
                )

        self.parse = backend_mod.read

        self._quant_files = None
        self._regex_pattern = backend_mod.general_regex_pattern
        self._file_endings = backend_mod.general_file_endings
        self._quants_ignore = backend_mod.quants_ignore

    # TODO: define function to set attributes of standard quantities like t, x1, etc, only if missing

    def find_quants(self, path, dirs_runs, quants):
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
            label = m.group(1).strip("_-")
            if f not in quants_dict[label]:
                quants_dict[label].append(f)

        # Drop quantities that should be ignored
        if self._quants_ignore is not None:
            for q in self._quants_ignore:
                del quants_dict[q]

        return quants_dict

    def _load_quant_files(self, *args, **kwargs):
        self._quant_files = self.find_quants(*args, **kwargs)
        return self._quant_files

    def parse_data(self, files, *args, **kwargs):
        print("\nReading the following files:")
        ods = self.parse(files, self.as_series, *args, **kwargs)

        # Set metadata
        ods = ods.assign_attrs(
            {
                "file_backend": self.name,
                "source": os.path.commonpath(files),
                "file_prefix": os.path.commonprefix(
                    [os.path.basename(f) for f in files]
                ),
            }
        )

        return ods
